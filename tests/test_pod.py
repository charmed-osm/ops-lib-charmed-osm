import unittest

from opslib.osm.pod import (
    IngressResourceV3Builder,
    FilesV3Builder,
    ContainerV3Builder,
    PodRestartPolicy,
    PodSpecV3Builder,
)

from typing import Optional, List, Dict, Tuple, Set


class TestPodSpecBuilder(unittest.TestCase):
    def test_all_success(self):
        app_name = "prometheus"
        hostname = "hostname"
        port = 9090
        image_info = {
            "imagePath": "registrypath",
            "username": "username",
            "password": "password",
        }
        files_builder = FilesV3Builder()
        files_builder.add_file(
            "prometheus.yml",
            ("global:\n"),
        )
        files = files_builder.build()
        command = ["/bin/prometheus"]

        container_builder = ContainerV3Builder(
            app_name, image_info, run_as_non_root=True
        )
        container_builder.add_port(name=app_name, port=port)
        container_builder.add_http_readiness_probe("/-/ready", port)
        container_builder.add_http_liveness_probe(
            "/-/healthy", port, failure_threshold=7
        )
        container_builder.add_command(command)
        container_builder.add_volume_config("config", "/etc/prometheus", files)
        container = container_builder.build()

        annotations = {"nginx.ingress.kubernetes.io/proxy-body-size": "15m"}

        ingress_resource_builder = IngressResourceV3Builder(
            f"{app_name}-ingress", annotations
        )

        ingress_resource_builder.add_tls([hostname], "tls_secret_name")
        ingress_resource_builder.add_rule(hostname, app_name, port)

        ingress_resource = ingress_resource_builder.build()
        pod_spec_builder = PodSpecV3Builder(enable_security_context=True)
        pod_spec_builder.add_container(container)
        pod_spec_builder.add_secret("secret-name", {"key": "value"})
        pod_spec_builder.add_ingress_resource(ingress_resource)
        restart_policy = PodRestartPolicy()
        restart_policy.add_secrets(secret_names=("secret-name"))
        policy_hash = restart_policy.policy_hash(
            {
                "kubernetesResources": {
                    "secrets": [
                        {
                            "name": "secret-name",
                            "type": "Opaque",
                            "stringData": {"key": "value"},
                        }
                    ],
                },
            }
        )
        pod_spec_builder.set_restart_policy(restart_policy)
        self.assertEqual(
            pod_spec_builder.build(),
            {
                "version": 3,
                "containers": [
                    {
                        "name": "prometheus",
                        "imageDetails": {
                            "imagePath": "registrypath",
                            "username": "username",
                            "password": "password",
                        },
                        "imagePullPolicy": "Always",
                        "ports": [
                            {
                                "name": "prometheus",
                                "containerPort": 9090,
                                "protocol": "TCP",
                            }
                        ],
                        "envConfig": {"policyHash": policy_hash},
                        "volumeConfig": [
                            {
                                "name": "config",
                                "mountPath": "/etc/prometheus",
                                "files": [
                                    {"path": "prometheus.yml", "content": "global:\n"}
                                ],
                            }
                        ],
                        "kubernetes": {
                            "securityContext": {
                                "runAsNonRoot": True,
                                "privileged": False,
                            },
                            "readinessProbe": {
                                "httpGet": {"path": "/-/ready", "port": 9090},
                                "initialDelaySeconds": 0,
                                "timeoutSeconds": 1,
                                "successThreshold": 1,
                                "failureThreshold": 3,
                                "periodSeconds": 10,
                            },
                            "livenessProbe": {
                                "httpGet": {"path": "/-/healthy", "port": 9090},
                                "initialDelaySeconds": 0,
                                "timeoutSeconds": 1,
                                "successThreshold": 1,
                                "failureThreshold": 7,
                                "periodSeconds": 10,
                            },
                        },
                        "command": ["/bin/prometheus"],
                    }
                ],
                "kubernetesResources": {
                    "pod": {
                        "securityContext": {
                            "runAsUser": 1000,
                            "runAsGroup": 1000,
                            "fsGroup": 1000,
                        },
                    },
                    "ingressResources": [
                        {
                            "name": "prometheus-ingress",
                            "annotations": {
                                "nginx.ingress.kubernetes.io/proxy-body-size": "15m"
                            },
                            "spec": {
                                "rules": [
                                    {
                                        "host": "hostname",
                                        "http": {
                                            "paths": [
                                                {
                                                    "path": "/",
                                                    "backend": {
                                                        "serviceName": "prometheus",
                                                        "servicePort": 9090,
                                                    },
                                                }
                                            ]
                                        },
                                    }
                                ],
                                "tls": [
                                    {
                                        "hosts": ["hostname"],
                                        "secretName": "tls_secret_name",
                                    },
                                ],
                            },
                        }
                    ],
                    "secrets": [
                        {
                            "name": "secret-name",
                            "type": "Opaque",
                            "stringData": {"key": "value"},
                        }
                    ],
                },
            },
        )


if __name__ == "__main__":
    unittest.main()
