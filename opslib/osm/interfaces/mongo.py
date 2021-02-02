import ops.charm

from .common import BaseRelationClient


class MongoClient(BaseRelationClient):
    """Requires side of a Mongo Endpoint"""

    mandatory_fields = ["connection_string"]

    def __init__(self, charm: ops.charm.CharmBase, relation_name: str):
        super().__init__(charm, relation_name, self.mandatory_fields)

    @property
    def connection_string(self):
        return self.get_data_from_unit("connection_string")
