import ops.charm

from .common import BaseRelationClient


class KafkaClient(BaseRelationClient):
    """Requires side of a Kafka Endpoint"""

    mandatory_fields = ["host", "port"]

    def __init__(self, charm: ops.charm.CharmBase, relation_name: str):
        super().__init__(charm, relation_name, self.mandatory_fields)

    @property
    def host(self):
        return self.get_data_from_unit("host")

    @property
    def port(self):
        return self.get_data_from_unit("port")
