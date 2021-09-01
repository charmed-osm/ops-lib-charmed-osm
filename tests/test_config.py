import unittest

from opslib.osm.config.mysql import MysqlModel
from opslib.osm.validator import ValidationError


class TestMysqlConfig(unittest.TestCase):
    def test_success_with_db(self):
        config = {"mysql_uri": "mysql://user:pass@host:1234/db"}
        model = MysqlModel(**config)
        self.assertEqual(model.username, "user")
        self.assertEqual(model.password, "pass")
        self.assertEqual(model.host, "host")
        self.assertEqual(model.port, 1234)
        self.assertEqual(model.database, "db")

    def test_success_without_db(self):
        complex_password = "jh$-$_KRpSWdR!*zC49+"
        config = {"mysql_uri": f"mysql://user:{complex_password}@host:1234/"}
        model = MysqlModel(**config)
        self.assertEqual(model.username, "user")
        self.assertEqual(model.password, complex_password)
        self.assertEqual(model.host, "host")
        self.assertEqual(model.port, 1234)
        self.assertEqual(model.database, None)

    def test_success_no_data(self):
        config = {}
        model = MysqlModel(**config)

    def test_invalid(self):
        invalid_uris = [
            "user:pass@host:1234/db",
            "mysql://user:pass@host:badport",
            "mysql://user@host:1234",
            "mysql://host:1234",
        ]

        for uri in invalid_uris:
            with self.assertRaises(ValidationError):
                config = {"mysql_uri": uri}
                MysqlModel(**config)
