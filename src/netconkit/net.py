from __future__ import annotations

import ipaddress
import platform
import subprocess
from typing import Iterable

import psutil

def interfaces():
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    for name, addr_list in addrs.items():
        yield {
            "name": name,
            "is_up": bool(stats.get(name).isup) if name in stats else None,
            "addrs": [
                {"family": str(a.family), "address": a.address, "netmask": a.netmask, "broadcast": a.broadcast}
                for a in addr_list
            ],
        }

def default_gateway_best_effort() -> str | None:
    system = platform.system().lower()
    try:
        if system == "linux":
            out = subprocess.check_output(["ip", "route", "show", "default"], text=True)
            # e.g. "default via 192.168.1.1 dev wlan0 ..."
            parts = out.strip().split()
            if "via" in parts:
                return parts[parts.index("via")+1]
        elif system == "darwin":
            out = subprocess.check_output(["route", "-n", "get", "default"], text=True)
            for line in out.splitlines():
                if line.strip().startswith("gateway:"):
                    return line.split(":", 1)[1].strip()
        elif system == "windows":
            out = subprocess.check_output(["ipconfig"], text=True, errors="ignore")
            # very best-effort parsing
            for line in out.splitlines():
                if "Default Gateway" in line:
                    gw = line.split(":", 1)[1].strip()
                    if gw:
                        return gw
    except Exception:
        return None
    return None

def arp_neighbors_best_effort() -> list[dict]:
    system = platform.system().lower()
    neighbors = []
    try:
        if system == "linux":
            # Prefer `ip neigh` on Linux (more reliable than `arp -a`)
            out = subprocess.check_output(["ip", "neigh"], text=True, errors="ignore")
            for line in out.splitlines():
                # e.g. "10.0.0.1 dev wlan0 lladdr aa:bb:cc:dd:ee:ff REACHABLE"
                parts = line.split()
                if not parts:
                    continue
                ip = parts[0]
                mac = None
                if "lladdr" in parts:
                    mac = parts[parts.index("lladdr")+1]
                neighbors.append({"ip": ip, "mac": mac})
        elif system == "darwin":
            out = subprocess.check_output(["arp", "-a"], text=True, errors="ignore")
            for line in out.splitlines():
                if "(" in line and ")" in line:
                    ip = line.split("(", 1)[1].split(")", 1)[0]
                    mac = None
                    if " at " in line:
                        mac = line.split(" at ", 1)[1].split(" ", 1)[0]
                    neighbors.append({"ip": ip, "mac": mac})
        elif system == "windows":
            out = subprocess.check_output(["arp", "-a"], text=True, errors="ignore")
            for line in out.splitlines():
                parts = line.split()
                if len(parts) >= 3 and parts[0].count(".") == 3:
                    neighbors.append({"ip": parts[0], "mac": parts[1]})
    except Exception:
        pass
    return neighbors

def cidr_hosts(cidr: str) -> Iterable[str]:
    net = ipaddress.ip_network(cidr, strict=False)
    for ip in net.hosts():
        yield str(ip)
