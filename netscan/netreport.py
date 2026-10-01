#!/usr/bin/env python3
"""CyberSaathi network reporter (v0.5).
Reads an Nmap XML scan (-oX) and turns the open ports into plain-language,
bilingual advice for a non-technical home user.

Usage:
  python3 netreport.py scan.xml            # English report
  python3 netreport.py scan.xml --ne       # Nepali report
  python3 netreport.py scan.xml --json     # machine-readable (for the app/backend)
"""
import sys, json
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULES = json.loads((HERE / "network_rules.json").read_text(encoding="utf-8"))
SERVICES = RULES["services"]
DEFAULT = RULES["default"]
SEV_RANK = {"high": 3, "medium": 2, "low": 1, "info": 0}
LEVEL_NAME = {3: "HIGH", 2: "MEDIUM", 1: "LOW", 0: "SAFE"}


def parse_scan(xml_path):
    root = ET.parse(xml_path).getroot()
    hosts = []
    for host in root.findall("host"):
        status = host.find("status")
        if status is not None and status.get("state") != "up":
            continue
        ip = ""
        for addr in host.findall("address"):
            if addr.get("addrtype") in ("ipv4", "ipv6") and addr.get("addr"):
                ip = addr.get("addr")
        hn = host.find("hostnames/hostname")
        hostname = hn.get("name") if hn is not None and hn.get("name") else ""
        ports = []
        for p in host.findall("ports/port"):
            state = p.find("state")
            if state is None or state.get("state") != "open":
                continue
            svc = p.find("service")
            product = (svc.get("product") if svc is not None else "") or ""
            version = (svc.get("version") if svc is not None else "") or ""
            name = (svc.get("name") if svc is not None else "") or ""
            ports.append({"port": p.get("portid"),
                          "seen": " ".join(x for x in [product, version] if x) or name})
        hosts.append({"ip": ip, "hostname": hostname, "ports": ports})
    return hosts


def assess(host, lang="en"):
    findings = []
    for p in host["ports"]:
        rule = SERVICES.get(p["port"], DEFAULT)
        findings.append({
            "port": p["port"], "seen": p["seen"],
            "name": rule["name_" + lang], "severity": rule["severity"],
            "reason": rule["reason_" + lang], "action": rule["action_" + lang],
        })
    top = max((SEV_RANK[f["severity"]] for f in findings), default=0)
    findings.sort(key=lambda f: -SEV_RANK[f["severity"]])
    return LEVEL_NAME[top], findings


def render(host, lang="en"):
    level, findings = assess(host, lang)
    L = RULES["labels"][lang]
    icons = {"high": "⛔", "medium": "⚠️", "low": "•", "info": "•"}
    out = []
    title = host["hostname"] or host["ip"]
    out.append("=" * 56)
    out.append(f"{L['device']}: {title}   ({host['ip']})")
    out.append(f"{L['risk']}: {level}  —  {RULES['level_summary'][level][lang]}")
    out.append(L["open_count"].format(n=len(findings)))
    out.append("=" * 56)
    for f in findings:
        out.append("")
        out.append(f"{icons[f['severity']]}  {L['port']} {f['port']} — {f['name']}   [{f['seen']}]")
        out.append(f"    {L['why']}: {f['reason']}")
        out.append(f"    {L['do']}: {f['action']}")
    return "\n".join(out)


def main():
    args = sys.argv[1:]
    lang = "ne" if "--ne" in args else "en"
    as_json = "--json" in args
    files = [a for a in args if not a.startswith("--")]
    if not files:
        print(__doc__)
        sys.exit(1)
    hosts = parse_scan(files[0])
    if as_json:
        report = []
        for h in hosts:
            level, findings = assess(h, lang)
            report.append({"ip": h["ip"], "hostname": h["hostname"],
                           "risk": level, "findings": findings})
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    if not hosts:
        print("No live hosts found in the scan.")
        return
    for h in hosts:
        print(render(h, lang))
        print()


if __name__ == "__main__":
    main()
