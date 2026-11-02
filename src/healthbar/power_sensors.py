"""Read-only electrical telemetry. Never infer wall draw from package or GPU watts.

System mains voltage / AC power requires external measurement hardware;
per-core CPU/GPU and VRAM voltage or watts are only populated if genuinely
available from hardware interfaces. Unknown != zero.
"""
from __future__ import annotations
import math
from pathlib import Path


def _read_number(path):
    try:
        value = float(path.read_text(encoding="utf-8").strip())
        return value if math.isfinite(value) else None
    except (OSError, ValueError, OverflowError):
        return None


def _read_label(path):
    try:
        return path.read_text(encoding="utf-8").strip()[:90]
    except (OSError, ValueError):
        return ""


def power_sensor_snapshot(hwmon_root=Path("/sys/class/hwmon"),
                          supply_root=Path("/sys/class/power_supply")):
    """Return explicit sources only; no total-PC wattage from adding components."""
    result = {
        "power_total_w": None, "power_mains_voltage_v": None,
        "cpu_package_voltage_v": None, "gpu_core_voltage_v": None,
        "gpu_core_power_w": None, "gpu_vram_power_w": None,
        "gpu_vram_voltage_v": None,
        "battery_discharge_w": None, "ram_voltage_rails": [],
    }
    try:
        chips = sorted(hwmon_root.iterdir())
    except OSError:
        chips = []
    for chip in chips[:80]:
        if not chip.is_dir():
            continue
        for path in sorted(chip.glob("in*_input"))[:48]:
            label = _read_label(path.with_name(path.name.replace("_input", "_label")))
            if not label:
                continue
            v = _read_number(path)
            if v is None or not 0 <= v <= 30000:
                continue
            volts = round(v / 1000, 4)  # Linux hwmon in*_input uses millivolts.
            normalized = label.lower().replace(" ", "")
            if any(token in normalized for token in ("dimm", "dram", "vddq", "vddmem", "vdimm")):
                if len(result["ram_voltage_rails"]) < 16:
                    result["ram_voltage_rails"].append({"name": label, "voltage_v": volts})
            elif any(token in normalized for token in ("vcore", "cpu_vcore", "vddcr_cpu")):
                # A shared rail is NOT an individual core measurement.
                if result["cpu_package_voltage_v"] is None:
                    result["cpu_package_voltage_v"] = volts
    try:
        supplies = sorted(supply_root.iterdir())
    except OSError:
        supplies = []
    result["batteries"] = [battery_snapshot(s) for s in supplies[:32]
                           if s.name.upper().startswith("BAT")]
    for battery in result["batteries"]:
        if battery["status"] == "discharging" and battery["power_w"] is not None:
            result["battery_discharge_w"] = battery["power_w"]
            break
    return result


def battery_snapshot(supply):
    """Linux power_supply values use micro-units. Keep charge and energy distinct."""
    def micro(name):
        value = _read_number(supply / name)
        return value / 1e6 if value is not None and value >= 0 else None
    voltage, current = micro("voltage_now"), micro("current_now")
    power = micro("power_now")
    source = "power_now" if power is not None else "unavailable"
    if power is None and voltage is not None and current is not None:
        power, source = voltage * current, "voltage_now × current_now"
    energy, full, design = (micro(n) for n in ("energy_now", "energy_full", "energy_full_design"))
    charge, charge_full, charge_design = (micro(n) for n in ("charge_now", "charge_full", "charge_full_design"))
    # Rated voltage is appropriate for estimating rated energy; never use the
    # instantaneous voltage to misrepresent a measured full/design capacity.
    nominal = micro("voltage_min_design")
    estimated_energy = False
    if nominal is not None:
        if energy is None and charge is not None:
            energy, estimated_energy = charge * nominal, True
        if full is None and charge_full is not None:
            full, estimated_energy = charge_full * nominal, True
        if design is None and charge_design is not None:
            design, estimated_energy = charge_design * nominal, True
    ratio = full / design if full is not None and design else (
        charge_full / charge_design if charge_full is not None and charge_design else None)
    remaining = _read_number(supply / "capacity")
    if remaining is None and energy is not None and full:
        remaining = 100 * energy / full
    if remaining is None and charge is not None and charge_full:
        remaining = 100 * charge / charge_full
    return {"id": supply.name, "status": _read_label(supply / "status").lower(),
            "voltage_v": voltage, "current_a": current, "power_w": power,
            "power_source": source, "power_kind": "calculated" if "×" in source else "measured" if power is not None else "unavailable",
            "charge_ah": charge, "charge_full_ah": charge_full,
            "energy_wh": energy, "energy_full_wh": full, "energy_design_wh": design,
            "energy_estimated": estimated_energy,
            "remaining_percent": max(0, min(100, remaining)) if remaining is not None else None,
            "wear_percent": max(0, min(100, 100 * (1-ratio))) if ratio is not None else None}


class PowerSession:
    """Integrate battery discharge only across consecutive, valid samples.

    Gaps over 30 s, unplugging, charging and missing sensors break integration.
    The session total is an estimate from sampled battery power, never wall energy.
    """
    def __init__(self):
        from collections import deque
        self.history = deque(maxlen=600)
        self.previous = None
        self.energy_wh = 0.0
        self.elapsed = 0.0
        self.minimum = self.maximum = None

    def sample(self, batteries, now):
        active = [b for b in batteries if b["status"] == "discharging"]
        valid = bool(active) and all(b["power_w"] is not None for b in active)
        watts = sum(b["power_w"] for b in active) if valid else None
        ids = tuple(b["id"] for b in active)
        if watts is not None:
            self.minimum = watts if self.minimum is None else min(self.minimum, watts)
            self.maximum = watts if self.maximum is None else max(self.maximum, watts)
            if self.previous and self.previous[2] == ids:
                delta = now - self.previous[0]
                if 0 < delta <= 30:
                    self.energy_wh += (self.previous[1] + watts) / 2 * delta / 3600
                    self.elapsed += delta
            self.previous = (now, watts, ids)
        else:
            self.previous = None
        self.history.append((now, watts))
        return {"battery_session_wh": self.energy_wh,
                "battery_average_w": self.energy_wh * 3600 / self.elapsed if self.elapsed else None,
                "battery_min_w": self.minimum, "battery_max_w": self.maximum,
                "battery_power_history": list(self.history)}
