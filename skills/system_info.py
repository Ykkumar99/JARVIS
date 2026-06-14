"""
J.A.R.V.I.S. — System Info Skill
Uses psutil to report system statistics.
"""

import psutil
import platform


def get_cpu_info() -> str:
    """Get CPU usage."""
    usage = psutil.cpu_percent(interval=1)
    count = psutil.cpu_count()
    freq = psutil.cpu_freq()
    freq_str = f" running at {freq.current:.0f} MHz" if freq else ""
    return f"CPU usage is at {usage}% across {count} cores{freq_str}, sir."


def get_ram_info() -> str:
    """Get RAM usage."""
    mem = psutil.virtual_memory()
    used_gb = mem.used / (1024 ** 3)
    total_gb = mem.total / (1024 ** 3)
    percent = mem.percent
    return f"Memory usage is at {percent}%. {used_gb:.1f} GB used out of {total_gb:.1f} GB total, sir."


def get_battery_info() -> str:
    """Get battery status."""
    battery = psutil.sensors_battery()
    if battery is None:
        return "No battery detected. You appear to be on a desktop system, sir."
    percent = battery.percent
    plugged = "plugged in" if battery.power_plugged else "on battery power"
    if battery.secsleft > 0 and not battery.power_plugged:
        hours = battery.secsleft // 3600
        minutes = (battery.secsleft % 3600) // 60
        return f"Battery is at {percent}%, {plugged}. Approximately {hours} hours and {minutes} minutes remaining, sir."
    return f"Battery is at {percent}%, {plugged}, sir."


def get_disk_info() -> str:
    """Get disk usage."""
    disk = psutil.disk_usage("/")
    used_gb = disk.used / (1024 ** 3)
    total_gb = disk.total / (1024 ** 3)
    free_gb = disk.free / (1024 ** 3)
    return f"Disk usage: {used_gb:.1f} GB used out of {total_gb:.1f} GB. {free_gb:.1f} GB free, sir."


def get_all_info() -> str:
    """Get a comprehensive system overview."""
    parts = []
    parts.append(f"System: {platform.system()} {platform.release()}")
    
    cpu = psutil.cpu_percent(interval=1)
    parts.append(f"CPU: {cpu}%")
    
    mem = psutil.virtual_memory()
    parts.append(f"RAM: {mem.percent}% ({mem.used / (1024**3):.1f}/{mem.total / (1024**3):.1f} GB)")
    
    disk = psutil.disk_usage("/")
    parts.append(f"Disk: {disk.percent}% used")
    
    battery = psutil.sensors_battery()
    if battery:
        parts.append(f"Battery: {battery.percent}%")
    
    overview = ". ".join(parts)
    return f"System status report: {overview}. All systems nominal, sir."


def get_system_info(info_type: str = "all") -> str:
    """Route system info requests."""
    handlers = {
        "cpu": get_cpu_info,
        "ram": get_ram_info,
        "memory": get_ram_info,
        "battery": get_battery_info,
        "disk": get_disk_info,
        "storage": get_disk_info,
        "all": get_all_info,
    }
    handler = handlers.get(info_type, get_all_info)
    return handler()
