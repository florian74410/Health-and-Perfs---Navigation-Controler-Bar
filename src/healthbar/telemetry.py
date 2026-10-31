"""Read-only telemetry. Values are None when hardware or permissions do not expose them."""
import math
import subprocess
import time
from pathlib import Path
from .cpu_detail import cpu_identity, sample_cpu_cores, PackagePower
try:
    import psutil
except ImportError:
    psutil = None

def _number(v):
    try:
        n = float(v)
        return n if math.isfinite(n) else None
    except (TypeError, ValueError):
        return None

def cpu_temperature():
    if psutil is None or not hasattr(psutil, "sensors_temperatures"):
        return None
    try:
        groups = psutil.sensors_temperatures(fahrenheit=False)
        for key in ("coretemp", "k10temp", "zenpower", "cpu_thermal"):
            values=[_number(item.current) for item in groups.get(key, [])]
            values=[value for value in values if value is not None and -20 <= value <= 150]
            if values:return max(values)
    except (OSError, RuntimeError, ValueError):
        pass
    return None

def list_fans():
    if psutil is None or not hasattr(psutil, "sensors_fans"):
        return []
    results = []
    try:
        for chip, fans in psutil.sensors_fans().items():
            for n, fan in enumerate(fans):
                rpm = _number(fan.current)
                if rpm is not None and rpm >= 0:
                    results.append({"name": (fan.label or f"{chip} {n+1}")[:30],
                                    "rpm": round(rpm)})
    except (OSError, RuntimeError, ValueError):
        pass
    return results[:32]

def nvidia_gpu():
    fields = "temperature.gpu,utilization.gpu,clocks.gr,memory.used,memory.total,power.draw"
    try:
        result = subprocess.run(["nvidia-smi", "--query-gpu=" + fields,
                                 "--format=csv,noheader,nounits"],
                                capture_output=True, text=True, check=True, timeout=1.5)
        rows = result.stdout.splitlines()
        values = [_number(x.strip()) for x in rows[0].split(",")] if rows else []
        if len(values) == 6:
            keys = ("gpu_temperature_c", "gpu_percent", "gpu_clock_mhz",
                    "vram_used_mb", "vram_total_mb", "gpu_power_w")
            data = dict(zip(keys, values))
            for src, dst in (("vram_used_mb", "vram_used_gb"),
                             ("vram_total_mb", "vram_total_gb")):
                val = data.pop(src)
                data[dst] = val / 1024 if val is not None else None
            return data
    except (FileNotFoundError, OSError, subprocess.SubprocessError):
        pass
    return {}

class Telemetry:
    def __init__(self):
        self.last_at = time.monotonic()
        self.last_net = None
        self.last_disk = None
        self.package_power = PackagePower()
        self.cpu_model = cpu_identity()
        if psutil:
            psutil.cpu_percent(interval=None)

    def sample(self):
        keys = ("cpu_percent", "cpu_frequency_ghz", "cpu_frequency_max_ghz",
            "cpu_temperature_c", "cpu_power_w", "cpu_model", "cpu_physical_cores", "cpu_logical_cores", "gpu_temperature_c", "gpu_percent", "gpu_clock_mhz",
            "gpu_power_w", "vram_used_gb", "vram_total_gb",
            "ram_percent", "ram_used_gb", "ram_available_gb", "ram_total_gb",
            "disk_percent", "disk_used_gb", "disk_free_gb", "disk_total_gb",
            "disk_read_mbs", "disk_write_mbs", "disk_health_percent",
            "net_down_mbs", "net_up_mbs")
        data = dict.fromkeys(keys)
        data["fans"] = []
        data["cpu_cores"] = []
        if psutil is None:
            return data
        try:
            data["cpu_percent"] = _number(psutil.cpu_percent(interval=None))
            data["cpu_model"] = self.cpu_model
            data["cpu_physical_cores"] = psutil.cpu_count(logical=False)
            data["cpu_logical_cores"] = psutil.cpu_count(logical=True)
            data["cpu_cores"] = sample_cpu_cores(psutil)
            data["cpu_power_w"] = self.package_power.sample()
            freq = psutil.cpu_freq() if hasattr(psutil, 'cpu_freq') else None
            if freq:
                data["cpu_frequency_ghz"] = round(freq.current/1000, 2)
                data["cpu_frequency_max_ghz"] = round(freq.max/1000, 2) if freq.max else None
            data["cpu_temperature_c"] = cpu_temperature()
            data["fans"] = list_fans()
            mem = psutil.virtual_memory()
            data.update(ram_percent=mem.percent, ram_used_gb=mem.used/2**30,
                        ram_available_gb=mem.available/2**30, ram_total_gb=mem.total/2**30)
            try:
                disk = psutil.disk_usage(Path.home().anchor or "/")
                data.update(disk_percent=disk.percent, disk_used_gb=disk.used/2**30,
                            disk_free_gb=disk.free/2**30, disk_total_gb=disk.total/2**30)
            except OSError:
                pass
            now = time.monotonic()
            delta = max(0.001, now - self.last_at)
            net = psutil.net_io_counters()
            if self.last_net and net:
                data["net_down_mbs"] = max(0, (net.bytes_recv-self.last_net.bytes_recv)/delta/1e6)
                data["net_up_mbs"] = max(0, (net.bytes_sent-self.last_net.bytes_sent)/delta/1e6)
            self.last_net = net
            io = psutil.disk_io_counters()
            if self.last_disk and io:
                data["disk_read_mbs"] = max(0, (io.read_bytes-self.last_disk.read_bytes)/delta/1e6)
                data["disk_write_mbs"] = max(0, (io.write_bytes-self.last_disk.write_bytes)/delta/1e6)
            self.last_disk = io
            self.last_at = now
        except (OSError, RuntimeError, ValueError):
            pass
        data.update(nvidia_gpu())
        return data
