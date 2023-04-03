#!/usr/bin/env python3
# Copyright 2021 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# For those usages not covered by the Apache License, Version 2.0 please
# contact: legal@canonical.com
#
# To get in touch with the maintainers, please contact:
# osm-charmers@lists.launchpad.net
##

__all__ = [
    "IngressResourceV3Builder",
    "FilesV3Builder",
    "ContainerV3Builder",
    "PodSpecV3Builder",
]


from typing import Any, Dict, List, NoReturn, Set


from .utils import find_in_list_with_key, hash_from_dict


class IngressResourceV3Builder:
    def __init__(self, name, annotations):
        self.name = name
        self.annotations = annotations
        self._rules = []
        self._tls = []

    @property
    def rules(self):
        return self._rules

    @property
    def tls(self):
        return self._tls

    @property
    def ingress_resource(self):
        r = {
            "name": self.name,
            "annotations": self.annotations,
            "spec": {"rules": self.rules},
        }
        if self._tls:
            r["spec"]["tls"] = self.tls
        return r

    def add_rule(self, hostname: str, service_name, port, path: str = "/"):
        # This function only supports one path per rule for simplicity
        self._rules.append(
            {
                "host": hostname,
                "http": {
                    "paths": [
                        {
                            "path": path,
                            "backend": {
                                "serviceName": service_name,
                                "servicePort": port,
                            },
                        }
                    ]
                },
            }
        )

    def add_tls(self, hosts, secret_name):
        tls = {"hosts": hosts}
        if secret_name:
            tls["secretName"] = secret_name
        self._tls.append(tls)

    def build(self):
        return self.ingress_resource


class FilesV3Builder:
    def __init__(self):
        self._files = []

    @property
    def files(self):
        return self._files

    def add_file(self, path: str, content: str, mode: int = None, secret: bool = False):
        file_spec = {"path": path, "content" if not secret else "key": content}
        if mode:
            file_spec.update({"mode": mode})
        self._files.append(file_spec)

    def build(self):
        return self.files


