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

"""
Grafana endpoint implementation for the Operator Framework.
Ported to the Operator Framework from the canonical-osm Reactive
charms at https://git.launchpad.net/canonical-osm
"""

from typing import NoReturn

import ops.charm
import ops.framework
import ops.model

from .common import BaseRelationClient


class GrafanaDashboardTarget(ops.framework.Object):
    """Provides side of a Grafana Dashboards endpoint"""

    relation_name: str = None

    def __init__(self, charm: ops.charm.CharmBase, relation_name: str):
        super().__init__(charm, relation_name)
        self.relation_name = relation_name

    def publish_info(
        self,
        name: str,
        dashboard: str,
    ) -> NoReturn:
        if self.framework.model.unit.is_leader():
            for relation in self.framework.model.relations[self.relation_name]:
                relation.data[self.framework.model.app]["name"] = name
                relation.data[self.framework.model.app]["dashboard"] = dashboard


class GrafanaDashboardServer(BaseRelationClient):
    """Requires side of a Grafana Dashboard Endpoint"""

    mandatory_fields = ["name", "dashboard"]

    def __init__(self, charm: ops.charm.CharmBase, relation_name: str):
        super().__init__(charm, relation_name, self.mandatory_fields)

    @property
    def name(self):
        return self.get_data_from_app("name")

    @property
    def dashboard(self):
        return self.get_data_from_app("dashboard")


class GrafanaCluster(BaseRelationClient):
    """Peer relation for a Grafana cluster"""

    def __init__(self, charm: ops.charm.CharmBase, relation_name: str):
        super().__init__(charm, relation_name)

    def set_initial_password(self, password: str):
        if self.framework.model.unit.is_leader():
            self.relation.data[self.framework.model.app][
                "admin_initial_password"
            ] = str(password)

    @property
    def admin_initial_password(self) -> int:
        """Return grafana admin password in the cluster"""
        return self.get_data_from_app("admin_initial_password")
