import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from healthbar.power_sensors import battery_snapshot, PowerSession


class BatteryTests(unittest.TestCase):
    def test_macro_full_battery_zero_current_is_real_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            battery=Path(tmp)/'BAT0';battery.mkdir()
            for name,value in {'status':'Full','voltage_now':'12419000','current_now':'0',
                               'charge_full':'5000000','charge_full_design':'6000000'}.items():
                (battery/name).write_text(value)
            sample=battery_snapshot(battery)
            self.assertEqual(sample['voltage_v'],12.419)
            self.assertEqual(sample['power_w'],0)
            self.assertAlmostEqual(sample['wear_percent'],100/6)
            self.assertIsNone(sample['energy_full_wh'])
            self.assertEqual(sample['power_kind'],'calculated')

    def test_energy_integration_breaks_on_missing_values_and_long_gaps(self):
        session=PowerSession()
        def record(w,status='discharging'):
            return [{'id':'BAT0','status':status,'power_w':w}]
        session.sample(record(10),0)
        sample=session.sample(record(20),10)
        self.assertAlmostEqual(sample['battery_session_wh'],15*10/3600)
        session.sample(record(None),20);session.sample(record(20),30)
        session.sample(record(20),300)
        session.sample(record(20,'charging'),310)
        self.assertAlmostEqual(session.energy_wh,15*10/3600)

    def test_unknown_does_not_become_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(battery_snapshot(Path(tmp))['power_w'])
        self.assertIsNone(PowerSession().sample([],0)['battery_average_w'])
