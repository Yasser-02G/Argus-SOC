"""Test de charge et de robustesse du pipeline d'ingestion ARGUS.

Deux volets :
1. Volume réaliste — génère un grand nombre de logs valides, variés,
   répartis sur les 6 sources (fortigate, eset, synology, windows, linux,
   network), pour vérifier le débit et l'absence de perte.
2. Robustesse — envoie des logs volontairement malformés (tronqués,
   encodage invalide, taille excessive, vides, gibberish) pour vérifier
   que le parser de secours (`unknown`) absorbe tout sans jamais faire
   planter le collecteur.

Usage :
    python scripts/stress_test_logs.py --host 127.0.0.1 --port 5514 \
        --count 2000 --malformed 200 --api-base http://127.0.0.1:8000

Avec --dry-run, rien n'est envoyé : affiche juste des échantillons et les
totaux prévus, pour relecture avant de lancer pour de vrai.
"""
import argparse
import random
import socket
import time
import urllib.request
import urllib.error
import json

FORTIGATE_TYPES = [("utm", "virus", "warning"), ("ips", "signature", "critical"), ("traffic", "forward", "information")]
ESET_THREATS = ["Trojan.GenericKD", "PUA.Adware.OpenCandy", "Win32/Exploit.CVE-2024-21412", "HTML/Phishing.Agent"]
SYNOLOGY_MSGS = [
    ("SYSTEM", "Warning", "The free space of volume 1 has fallen below 10GB."),
    ("Backup", "Info", 'The Hyper Backup task "Daily-Backup" has been completed.'),
    ("Security", "Error", "Multiple failed login attempts detected from [{ip}]."),
]
WIN_EVENTS = ["4624", "4625", "4720", "4740", "1102", "4688"]
CISCO_FACILITIES = [("LINK", 3, "UPDOWN"), ("SEC", 6, "IPACCESSLOGP"), ("SYS", 5, "CONFIG_I")]
USERS = ["s.benali", "j.dupont", "k.tazi", "admin", "y.idrissi", "n.amrani"]


def rand_ip(private=False):
    if private:
        return f"192.168.1.{random.randint(2, 250)}"
    return f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"


def gen_fortigate():
    t, sub, lvl = random.choice(FORTIGATE_TYPES)
    return (
        f'date=2026-08-09 time={random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d} '
        f'devname="FGT600E" devid="FG600E1234567890" logid="000000{random.randint(10,99)}" '
        f'type="{t}" subtype="{sub}" level="{lvl}" srcip={rand_ip()} dstip={rand_ip(private=True)} '
        f'action="blocked" msg="Simulated {t}/{sub} event #{random.randint(1,99999)}"'
    )


def gen_eset():
    threat = random.choice(ESET_THREATS)
    host = f"PC-{random.choice(['COMPTA','RH','DEV','DIR'])}-{random.randint(1,20):02d}"
    return (
        f'CEF:0|ESET|ESET PROTECT|1.0|4001|Malware detected|{random.randint(4,10)}|'
        f'src={rand_ip(private=True)} duser={random.choice(USERS)} cs1={threat}.{random.randint(10000000,99999999)} '
        f'act=quarantined dvchost={host}'
    )


def gen_synology():
    cat, level, msg = random.choice(SYNOLOGY_MSGS)
    return f"Synology-NAS-01 {cat}: {level} {msg.format(ip=rand_ip())}"


def gen_windows():
    eid = random.choice(WIN_EVENTS)
    return (
        f"WIN-DC01 MSWinEventLog Security EventID={eid} Microsoft-Windows-Security-Auditing "
        f"Account Name: {random.choice(USERS)} Source Network Address: {rand_ip()}"
    )


def gen_linux():
    host = f"ubuntu-edr-{random.randint(1,3):02d}"
    if random.random() < 0.5:
        return f"{host} sshd[{random.randint(1000,9999)}]: Failed password for {random.choice(USERS)} from {rand_ip()} port {random.randint(1024,65000)} ssh2"
    return f"{host} sudo: {random.choice(USERS)} : TTY=pts/0 ; PWD=/home ; USER=root ; COMMAND=/usr/bin/apt update"


def gen_network():
    fac, sev, mnem = random.choice(CISCO_FACILITIES)
    if mnem == "UPDOWN":
        state = random.choice(["up", "down"])
        return f"%{fac}-{sev}-{mnem}: Interface GigabitEthernet1/0/{random.randint(1,48)}, changed state to {state}"
    return f"%{fac}-{sev}-{mnem}: list 101 denied tcp {rand_ip()}({random.randint(1,60000)}) -> {rand_ip(private=True)}(22)"


GENERATORS = [gen_fortigate, gen_eset, gen_synology, gen_windows, gen_linux, gen_network]


