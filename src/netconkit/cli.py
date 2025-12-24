from __future__ import annotations

import asyncio
import platform
import subprocess

import typer
from rich.console import Console
from rich.table import Table

from .net import interfaces, default_gateway_best_effort, arp_neighbors_best_effort, cidr_hosts

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()

@app.command()
def ifaces():
    """Show network interfaces and addresses."""
    table = Table(title="interfaces")
    table.add_column("Name")
    table.add_column("Up")
    table.add_column("Addresses")
    for it in interfaces():
        addrs = ", ".join(a["address"] for a in it["addrs"] if a.get("address"))
        table.add_row(it["name"], "✅" if it["is_up"] else "—", addrs)
    console.print(table)

@app.command()
def gateway():
    """Show default gateway (best-effort)."""
    gw = default_gateway_best_effort()
    if gw:
        console.print(f"Default gateway: [green]{gw}[/green]")
    else:
        console.print("[yellow]Could not determine gateway.[/yellow]")

@app.command()
def arp():
    """Show ARP neighbors (best-effort)."""
    neigh = arp_neighbors_best_effort()
    table = Table(title="ARP neighbors")
    table.add_column("IP")
    table.add_column("MAC")
    for n in neigh:
        table.add_row(n.get("ip",""), n.get("mac") or "")
    console.print(table)

async def _ping(ip: str) -> bool:
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", "1", "-w", "600", ip]
    else:
        cmd = ["ping", "-c", "1", "-W", "1", ip]
    try:
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        rc = await proc.wait()
        return rc == 0
    except Exception:
        return False

@app.command()
def sweep(cidr: str, limit: int = typer.Option(64, help="Max concurrent pings")):
    """Ping-sweep a CIDR (slow, informational)."""
    async def run():
        sem = asyncio.Semaphore(limit)
        live = []

        async def one(ip: str):
            async with sem:
                if await _ping(ip):
                    live.append(ip)

        tasks = [one(ip) for ip in cidr_hosts(cidr)]
        await asyncio.gather(*tasks)

        table = Table(title=f"Live hosts: {cidr}")
        table.add_column("IP")
        for ip in sorted(live):
            table.add_row(ip)
        console.print(table)

    asyncio.run(run())

def main():
    app()

if __name__ == "__main__":
    main()
