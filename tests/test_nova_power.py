import tempfile
import unittest
from pathlib import Path
from nova_nexus.power_monitor import EnergySession, sample_battery

class PowerTests(unittest.TestCase):
    def test_macro_full(self):
        with tempfile.TemporaryDirectory() as d:
            for key, value in {"status":"Full","current_now":"0","voltage_now":"12419000","charge_now":"4152000"}.items():
                (Path(d)/key).write_text(value)
            value = sample_battery(d)
            self.assertAlmostEqual(value["voltage_v"], 12.419)
            self.assertEqual(value["battery_power_w"], 0.0)
            self.assertAlmostEqual(value["estimated_energy_wh"], 51.563688)
            self.assertIsNone(value["ac_wall_w"])
            self.assertIsNone(value["cpu_package_w"])

    def test_energy_interval(self):
        tracker = EnergySession()
        sample = {"battery_power_direction":"discharging","battery_power_w":18}
        tracker.update(sample, timestamp=0)
        self.assertAlmostEqual(tracker.update(sample, timestamp=3600), 0)
        self.assertAlmostEqual(tracker.update(sample, timestamp=3601), 0)
        self.assertAlmostEqual(tracker.update(sample, timestamp=3661), 0.3)
        tracker.update({"battery_power_direction":"charging","battery_power_w":15},timestamp=3662)
        self.assertAlmostEqual(tracker.consumed_wh, 0.3)

if __name__ == "__main__":
    unittest.main()