class ContainerV3Builder:
    def __init__(
        self,
        name,
        image_info,
        image_pull_policy="Always",
        run_as_non_root: bool = False,
    ):
        """
        :param: name: Name of the container
        :param: image_info: OCI image information
        :param: image_pull_policy: Image pull policy
        :param: run_as_non_root: Boolean to indicate whether to run the container
                                 as root or not. If True, will run as non-root,
                                 if False, will run as root. Default=False.
        """
        self.name = name
        self.image_info = image_info
        self.image_pull_policy = image_pull_policy
        self._security_context = {
            "runAsNonRoot": run_as_non_root,
            "privileged": False,
        }
        self._readiness_probe = {}
        self._liveness_probe = {}
        self._volume_config = []
        self._ports = []
        self._envs = {}
        self._command = None

    @property
    def security_context(self):
        return self._security_context

    @property
    def readiness_probe(self):
        return self._readiness_probe

    @property
    def liveness_probe(self):
        return self._liveness_probe

    @property
    def ports(self):
        return self._ports

    @property
    def env_config(self):
        return self._envs

    @property
    def command(self):
        return self._command

    @property
    def volume_config(self):
        return self._volume_config

    def add_port(self, name, port, protocol="TCP"):
        self._ports.append({"name": name, "containerPort": port, "protocol": protocol})

    def add_volume_config(self, name, mount_path, files, secret_name: str = None):
        volume_config = {
            "name": name,
            "mountPath": mount_path,
        }
        if secret_name:
            volume_config["secret"] = {"name": secret_name, "files": files}
        else:
            volume_config["files"] = files
        self._volume_config.append(volume_config)

    def add_command(self, command):
        self._command = command

    def update_security_context(
        self, run_as_non_root: bool = True, privileged: bool = False
    ):
        self._security_context.update(
            {
                "runAsNonRoot": run_as_non_root,
                "privileged": privileged,
            }
        )

    def add_http_readiness_probe(
        self,
        path,
        port,
        initial_delay_seconds=0,
        timeout_seconds=1,
        period_seconds=10,
        success_threshold=1,
        failure_threshold=3,
        http_headers=[],
    ):
        self._readiness_probe = self._http_probe(
            path,
            port,
            initial_delay_seconds,
            timeout_seconds,
            period_seconds,
            success_threshold,
            failure_threshold,
            http_headers,
        )

    def add_http_liveness_probe(
        self,
        path,
        port,
        initial_delay_seconds=0,
        timeout_seconds=1,
        period_seconds=10,
        success_threshold=1,
        failure_threshold=3,
        http_headers=[],
    ):
        self._liveness_probe = self._http_probe(
            path,
            port,
            initial_delay_seconds,
            timeout_seconds,
            period_seconds,
            success_threshold,
            failure_threshold,
            http_headers,
        )

    def _http_probe(
        self,
        path,
        port,
        initial_delay_seconds=0,
        timeout_seconds=1,
        period_seconds=10,
        success_threshold=1,
        failure_threshold=3,
        http_headers=[],
    ):
        http_probe = {
            "httpGet": {
                "path": path,
                "port": port,
            },
            "initialDelaySeconds": initial_delay_seconds,
            "timeoutSeconds": timeout_seconds,
            "successThreshold": success_threshold,
            "failureThreshold": failure_threshold,
            "periodSeconds": period_seconds,
        }
        if http_headers:
            http_probe["httpGet"]["httpHeaders"] = []
            for name, value in http_headers:
                http_probe["httpGet"]["httpHeaders"].append(
                    {"name": name, "value": value}
                )
        return http_probe

    def add_tcpsocket_readiness_probe(
        self,
        port,
        initial_delay_seconds=0,
        timeout_seconds=1,
        period_seconds=10,
        success_threshold=1,
        failure_threshold=3,
    ):
        self._readiness_probe = self._tcpsocket_probe(
            port,
            initial_delay_seconds,
            timeout_seconds,
            period_seconds,
            success_threshold,
            failure_threshold,
        )

    def add_tcpsocket_liveness_probe(
        self,
        port,
        initial_delay_seconds=0,
        timeout_seconds=1,
        period_seconds=10,
        success_threshold=1,
        failure_threshold=3,
    ):
        self._liveness_probe = self._tcpsocket_probe(
            port,
            initial_delay_seconds,
            timeout_seconds,
            period_seconds,
            success_threshold,
            failure_threshold,
        )

    def _tcpsocket_probe(
        self,
        port,
        initial_delay_seconds=0,
        timeout_seconds=1,
        period_seconds=10,
        success_threshold=1,
        failure_threshold=3,
    ):
        return {
            "tcpSocket": {
                "port": port,
            },
            "initialDelaySeconds": initial_delay_seconds,
            "timeoutSeconds": timeout_seconds,
            "successThreshold": success_threshold,
            "failureThreshold": failure_threshold,
            "periodSeconds": period_seconds,
        }

    def add_env(self, key: str, value: str):
        self._envs[key] = value

    def add_envs(self, envs: dict):
        self._envs = {**self._envs, **envs}

    def add_secret_envs(self, secret_name: str, envs: dict):
        new_secret_envs = {
            k: {"secret": {"name": secret_name, "key": v}} for k, v in envs.items()
        }
        self._envs = {**self._envs, **new_secret_envs}

    def build(self):
        container = {
            "name": self.name,
            "imageDetails": self.image_info,
            "imagePullPolicy": self.image_pull_policy,
            "ports": self.ports,
            "envConfig": self.env_config,
            "volumeConfig": self.volume_config,
            "kubernetes": {
                "securityContext": self.security_context,
            },
        }
        if self.command:
            container["command"] = self.command
        if self.readiness_probe:
            container["kubernetes"]["readinessProbe"] = self.readiness_probe
        if self.liveness_probe:
            container["kubernetes"]["livenessProbe"] = self.liveness_probe
        return container


