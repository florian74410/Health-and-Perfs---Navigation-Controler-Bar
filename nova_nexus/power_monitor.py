"""NOVA battery power telemetry (read-only Linux sysfs).

Units: uV -> V, uA -> A, uW -> W, uAh -> Ah, uWh -> Wh.
Wh consumed over a sampling interval = trapezoid(W) * elapsed_seconds / 3600.
Battery power is NOT AC-wall draw or CPU package power.
"""
from __future__ import annotations
import time
from pathlib import Path

def _read(directory, name):
    try:
        return (Path(directory) / name).read_text().strip()
    except (OSError, ValueError):
        return None

def _micro(directory, name):
    raw = _read(directory, name)
    try:
        return max(0.0, float(raw) / 1_000_000) if raw is not None else None
    except ValueError:
        return None

def sample_battery(directory="/sys/class/power_supply/BAT0"):
    status = _read(directory, "status") or "Unknown"
    v = _micro(directory, "voltage_now")
    current = _micro(directory, "current_now")
    watts = _micro(directory, "power_now")
    if watts is None and v is not None and current is not None:
        watts = v * current
    energy = _micro(directory, "energy_now")
    full = _micro(directory, "energy_full")
    design = _micro(directory, "energy_full_design")
    capacity_ah = _micro(directory, "charge_now")
    full_ah = _micro(directory, "charge_full")
    design_ah = _micro(directory, "charge_full_design")
    # A charge (Ah) times live voltage (V) is an approximation of Wh, not
    # the actual battery energy counter. Keep these fields separate.
    estimate_wh = capacity_ah * v if energy is None and capacity_ah is not None and v is not None else None
    health = 100 * full / design if full is not None and design and design > 0 else (
        100 * full_ah / design_ah if full_ah is not None and design_ah and design_ah > 0 else None
    )
    return {
        "status": status,
        "voltage_v": v,
        "current_a": current,
        "battery_power_w": watts,
        "battery_power_direction": ("discharging" if status == "Discharging" else "charging" if status == "Charging" else "idle"),
        "energy_wh": energy,
        "estimated_energy_wh": estimate_wh,
        "full_wh": full,
        "design_wh": design,
        "health_pct": health,
        "charge_ah": capacity_ah,
        "cpu_package_w": None,
        "ac_wall_w": None,
    }

class EnergySession:
    """Track discharge energy; never integrate charge or unknown status."""
    def __init__(self):
        self.previous = None
        self.consumed_wh = 0.0

    def update(self, sample, timestamp=None):
        now = time.monotonic() if timestamp is None else float(timestamp)
        eligible = sample["battery_power_direction"] == "discharging" and sample["battery_power_w"] is not None
        if eligible and self.previous:
            prior_t, prior_w = self.previous
            delta = now - prior_t
            if 0 < delta <= 120:
                self.consumed_wh += (prior_w + sample["battery_power_w"]) / 2 * delta / 3600
        self.previous = (now, sample["battery_power_w"]) if eligible else None
        return self.consumed_wh
