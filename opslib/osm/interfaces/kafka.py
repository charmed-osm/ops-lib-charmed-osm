import ops.charm

from .common import BaseRelationClient


class KafkaServer(ops.framework.Object):
    """Provides side of a Kafka Endpoint"""

    relation_name: str = None

    def __init__(self, charm: ops.charm.CharmBase, relation_name: str):
        super().__init__(charm, relation_name)
        self.relation_name = relation_name

    def publish_info(self, host: str, port: int):
        if self.framework.model.unit.is_leader():
            for relation in self.framework.model.relations[self.relation_name]:
                relation_data = relation.data[self.framework.model.app]
                relation_data["host"] = str(host)
                relation_data["port"] = str(port)


class KafkaClient(BaseRelationClient):
    """Requires side of a Kafka Endpoint"""

    mandatory_fields = ["host", "port"]

    def __init__(self, charm: ops.charm.CharmBase, relation_name: str):
        super().__init__(charm, relation_name, self.mandatory_fields)

    @property
    def host(self) -> int:
        """Returns Kafka host from relation data"""
        return self.get_data_from_app("host") or self.get_data_from_unit("host")

    @property
    def port(self) -> int:
        """Returns Kafka port from relation data"""
        port = self.get_data_from_app("port") or self.get_data_from_unit("port")
        if port:
            return int(port)


class KafkaCluster(BaseRelationClient):
    """Peer relation for a Kafka cluster"""

    def __init__(self, charm: ops.charm.CharmBase, relation_name: str):
        super().__init__(charm, relation_name)

    @property
    def num_units(self) -> int:
        """Return number of units in the cluster"""
        # The `units` property in Relation only includes other units, not the current
        # For that reason, 1 unit is added, to include the current one.
        if not self.relation:
            self._update_relation()
        return len(self.relation.units) + 1
