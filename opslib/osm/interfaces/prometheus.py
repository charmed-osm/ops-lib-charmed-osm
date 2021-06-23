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
Prometheus endpoint implementation for the Operator Framework.
Ported to the Operator Framework from the canonical-osm Reactive
charms at https://git.launchpad.net/canonical-osm
"""

from typing import NoReturn

import ops.charm
import ops.framework
import ops.model

from .common import BaseRelationClient


class PrometheusServer(ops.framework.Object):
    """Provides side of a Prometheus Endpoint"""

    relation_name: str = None

    def __init__(self, charm: ops.charm.CharmBase, relation_name: str):
        super().__init__(charm, relation_name)
        self.relation_name = relation_name

    def publish_info(self, hostname: str, port: int = 9091):
        if self.framework.model.unit.is_leader():
            for relation in self.framework.model.relations[self.relation_name]:
                relation.data[self.framework.model.app]["hostname"] = hostname
                relation.data[self.framework.model.app]["port"] = str(port)


class PrometheusClient(BaseRelationClient):
    """Requires side of a Prometheus Endpoint"""

    mandatory_fields = ["hostname", "port"]

    def __init__(self, charm: ops.charm.CharmBase, relation_name: str):
        super().__init__(charm, relation_name, self.mandatory_fields)

    @property
    def hostname(self):
        return self.get_data_from_app("hostname")

    @property
    def port(self):
        return self.get_data_from_app("port")


class PrometheusScrapeTarget(ops.framework.Object):
    """Provides side of a Prometheus Scrape endpoint"""

    relation_name: str = None

    def __init__(self, charm: ops.charm.CharmBase, relation_name: str):
        super().__init__(charm, relation_name)
        self.relation_name = relation_name

    def publish_info(
        self,
        hostname: str,
        port: str,
        metrics_path: str,
        scrape_interval: str,
        scrape_timeout: str,
    ) -> NoReturn:
        if self.framework.model.unit.is_leader():
            for relation in self.framework.model.relations[self.relation_name]:
                relation.data[self.framework.model.app]["hostname"] = hostname
                relation.data[self.framework.model.app]["port"] = port
                relation.data[self.framework.model.app]["metrics_path"] = metrics_path
                relation.data[self.framework.model.app][
                    "scrape_interval"
                ] = scrape_interval
                relation.data[self.framework.model.app][
                    "scrape_timeout"
                ] = scrape_timeout


class PrometheusScrapeServer(BaseRelationClient):
    """Requires side of a Prometheus Scrape Endpoint"""

    mandatory_fields = [
        "hostname",
        "port",
        "metrics_path",
        "scrape_interval",
        "scrape_timeout",
    ]

    def __init__(self, charm: ops.charm.CharmBase, relation_name: str):
        super().__init__(charm, relation_name, self.mandatory_fields)

    @property
    def hostname(self):
        return self.get_data_from_app("hostname")

    @property
    def port(self):
        return self.get_data_from_app("port")

    @property
    def metrics_path(self):
        return self.get_data_from_app("metrics_path")

    @property
    def scrape_interval(self):
        return self.get_data_from_app("scrape_interval")

    @property
    def scrape_timeout(self):
        return self.get_data_from_app("scrape_timeout")
