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

    @property
    def database(self):
        return self.get_data_from_unit("database")

    def get_root_uri(self, database: str):
        """
        Get the URI for the mysql connection with the root user credentials

        :param: database: Database name

        :return: A string with the following format:
                    mysql://root:<root_password>@<mysql_host>:<mysql_port>/<database>
        """
        return "mysql://root:{}@{}:{}/{}".format(
            self.root_password,
            self.host,
            self.port,
            database
        )

    def get_uri(self):
        """
        Get the URI for the mysql connection with the standard user credentials

        :param: database: Database name

        :return: A string with the following format:
                    mysql://<user>:<password>@<mysql_host>:<mysql_port>/<database>
        """
        return "mysql://{}:{}@{}:{}/{}".format(
            self.user,
            self.password,
            self.host,
            self.port,
            self.database
        )
