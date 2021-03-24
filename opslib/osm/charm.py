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
from typing import Any, Dict, NoReturn

from oci_image import OCIImageResource, OCIImageResourceError
from ops.charm import CharmBase
from ops.framework import StoredState
from ops.model import (
    ActiveStatus,
    BlockedStatus,
    MaintenanceStatus,
    ModelError,
    WaitingStatus,
)

from .validator import ValidationError

logger = logging.getLogger(__name__)


class RelationsMissing(Exception):
    def __init__(self, missing_relations: list):
        self.message = ""
        if missing_relations and isinstance(missing_relations, list):
            self.message += f'Waiting for {", ".join(missing_relations)} relation'
            if "," in self.message:
                self.message += "s"


class CharmedOsmBase(CharmBase):
    """CharmedOsmBase Charm."""

    state = StoredState()

    def __init__(self, *args, oci_image="image") -> NoReturn:
        """CharmedOsmBase Charm constructor."""
        super().__init__(*args)

        # Internal state initialization
        self.state.set_default(pod_spec=None)

        self.image = OCIImageResource(self, oci_image)

        # Registering regular events
        self.framework.observe(self.on.config_changed, self.configure_pod)
        self.framework.observe(self.on.leader_elected, self.configure_pod)

    def build_pod_spec(self, image_info):
        raise NotImplementedError()

    def configure_pod(self, _=None) -> NoReturn:
        """Assemble the pod spec and apply it, if possible."""
        try:
            if self.unit.is_leader():
                self.unit.status = MaintenanceStatus("Assembling pod spec")
                image_info = self.image.fetch()
                pod_spec = self.build_pod_spec(image_info)
                self._set_pod_spec(pod_spec)

            self.unit.status = ActiveStatus("ready")
        except OCIImageResourceError:
            self.unit.status = BlockedStatus("Error fetching image information")
        except ValidationError as e:
            logger.exception(f"Config data validation error: {e}")
            self.unit.status = BlockedStatus(str(e))
        except RelationsMissing as e:
            logger.error(f"Relation missing error: {e.message}")
            self.unit.status = WaitingStatus(e.message)
        except ModelError as e:
            self.unit.status = BlockedStatus(str(e))
        except Exception as e:
            logger.error(f"Unknown exception: {e}")
            self.unit.status = BlockedStatus(e)

    def _set_pod_spec(self, pod_spec: Dict[str, Any]) -> NoReturn:
        pod_spec_hash = _hash_from_dict(pod_spec)
        if self.state.pod_spec != pod_spec_hash:
            self.model.pod.set_spec(pod_spec)
            self.state.pod_spec = pod_spec_hash


def _hash_from_dict(dict: Dict[str, Any]) -> str:
    dict_str = json.dumps(dict, sort_keys=True)
    result = hashlib.md5(dict_str.encode())
    return result.hexdigest()
