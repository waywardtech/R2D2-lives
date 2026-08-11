from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from r2_runtime.config import R2Config
from r2_runtime.drivers import HardwareUnavailableError, SimDroidDriver, Spherov2R2Driver
from r2_runtime.spatial import NullSpatialProviderClient, SimSpatialProviderClient, select_spatial_provider


class R2ScaffoldTest(unittest.TestCase):
    def test_default_is_simulation_and_null_provider(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            config = R2Config.from_env()
        self.assertEqual(config.droid_driver, "sim")
        self.assertIsInstance(select_spatial_provider(config.spatial_provider), NullSpatialProviderClient)

    def test_provider_is_selected_by_configuration(self) -> None:
        with patch.dict(os.environ, {"R2_SPATIAL_PROVIDER": "sim"}, clear=True):
            config = R2Config.from_env()
        self.assertIsInstance(select_spatial_provider(config.spatial_provider), SimSpatialProviderClient)

    def test_no_real_driver_can_be_selected(self) -> None:
        with patch.dict(os.environ, {"R2_DROID_DRIVER": "ble"}, clear=True):
            with self.assertRaisesRegex(ValueError, "only the simulation"):
                R2Config.from_env()

    def test_sim_driver_starts_and_ends_stopped(self) -> None:
        driver = SimDroidDriver()
        driver.safe_hold()
        self.assertTrue(driver.stopped)
        self.assertEqual(driver.history, ["safe_hold"])

    def test_hardware_adapter_is_fail_closed_in_phase_zero(self) -> None:
        driver = Spherov2R2Driver(configured_identity="configured-outside-source")
        with self.assertRaisesRegex(HardwareUnavailableError, "simulation/replay is mandatory"):
            driver.connect()
        self.assertTrue(driver.stopped)


if __name__ == "__main__":
    unittest.main()
