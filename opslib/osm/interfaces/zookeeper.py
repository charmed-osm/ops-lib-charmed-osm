# This file is part of the ops-lib-mysql component for Juju Operator
# Framework Charms.
# Copyright 2021 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the Lesser GNU General Public License version 3,
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the Lesser GNU General Public License for more details.
#
# You should have received a copy of the Lesser GNU General Public
# License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.

import logging


import ops.charm
import ops.framework
import ops.model

from .common import BaseRelationClient


logger = logging.getLogger(__name__)


class ZookeeperServer(ops.framework.Object):
    """Provides side of a Zookeeper Endpoint"""

    relation_name: str = None

    def __init__(self, charm: ops.charm.CharmBase, relation_name: str):
        super().__init__(charm, relation_name)
        self.relation_name = relation_name

    def publish_info(self, zookeeper_uri):
        if self.framework.model.unit.is_leader():
            for relation in self.framework.model.relations[self.relation_name]:
                relation_data = relation.data[self.framework.model.app]
                relation_data["zookeeper_uri"] = str(zookeeper_uri)


class ZookeeperClient(BaseRelationClient):
    """Requires side of a Zookeeper Endpoint"""

    mandatory_fields = ["zookeeper_uri"]

    def __init__(self, charm: ops.charm.CharmBase, relation_name: str):
        super().__init__(charm, relation_name, self.mandatory_fields)

    @property
    def zookeeper_uri(self):
        return self.get_data_from_app("zookeeper_uri")


class ZookeeperCluster(BaseRelationClient):
    """Peer relation for a Zookeeper cluster"""

    def __init__(self, charm: ops.charm.CharmBase, relation_name: str, port: int):
        super().__init__(charm, relation_name)
        self.port = port
        self.framework.observe(
            charm.on["cluster"].relation_changed, self._update_zookeeper_uri
        )

    @property
    def zookeeper_uri(self):
        return self.get_data_from_app("zookeeper_uri")

    def _update_zookeeper_uri(self, event):
        if self.framework.model.unit.is_leader():
            zookeepers = []
            for i in range(self.num_units):
                zookeepers.append(
                    f"{self.app_name}-{i}.{self.k8s_service_name}:{self.port}"
                )
            zookeeper_uri = ",".join(zookeepers)
            relation_data = event.relation.data[self.framework.model.app]
            relation_data["zookeeper_uri"] = str(zookeeper_uri)

    @property
    def k8s_service_name(self):
        return f"{self.framework.model.app.name}-endpoints"

    @property
    def service_name(self):
        return f"{self.app_name}-endpoints"

    @property
    def app_name(self):
        return self.framework.model.app.name

    @property
    def num_units(self) -> int:
        """Return number of units in the cluster"""
        # The `units` property in Relation only includes other units, not the current
        # For that reason, 1 unit is added, to include the current one.
        if not self.relation:
            self._update_relation()
        return len(self.relation.units) + 1
