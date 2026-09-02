"""Simulate syslog traffic from each equipment type, for local testing
of the collector + parsers without needing real devices.

Usage:
    python scripts/send_test_logs.py [host] [port]
"""
import socket
import sys
import time
from datetime import datetime

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5514

TODAY = datetime.now().strftime("%Y-%m-%d")

SAMPLE_LOGS = [
    # FortiGate — date générée dynamiquement pour rester "aujourd'hui" à chaque exécution
    f'date={TODAY} time=08:12:04 devname="FGT600E" devid="FG600E1234567890" '
    'logid="0000000013" type="utm" subtype="virus" level="warning" '
    'srcip=41.226.13.90 dstip=192.168.1.42 action="blocked" msg="File was infected/blocked"',

    f'date={TODAY} time=06:40:02 devname="FGT600E" devid="FG600E1234567890" '
    'logid="0000000020" type="ips" subtype="signature" level="critical" '
    'srcip=203.0.113.4 dstip=192.168.1.1 action="dropped" msg="SSH.Brute.Force detected"',

    # ESET PROTECT (CEF)
    'CEF:0|ESET|ESET PROTECT|1.0|4001|Malware detected|8|'
    'src=192.168.1.42 duser=s.benali cs1=Trojan.GenericKD.68541812 act=quarantined dvchost=PC-COMPTA-04',

    # Synology DSM
    "Synology-NAS-01 SYSTEM: Warning The free space of volume 1 has fallen below 10GB.",
    'Synology-NAS-01 Backup: Info The Hyper Backup task "Daily-Backup" has been completed.',

    # Windows (via NXLog-style forwarding)
    "WIN-DC01 MSWinEventLog Security EventID=4625 Microsoft-Windows-Security-Auditing "
    "Account Name: j.dupont Source Network Address: 192.168.1.77",

    # Network gear (Cisco-style)
    "%LINK-3-UPDOWN: Interface GigabitEthernet1/0/14, changed state to up",
    "%SEC-6-IPACCESSLOGP: list 101 denied tcp 203.0.113.4(0) -> 10.0.0.1(22)",
]


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for line in SAMPLE_LOGS:
        sock.sendto(line.encode("utf-8"), (HOST, PORT))
        print(f"sent: {line[:80]}...")
        time.sleep(0.2)
    print(f"\n{len(SAMPLE_LOGS)} test logs sent to {HOST}:{PORT}")
    print("Check them with: curl http://localhost:8000/api/logs | jq")


if __name__ == "__main__":
    main()
