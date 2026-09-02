# ARGUS — Déploiement production (lab GNS3)

Topologie de référence :

| Nœud | IP | Rôle |
|---|---|---|
| Forti-Firewall | 192.168.1.1 | Pare-feu périmétrique |
| ESETProtect-1 | 192.168.1.10 | Console ESET PROTECT |
| **Serveur-APK** | **192.168.1.20** | **Serveur ARGUS (ce dépôt)** |
| Backup-Server | 192.168.1.100 | Simulateur NAS/sauvegarde |
| EDR-1 / EDR-2 / EDR-3 | 192.168.1.21-23 (à définir) | Ubuntu + agent ESET |

Tous les équipements envoient leur syslog vers **192.168.1.20:5514** (UDP ou TCP).

---

## 1. Déploiement sur Serveur-APK (192.168.1.20)

```bash
# Docker + Compose (si pas déjà fait)
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER   # puis se reconnecter

# Récupérer le projet (backend/ + frontend/ + docker-compose.prod.yml + Caddyfile)
cd ~ && unzip argus-production.zip && cd argus-production

# Configuration backend
cp backend/.env.example backend/.env
nano backend/.env
#   -> GEMINI_API_KEY=...              (clé gratuite sur aistudio.google.com/apikey)
#   -> POSTGRES_PASSWORD si tu le changes ici, le refléter aussi dans le
#      DATABASE_URL de backend/.env (même mot de passe des deux côtés)

# Build + lancement
docker compose -f docker-compose.prod.yml up --build -d

# Vérification
docker compose -f docker-compose.prod.yml ps
curl http://localhost/health
curl http://localhost/api/devices
```

Le frontend est servi sur `http://192.168.1.20/` (port 80, via Caddy) — plus besoin de
configurer une URL d'API dans Paramètres, les chemins sont relatifs par défaut.

### Pare-feu du serveur Ubuntu

```bash
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 5514/udp
sudo ufw allow 5514/tcp
sudo ufw enable
```

---

## 2. FortiGate (192.168.1.1) — envoyer les logs vers ARGUS

Console CLI FortiGate :

```
config log syslogd setting
    set status enable
    set server "192.168.1.20"
    set port 5514
    set mode udp
    set facility local7
    set format default
end

config log syslogd filter
    set severity information
end
```

---

## 3. ESET PROTECT (192.168.1.10) — export syslog CEF

Dans la console web ESET PROTECT :

`More → Settings → Advanced Settings → Syslog Server`
- **Enable Syslog server** : activé
- **Host** : `192.168.1.20`
- **Port** : `5514`
- **Format** : `CEF`
- **Transport** : UDP (ou TCP si le lab le permet)

Enregistrer, puis vérifier dans `Server Settings → Diagnostics` qu'aucune erreur d'export
n'apparaît.

---

## 4. EDR-1 / EDR-2 / EDR-3 (serveurs Ubuntu) — agent ESET + logs OS

**a. Agent ESET** : installer l'agent ESET Management Agent (`.deb` fourni par la console
ESET PROTECT, menu `Quick Links → Deploy Agent`), pointé vers `192.168.1.10`. Une fois
enrôlé, les détections remontent automatiquement à ESET PROTECT → ARGUS (étape 3) — rien
à configurer côté EDR pour ce flux-là.

**b. Logs système (auth, sudo)** — pour que le nouveau parser Linux les capture, configurer
`rsyslog` pour forwarder vers ARGUS :

```bash
# Sur chaque EDR (192.168.1.21, .22, .23)
sudo tee /etc/rsyslog.d/60-argus.conf > /dev/null <<'EOF'
# Forward auth/sudo logs to ARGUS
if $programname == 'sshd' or $programname == 'sudo' then @192.168.1.20:5514
& stop
EOF

sudo systemctl restart rsyslog
```

Test rapide :
```bash
logger -t sudo "test : sbenali : TTY=pts/0 ; PWD=/home/sbenali ; USER=root ; COMMAND=/usr/bin/whoami"
```
Puis vérifier côté ARGUS : `curl http://192.168.1.20/api/logs?source_type=linux`

---

## 5. Backup-Server (192.168.1.100) — simulateur NAS

Ce nœud n'étant pas un vrai Synology, on simule des logs au bon format directement :

```bash
sudo tee /etc/rsyslog.d/60-argus.conf > /dev/null <<'EOF'
if $programname == 'backup-sim' then @192.168.1.20:5514
& stop
EOF
sudo systemctl restart rsyslog

# Script de simulation (à lancer en cron ou systemd timer, ex: toutes les heures)
sudo tee /usr/local/bin/backup-sim.sh > /dev/null <<'EOF'
#!/bin/bash
HOST="Synology-NAS-01"
logger -t backup-sim "$HOST Backup: Info The Hyper Backup task \"Daily-Backup\" has been completed."
EOF
sudo chmod +x /usr/local/bin/backup-sim.sh

# Toutes les heures
( crontab -l 2>/dev/null; echo "0 * * * * /usr/local/bin/backup-sim.sh" ) | crontab -
```

> Note : le parser Synology actuel attend un format `HOTE CATEGORIE: Niveau message`
> (voir `backend/app/collector/parsers/synology.py`). Adapter le script ci-dessus si tu
> veux varier les catégories (`SYSTEM`, `Security`...).

---

## 6. Checklist de vérification en conditions réelles

```bash
# 1. Chaque équipement atteint bien ARGUS sur le port syslog
#    (depuis chaque nœud GNS3)
nc -zvu 192.168.1.20 5514

# 2. Les logs arrivent et sont bien répartis par source
curl http://192.168.1.20/api/devices
curl "http://192.168.1.20/api/logs?limit=20"

# 3. Le tableau de bord affiche des données réelles
#    -> ouvrir http://192.168.1.20/ dans un navigateur

# 4. L'agent IA répond avec du function calling réel
curl -X POST http://192.168.1.20/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Resume les evenements critiques d aujourd hui"}'

# 5. Un rapport PDF se génère à partir des vraies données
curl -X POST http://192.168.1.20/api/reports/generate \
  -H "Content-Type: application/json" -d '{"period": "daily"}'
```

Si une étape échoue, vérifier dans l'ordre : connectivité réseau GNS3 (ping) → règles
`ufw` sur Serveur-APK → logs du conteneur (`docker compose -f docker-compose.prod.yml
logs backend --tail=50`).
