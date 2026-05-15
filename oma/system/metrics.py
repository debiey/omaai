"""
OmaAI System Metrics
Collects real-time system data via psutil.
Used by oma monitor.
"""

import psutil
import platform
import subprocess
from datetime import datetime


def get_cpu() -> dict:
    return {
        "percent":        psutil.cpu_percent(interval=1),
        "count_logical":  psutil.cpu_count(logical=True),
        "count_physical": psutil.cpu_count(logical=False),
        "freq_mhz":       round(psutil.cpu_freq().current) if psutil.cpu_freq() else None,
        "per_core":       psutil.cpu_percent(interval=0.5, percpu=True),
    }


def get_memory() -> dict:
    vm   = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "total_gb":      round(vm.total / 1e9, 1),
        "used_gb":       round(vm.used   / 1e9, 1),
        "available_gb":  round(vm.available / 1e9, 1),
        "percent":       vm.percent,
        "swap_total_gb": round(swap.total / 1e9, 1),
        "swap_used_gb":  round(swap.used  / 1e9, 1),
        "swap_percent":  swap.percent,
    }


def get_disk() -> list:
    partitions = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            partitions.append({
                "device":     part.device,
                "mountpoint": part.mountpoint,
                "fstype":     part.fstype,
                "total_gb":   round(usage.total / 1e9, 1),
                "used_gb":    round(usage.used   / 1e9, 1),
                "free_gb":    round(usage.free   / 1e9, 1),
                "percent":    usage.percent,
            })
        except PermissionError:
            continue
    return partitions


def get_network() -> dict:
    net = psutil.net_io_counters()
    return {
        "bytes_sent_mb": round(net.bytes_sent / 1e6, 1),
        "bytes_recv_mb": round(net.bytes_recv / 1e6, 1),
        "packets_sent":  net.packets_sent,
        "packets_recv":  net.packets_recv,
    }


def get_top_processes(n: int = 8) -> list:
    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent",
                                   "memory_percent", "status"]):
        try:
            info = p.info
            if info["cpu_percent"] is not None:
                procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return sorted(
        procs, key=lambda x: x.get("cpu_percent", 0), reverse=True
    )[:n]


def get_uptime() -> str:
    boot  = datetime.fromtimestamp(psutil.boot_time())
    delta = datetime.now() - boot
    hours, rem = divmod(int(delta.total_seconds()), 3600)
    mins = rem // 60
    if hours >= 24:
        return f"{hours // 24}d {hours % 24}h {mins}m"
    return f"{hours}h {mins}m"


def get_failed_services() -> list:
    """Returns any failed systemd services on Ubuntu."""
    try:
        result = subprocess.run(
            ["systemctl", "--failed", "--no-pager", "--no-legend"],
            capture_output=True, text=True, timeout=5,
        )
        failed = []
        for line in result.stdout.strip().splitlines():
            parts = line.split()
            if parts:
                failed.append({
                    "name":   parts[0],
                    "active": "failed",
                    "sub":    "failed",
                })
        return failed
    except Exception:
        return []


def snapshot() -> dict:
    """Full system snapshot — used by oma monitor."""
    return {
        "timestamp":     datetime.now().isoformat(),
        "platform":      platform.platform(),
        "uptime":        get_uptime(),
        "cpu":           get_cpu(),
        "memory":        get_memory(),
        "disk":          get_disk(),
        "network":       get_network(),
        "top_processes": get_top_processes(),
        "services":      get_failed_services(),
    }
