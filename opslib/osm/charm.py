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

__all__ = ["CharmedOsmBase", "RelationsMissing"]


import hashlib
import json
import logging
from string import Template
import traceback
from typing import Any, Dict, NoReturn


from oci_image import OCIImageResource, OCIImageResourceError
from ops.charm import CharmBase
from ops.framework import StoredState
from ops.model import (
    ActiveStatus,
    BlockedStatus,
    MaintenanceStatus,
    ModelError,
)


from .config.mysql import MysqlModel
from .validator import ValidationError

logger = logging.getLogger(__name__)

DEBUG_SCRIPT = """#!/bin/bash
PUBLIC_KEY_CONTENT="$pubkey"
DEBIAN_FRONTEND=noninteractive  apt update && apt install ssh -y
cat /etc/ssh/sshd_config |
    grep -E '^PermitRootLogin yes$$' || (
    echo PermitRootLogin yes |
    tee -a /etc/ssh/sshd_config
)
mkdir -p /root/.ssh/
echo $$PUBLIC_KEY_CONTENT | tee -a /root/.ssh/authorized_keys
service ssh stop
sleep 3
service ssh start
grep OSM /root/.bashrc || (
    env |
    grep OSM |
    sed -e 's/^/export /' |
    sed -e 's/$$/\\\"/' |
    sed -e 's/=/=\\\"/' |
    tee -a /root/.bashrc
)
cat << EOF > /root/debug.code-workspace
$vscode_workspace
EOF
sleep infinity"""


class RelationsMissing(Exception):
    def __init__(self, missing_relations: list):
        if not missing_relations or not isinstance(missing_relations, list):
            raise Exception("missing_relations should be a non-empty list")
        self.message = f'Need {", ".join(missing_relations)} relation'
        if "," in self.message:
            self.message += "s"


class CharmedOsmBase(CharmBase):
    """CharmedOsmBase Charm."""

    state = StoredState()

    def __init__(
        self,
        *args,
        oci_image="image",
        debug_mode_config_key=None,
        debug_pubkey_config_key=None,
        vscode_workspace: Dict = {},
        mysql_uri: bool = False,
    ) -> NoReturn:
        """
        CharmedOsmBase Charm constructor

        :params: oci_image: Resource name for main OCI image
        :params: debug_mode_config_key: Key in charm config for enabling debugging mode
        :params: debug_pubkey_config_key: Key in charm config for setting debugging public ssh key
        :params: vscode_workspace: VSCode workspace
        """
        super().__init__(*args)

        # Internal state initialization
        self.state.set_default(pod_spec=None)

        self.image = OCIImageResource(self, oci_image)
        self.debugging_supported = debug_mode_config_key and debug_pubkey_config_key
        self.debug_mode_config_key = debug_mode_config_key
        self.debug_pubkey_config_key = debug_pubkey_config_key
        self.vscode_workspace = vscode_workspace
        self.mysql_uri = mysql_uri

        # Registering regular events
        self.framework.observe(self.on.config_changed, self.configure_pod)
        self.framework.observe(self.on.leader_elected, self.configure_pod)

    def build_pod_spec(self, image_info: Dict, **kwargs):
        """
        Method to be implemented by the charm to build the pod spec

        :params: image_info: Image info details
        :params: kwargs:
                    mysql_config (opslib.osm.config.mysql.MysqlModel):
                        Mysql config object. Will be included if the charm has been initialized
                        with mysql_uri=True.
        """
        raise NotImplementedError("build_pod_spec is not implemented")

    def _debug(self, pod_spec: Dict) -> NoReturn:
        """
        Activate debugging mode in the charm

        :params: pod_spec: Pod Spec to be debugged. Note: The first container is
                           the one that will be debugged.
        """
        container = pod_spec["containers"][0]
        if "readinessProbe" in container["kubernetes"]:
            container["kubernetes"].pop("readinessProbe")
        if "livenessProbe" in container["kubernetes"]:
            container["kubernetes"].pop("livenessProbe")
        container["ports"].append(
            {
                "name": "ssh",
                "containerPort": 22,
                "protocol": "TCP",
            }
        )
        container["volumeConfig"].append(
            {
                "name": "scripts",
                "mountPath": "/osm-debug-scripts",
                "files": [
                    {
                        "path": "debug.sh",
                        "content": Template(DEBUG_SCRIPT).substitute(
                            pubkey=self.config[self.debug_pubkey_config_key],
                            vscode_workspace=json.dumps(
                                self.vscode_workspace,
                                sort_keys=True,
                                indent=4,
                                separators=(",", ": "),
                            ),
                        ),
                        "mode": 0o777,
                    }
                ],
            }
        )
        container["command"] = ["/osm-debug-scripts/debug.sh"]

    def _debug_if_needed(self, pod_spec):
        """
        Debug the pod_spec if needed

        :params: pod_spec: Pod Spec to be debugged.
        """
        if self.debugging_supported and self.config[self.debug_mode_config_key]:
            if self.debug_pubkey_config_key not in self.config:
                raise Exception("debug_pubkey config is not set")
            self._debug(pod_spec)

    def _get_build_pod_spec_kwargs(self):
        """Get kwargs for the build_pod_spec function"""
        kwargs = {}
        if self.mysql_uri:
            kwargs["mysql_config"] = MysqlModel(**self.config)
        return kwargs

    def configure_pod(self, _=None) -> NoReturn:
        """Assemble the pod spec and apply it, if possible."""
        try:
            if self.unit.is_leader():
                self.unit.status = MaintenanceStatus("Assembling pod spec")
                image_info = self.image.fetch()
                kwargs = self._get_build_pod_spec_kwargs()
                pod_spec = self.build_pod_spec(image_info, **kwargs)
                self._debug_if_needed(pod_spec)
                self._set_pod_spec(pod_spec)

            self.unit.status = ActiveStatus("ready")
        except OCIImageResourceError:
            self.unit.status = BlockedStatus("Error fetching image information")
        except ValidationError as e:
            logger.error(f"Config data validation error: {e}")
            logger.debug(traceback.format_exc())
            self.unit.status = BlockedStatus(str(e))
        except RelationsMissing as e:
            logger.error(f"Relation missing error: {e.message}")
            logger.debug(traceback.format_exc())
            self.unit.status = BlockedStatus(e.message)
        except ModelError as e:
            self.unit.status = BlockedStatus(str(e))
        except Exception as e:
            error_message = f"Unknown exception: {e}"
            logger.error(error_message)
            logger.debug(traceback.format_exc())
            self.unit.status = BlockedStatus(error_message)

    def _set_pod_spec(self, pod_spec: Dict[str, Any]) -> NoReturn:
        pod_spec_hash = _hash_from_dict(pod_spec)
        if self.state.pod_spec != pod_spec_hash:
            self.model.pod.set_spec(pod_spec)
            self.state.pod_spec = pod_spec_hash


def _hash_from_dict(dict: Dict[str, Any]) -> str:
    dict_str = json.dumps(dict, sort_keys=True)
    result = hashlib.md5(dict_str.encode())
    return result.hexdigest()
