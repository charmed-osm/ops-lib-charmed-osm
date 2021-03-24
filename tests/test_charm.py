#!/usr/bin/env python3

import base64
import sys
from typing import NoReturn
import unittest

import mock
from opslib.osm.charm import CharmedOsmBase
from ops.model import ActiveStatus, WaitingStatus
from ops.testing import Harness


class TestCharm(unittest.TestCase):
    """Prometheus Charm unit tests."""

    def setUp(self) -> NoReturn:
        """Test setup"""
        self.image_info = sys.modules["oci_image"].OCIImageResource().fetch()
        self.harness = Harness(CharmedOsmBase)
        self.harness.set_leader(is_leader=True)
        self.harness.begin()

    def test_config_changed_non_leader(
        self,
    ) -> NoReturn:
        self.harness.set_leader(is_leader=False)
        self.harness.charm.on.config_changed.emit()
        self.assertIsInstance(self.harness.charm.unit.status, ActiveStatus)

    @mock.patch("opslib.osm.charm.CharmedOsmBase.build_pod_spec")
    def test_config_changed_leader(self, mock_build_pod_spec) -> NoReturn:
        mock_build_pod_spec.return_value = {
            "version": 3,
            "containers": [{"name": "c1"}, {"name": "c2"}],
        }
        self.harness.charm.on.config_changed.emit()
        self.assertIsInstance(self.harness.charm.unit.status, ActiveStatus)


if __name__ == "__main__":
    unittest.main()