# ---------------------------------------------------------------
# Logs malformés — chacun cible une classe de robustesse différente
# ---------------------------------------------------------------
def malformed_batch():
    return [
        ("vide", ""),
        ("espaces seuls", "   \t  "),
        ("gibberish", "".join(random.choices("!@#$%^&*()_+={}[]|\\<>?/~`", k=80))),
        ("fortigate tronqué", 'date=2026-08 time= devname="FGT' ),
        ("cef cassé (guillemets non fermés)", 'CEF:0|ESET|ESET PROTECT|1.0|4001|Malware detected|src=192.168.1.99 cs1="Trojan'),
        ("synology sans niveau reconnu", "Synology-NAS-01 SYSTEM: Critique espace disque"),
        ("windows sans eventid", "WIN-DC01 MSWinEventLog Security Something Happened No ID Here"),
        ("cisco sévérité invalide", "%LINK-X-UPDOWN: Interface Gi1/0/1 changed state to up"),
        ("message énorme (50k caractères)", "A" * 50_000),
        ("json inattendu", json.dumps({"unexpected": "format", "not": "syslog", "n": random.randint(1, 999)})),
        ("injection-like", "'; DROP TABLE log_entries; -- from source=fortigate"),
        ("unicode exotique", "🔥💀🚨 événement critïque avec ÉMOJIS et accents 日本語 🚨💀🔥"),
        ("multi-lignes collées", "ligne1\nligne2 devname=\"FGT\" srcip=1.2.3.4\nligne3"),
    ]


def send_udp(sock, host, port, text):
    sock.sendto(text.encode("utf-8", errors="ignore"), (host, port))


def send_udp_raw_bytes(sock, host, port, data: bytes):
    sock.sendto(data, (host, port))


def api_get(api_base, path):
    try:
        with urllib.request.urlopen(f"{api_base}{path}", timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.URLError as e:
        return None, str(e)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5514)
    ap.add_argument("--count", type=int, default=1000, help="Nombre de logs valides à envoyer")
    ap.add_argument("--malformed", type=int, default=100, help="Nombre de passes de logs malformés (répète le batch)")
    ap.add_argument("--api-base", default=None, help="ex: http://127.0.0.1:8000 — active la vérification post-test")
    ap.add_argument("--rate", type=float, default=0, help="Pause en secondes entre logs valides (0 = envoi en rafale)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    print(f"=== Volet 1 : {args.count} logs valides, répartis sur {len(GENERATORS)} sources ===")
    if args.dry_run:
        for gen in GENERATORS:
            print(f"  [{gen.__name__}] exemple: {gen()[:100]}...")
        print(f"\n=== Volet 2 : {args.malformed} passes du batch malformé ({len(malformed_batch())} cas/passe) ===")
        for label, payload in malformed_batch():
            preview = payload[:60].replace("\n", "\\n")
            print(f"  [{label}] {preview}...")
        print("\n(dry-run — rien envoyé)")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    t0 = time.time()

    # --- Volet 1 : volume réaliste ---
    sent_valid = 0
    for i in range(args.count):
        gen = random.choice(GENERATORS)
        send_udp(sock, args.host, args.port, gen())
        sent_valid += 1
        if args.rate:
            time.sleep(args.rate)
        elif i % 200 == 0 and i > 0:
            print(f"  ... {i}/{args.count} envoyés")
    t1 = time.time()
    print(f"Volet 1 terminé : {sent_valid} logs envoyés en {t1 - t0:.2f}s ({sent_valid / max(t1 - t0, 0.001):.0f} logs/s)")

    # --- Volet 2 : robustesse / logs malformés ---
    sent_malformed = 0
    batch = malformed_batch()
    for _ in range(args.malformed):
        for label, payload in batch:
            if "unicode" in label or "accents" in label:
                send_udp(sock, args.host, args.port, payload)
            else:
                send_udp_raw_bytes(sock, args.host, args.port, payload.encode("utf-8", errors="ignore"))
            sent_malformed += 1
    # Un vrai flux d'octets non-UTF8 (pas juste du texte mal formé) pour tester le decode()
    for _ in range(min(args.malformed, 20)):
        garbage = bytes(random.randint(0, 255) for _ in range(random.randint(10, 200)))
        send_udp_raw_bytes(sock, args.host, args.port, garbage)
        sent_malformed += 1

    t2 = time.time()
    print(f"Volet 2 terminé : {sent_malformed} logs malformés envoyés en {t2 - t1:.2f}s")
    sock.close()

    print(f"\nTotal envoyé : {sent_valid + sent_malformed} paquets UDP en {t2 - t0:.2f}s")

    if not args.api_base:
        print("\n(pas de --api-base fourni — pas de vérification automatique. "
              "Vérifie manuellement /api/logs et les logs du conteneur backend.)")
        return

    print(f"\n=== Vérification post-test via {args.api_base} ===")
    time.sleep(2)  # laisser le temps au dernier lot d'être traité (UDP async, best-effort)

    status, health = api_get(args.api_base, "/health")
    print(f"/health -> {status} {health}")
    if status != 200:
        print("‼️  Le backend ne répond plus après le test de charge — c'est un vrai problème à investiguer "
              "(docker compose logs backend).")
        return

    status, logs = api_get(args.api_base, "/api/logs?limit=1")
    print(f"/api/logs (sondage) -> {status}, exemple: {logs[0] if logs else 'aucun log'}")

    status, unknown_logs = api_get(args.api_base, "/api/logs?source_type=unknown&limit=500")
    n_unknown = len(unknown_logs) if isinstance(unknown_logs, list) else "?"
    print(f"/api/logs?source_type=unknown -> {n_unknown} logs stockés via le parser de secours "
          f"(ce sont les malformés qu'aucun parser dédié n'a reconnu — c'est le comportement attendu, "
          f"pas une erreur : rien ne doit jamais être perdu ni faire planter le service)")

    status, devices = api_get(args.api_base, "/api/devices")
    print(f"/api/devices -> {len(devices) if isinstance(devices, list) else devices}")

    print("\n✅ Backend toujours opérationnel après le test de charge + robustesse.")


if __name__ == "__main__":
    main()