import ops.charm

from .common import BaseRelationClient


class MysqlClient(BaseRelationClient):
    """Requires side of a Mysql Endpoint"""

    mandatory_fields = ["host", "port", "user", "password", "root_password"]

    def __init__(self, charm: ops.charm.CharmBase, relation_name: str):
        super().__init__(charm, relation_name, self.mandatory_fields)

    @property
    def host(self):
        return self.get_data_from_unit("host")

    @property
    def port(self):
        return self.get_data_from_unit("port")

    @property
    def user(self):
        return self.get_data_from_unit("user")

    @property
    def password(self):
        return self.get_data_from_unit("password")

    @property
    def root_password(self):
        return self.get_data_from_unit("root_password")
