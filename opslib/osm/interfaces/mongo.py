import ops.charm

from .common import BaseRelationClient


class MongoClient(BaseRelationClient):
    """Requires side of a Mongo Endpoint"""

    mandatory_fields_mapping = {
        "reactive": ["connection_string"],
        "ops": ["replica_set_uri", "replica_set_name"],
    }

    def __init__(self, charm: ops.charm.CharmBase, relation_name: str):
        super().__init__(charm, relation_name, mandatory_fields=[])

    @property
    def connection_string(self):
        if self.is_opts():
            replica_set_uri = self.get_data_from_unit("replica_set_uri")
            replica_set_name = self.get_data_from_unit("replica_set_name")
            return f"{replica_set_uri}?replicaSet={replica_set_name}"
        else:
            return self.get_data_from_unit("connection_string")

    def is_opts(self):
        return not self.is_missing_data_in_unit_ops()

    def is_missing_data_in_unit(self):
        return (
            self.is_missing_data_in_unit_ops()
            and self.is_missing_data_in_unit_reactive()
        )

    def is_missing_data_in_unit_ops(self):
        return not all(
            [
                self.get_data_from_unit(field)
                for field in self.mandatory_fields_mapping["ops"]
            ]
        )

    def is_missing_data_in_unit_reactive(self):
        return not all(
            [
                self.get_data_from_unit(field)
                for field in self.mandatory_fields_mapping["reactive"]
            ]
        )