class PodRestartPolicy:
    """
    Class that expresses which fields of the pod spec should force a pod restart

    At the moment, only secrets can force restart the pod. More parts of the pod
    can be added to the PodRestartPolicy while we need them.
    """

    default_policy = {
        "kubernetesResources": {
            "secrets": False,
        },
    }

    def add_secrets(self, secret_names: Set[str] = None) -> NoReturn:
        """
        Add secrets to the restart policy

        :param: secret_names: Set of secrets that will cause a force restart of the pod.
                              The set should include the name of the secrets.
                              If no secret_names are specified, all the secret will force
                              the restart of the pod
        """
        self.default_policy["kubernetesResources"]["secrets"] = (
            secret_names if secret_names else True
        )

    def _find_resources_with_name(
        self, resources: Dict, resources_names: Set[str]
    ) -> List[Any]:
        resources_found = []
        for name in resources_names:
            resource = find_in_list_with_key(resources, key="name", value=name)
            if resource:
                resources_found.append(resource)
        return resources_found

    def policy_hash(self, pod_spec: Dict) -> str:
        """
        Return a hash of the Pod Spec taking into account the current policy.
        This means that for the hash, only the data included in the policy will be added

        :param: pod_spec: Pod spec
        """
        spec = pod_spec.copy()
        policy_spec = {"kubernetesResources": {}}

        for resource_type, resource_names in self.default_policy[
            "kubernetesResources"
        ].items():
            if resource_names is True:
                policy_spec["kubernetesResources"][resource_type] = spec[
                    "kubernetesResources"
                ][resource_type]
            elif resource_names is not False:
                resources_found = self._find_resources_with_name(
                    spec["kubernetesResources"][resource_type], resource_names
                )
                if resources_found:
                    policy_spec["kubernetesResources"][resource_type] = resources_found
        return hash_from_dict(policy_spec)


class PodSpecV3Builder:
    def __init__(self, enable_security_context: bool = False):
        """
        :param: enable_security_context: Enable security context if True, disable it if False
                                         If True, user/group/fsgroup id 1000 will be used and
                                         container won't run as root user.
        """
        self._init_containers = []
        self._containers = []
        self._ingress_resources = []
        self._security_context = (
            {
                "runAsUser": 1000,
                "runAsGroup": 1000,
                "fsGroup": 1000,
            }
            if enable_security_context
            else {}
        )
        self._secrets = []
        self._restart_policy = None

    @property
    def containers(self):
        return self._containers

    @property
    def init_containers(self):
        return self._init_containers

    @property
    def ingress_resources(self):
        return self._ingress_resources

    @property
    def security_context(self):
        return self._security_context

    @property
    def secrets(self):
        return self._secrets

    @property
    def pod_spec(self):
        return {
            "version": 3,
            # "initContainers": self.init_containers,
            "containers": self.containers,
            "kubernetesResources": {
                "ingressResources": self.ingress_resources,
                "pod": {"securityContext": self.security_context},
                "secrets": self.secrets,
            },
        }

    def add_init_container(self, container):
        self._init_containers.append(container)

    def add_container(self, container):
        self._containers.append(container)

    def add_ingress_resource(self, ingress_resource):
        self._ingress_resources.append(ingress_resource)

    def set_security_context_run_as_user(self, user_id: int):
        self._security_context.update({"runAsUser": user_id})

    def set_security_context_run_as_group(self, group_id: int):
        self._security_context.update({"runAsGroup": group_id})

    def set_security_context_fs_group(self, fs_group: int):
        self._security_context.update({"fsGroup": fs_group})

    def set_restart_policy(self, restart_policy: PodRestartPolicy):
        self._restart_policy = restart_policy

    def add_secret(
        self, name: str, content: Dict, base64_encoded: bool = False, type="Opaque"
    ):
        """
        Add a secret to the Pod

        :param: name: Name of the secret
        :param: content: Dictionary with the content of the secret
        :base64_encoded: a bool to indicate if the content for the secret is base64 ncoded or not.
                         If true, then "data" will be used in the secret, if false, "stringData"
                         will be used
        :param: data_type: Type of the
        :param: type: Type of secret
                      ref: https://kubernetes.io/docs/concepts/configuration/secret/#secret-types
        """
        self._secrets.append(
            {
                "name": name,
                "type": type,
                "data" if base64_encoded else "stringData": content,
            }
        )

    def build(self):
        pod_spec = self.pod_spec
        if self._restart_policy:
            policy_hash = self._restart_policy.policy_hash(pod_spec)
            for container in pod_spec["containers"]:
                container["envConfig"]["policyHash"] = policy_hash
        return self.pod_spec
