# netconkit 🌐

A **mini network recon toolkit** (informational only). Designed for your own networks.

## Features (v0.1)
- Show local interfaces + IPs
- Show default gateway (best-effort)
- Show ARP neighbors (best-effort)
- Optional ping sweep for a CIDR (simple, slow, safe)

## Install (dev)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install -e .
```

## Usage
```bash
netconkit ifaces
netconkit gateway
netconkit arp
netconkit sweep 192.168.1.0/24 --limit 64
```
