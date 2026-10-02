# CyberSaathi Gateway — Setup & Reproduction (v0.6)

This document reproduces the CyberSaathi home security gateway on a Kali Linux
VM, exactly as built. The gateway routes a client device's traffic, filters
scam/malware domains, detects attacks, and reports threats to the app.

## Lab topology

```
Windows 7 (client)  →  Kali (gateway)  →  Internet (VirtualBox NAT)
  Host-Only LAN            eth0 = LAN 192.168.56.110
  192.168.56.0/24          eth1 = internet (NAT, 10.0.3.x)
```

- Kali VM: **Adapter 1 = Host-Only** (eth0, the LAN), **Adapter 2 = NAT** (eth1,
  internet).
- Windows 7 VM: **Host-Only only** (same network as Kali eth0). Static IP:
  - IP `192.168.56.50`, mask `255.255.255.0`
  - Gateway `192.168.56.110` (Kali), DNS `192.168.56.110` (Kali, for filtering)
- Metasploitable2 stays on the isolated Host-Only network — **never Bridged**.

> Interface names (eth0 LAN / eth1 internet) and Kali's LAN IP (192.168.56.110)
> are specific to this lab — check `ip a` and adjust if different.

---

## Stage A — Routing (NAT)

`ip_forward` + masquerade let Kali route the client to the internet. These are
applied by the startup script below (made persistent via systemd).

## Stage B — DNS filtering (dnsmasq)

```
sudo apt install -y dnsmasq
```

`/etc/dnsmasq.d/cybersaathi.conf`:
```
# Answer DNS only on the LAN interface (facing the client)
interface=eth0
bind-interfaces
listen-address=192.168.56.110

# Upstream resolvers for ALLOWED domains
no-resolv
server=8.8.8.8
server=1.1.1.1

# Log every lookup so CyberSaathi can report blocks
log-queries
log-facility=/var/log/dnsmasq.log
```

`/etc/dnsmasq.d/cybersaathi-blocklist.conf`:
```
# Blocked scam/malware domains — block BOTH IPv4 (A) and IPv6 (AAAA)
address=/example.com/0.0.0.0
address=/example.com/::
address=/paisa-jitnuhos.com/0.0.0.0
address=/paisa-jitnuhos.com/::
address=/free-esewa-bonus.com/0.0.0.0
address=/free-esewa-bonus.com/::
```

```
sudo systemctl enable dnsmasq
sudo systemctl restart dnsmasq
```

Test: `nslookup example.com 192.168.56.110` → `0.0.0.0` / `::` (blocked);
`nslookup google.com 192.168.56.110` → real IPs (allowed).

## Stage C — Suricata IDS

```
sudo apt install -y suricata
sudo suricata-update          # pull Emerging Threats Open ruleset
```

`/etc/suricata/rules/cybersaathi-test.rules`:
```
alert icmp any any -> any any (msg:"CyberSaathi TEST - ICMP ping seen"; sid:1000001; rev:1;)
alert tcp any any -> any any (msg:"CyberSaathi: possible port scan detected"; flags:S; threshold:type both, track by_src, count 20, seconds 10; classtype:attempted-recon; sid:1000002; rev:1;)
```

Suricata is started on `eth0` by the startup script below.
Test: run `sudo nmap -sS -T4 192.168.56.50` and the scan rule fires in
`/var/log/suricata/eve.json`.

## Stage D — Alerts to the app

`netscan/alert_report.py` reads `eve.json`, maps categories to bilingual advice
via `netscan/alert_rules.json`, and POSTs to the backend:
```
python3 netscan/alert_report.py --post https://cybersaathi-gmrv.onrender.com/alerts/scan
```
Backend endpoints: `POST /alerts/scan`, `GET /alerts/latest`. App "Alerts" tab
reads `/alerts/latest`.

---

## Persistence (startup on every boot)

`/usr/local/bin/cybersaathi-gateway.sh`:
```bash
#!/bin/bash
# CyberSaathi home gateway bring-up (routing + NAT + Suricata)
LAN=eth0
WAN=eth1
RULES=/etc/suricata/rules/cybersaathi-test.rules

sysctl -w net.ipv4.ip_forward=1

iptables -t nat -C POSTROUTING -o "$WAN" -j MASQUERADE 2>/dev/null || \
  iptables -t nat -A POSTROUTING -o "$WAN" -j MASQUERADE
iptables -C FORWARD -i "$LAN" -o "$WAN" -j ACCEPT 2>/dev/null || \
  iptables -A FORWARD -i "$LAN" -o "$WAN" -j ACCEPT
iptables -C FORWARD -i "$WAN" -o "$LAN" -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || \
  iptables -A FORWARD -i "$WAN" -o "$LAN" -m state --state RELATED,ESTABLISHED -j ACCEPT

if ! pgrep -x suricata >/dev/null; then
  rm -f /var/run/suricata.pid /run/suricata/suricata.pid
  suricata -i "$LAN" -s "$RULES" -D
fi

echo "CyberSaathi gateway up."
```

`/etc/systemd/system/cybersaathi-gateway.service`:
```ini
[Unit]
Description=CyberSaathi home gateway (routing, NAT, Suricata)
After=network-online.target dnsmasq.service
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/cybersaathi-gateway.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

```
sudo chmod +x /usr/local/bin/cybersaathi-gateway.sh
sudo systemctl daemon-reload
sudo systemctl enable --now cybersaathi-gateway.service
```

Verify after a reboot (nothing run by hand):
```
cat /proc/sys/net/ipv4/ip_forward     # 1
sudo iptables -t nat -L POSTROUTING -n # MASQUERADE present
pgrep -a suricata                      # running
```

---

## Honest limitations (for the dissertation / viva)

- Kali is both gateway and attacker in the scan demo for convenience; a real
  deployment uses a separate device as the attacker (detection is identical).
- The backend stores the latest scan/alert set **in memory** (lost on free-tier
  restart) — push data at the start of a demo.
- Only a representative set of Suricata alert categories is mapped to plain
  language; unmapped signatures fall back to a MEDIUM default; `ET INFO` noise
  is down-ranked to LOW.
- DNS filtering uses a small manual blocklist; production would subscribe to a
  threat-intel domain feed.
- Ethical scope: isolated Host-Only lab, only user-owned devices scanned,
  Metasploitable2 never bridged to a real network.
