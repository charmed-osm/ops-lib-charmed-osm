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


import ops.charm
import ops.framework
import ops.model

from .common import BaseRelationClient


class HttpServer(ops.framework.Object):
    """Provides side of a Http Endpoint"""

    relation_name: str = None

    def __init__(self, charm: ops.charm.CharmBase, relation_name: str):
        super().__init__(charm, relation_name)
        self.relation_name = relation_name

    def publish_info(
        self,
        host: str,
        port: int,
        path: str = None,
        basic_auth_username: str = None,
        basic_auth_password: str = None,
    ):
        if self.framework.model.unit.is_leader():
            for relation in self.framework.model.relations[self.relation_name]:
                relation_data = relation.data[self.framework.model.app]
                relation_data["host"] = str(host)
                relation_data["port"] = str(port)
                relation_data["path"] = str(path)
                relation_data["basic_auth_username"] = str(basic_auth_username)
                relation_data["basic_auth_password"] = str(basic_auth_password)


class HttpClient(BaseRelationClient):
    """Requires side of a Http Endpoint"""

    mandatory_fields = ["host", "port"]

    def __init__(self, charm: ops.charm.CharmBase, relation_name: str):
        super().__init__(charm, relation_name, self.mandatory_fields)

    @property
    def host(self):
        return self.get_data_from_app("host")

    @property
    def port(self):
        return self.get_data_from_app("port")

    @property
    def path(self):
        return self.get_data_from_app("path")

    @property
    def basic_auth_username(self):
        return self.get_data_from_app("basic_auth_username")

    @property
    def basic_auth_password(self):
        return self.get_data_from_app("basic_auth_password")
