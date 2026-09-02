# ARGUS — Backend (Phase 1 : ingestion, normalisation, stockage)

Collecteur syslog (UDP/TCP) qui reçoit les logs de FortiGate, ESET PROTECT,
Synology, Windows et des équipements réseau, les normalise dans un schéma
commun, et les stocke dans PostgreSQL. Une API REST permet de les
interroger — c'est cette API que l'agent IA (Phase 2) utilisera pour
répondre aux questions de l'admin.

## Démarrage rapide

```bash
cp .env.example .env
docker compose up --build
```

- API : http://localhost:8000/docs (Swagger auto-généré par FastAPI)
- Syslog : port `5514` en UDP et TCP (voir note ci-dessous sur le port 514)

## Tester sans équipements réels

Un script envoie des logs d'exemple représentatifs de chaque source :

```bash
pip install -r requirements.txt   # pour avoir python dispo localement, optionnel
python scripts/send_test_logs.py 127.0.0.1 5514
```

Puis vérifier :

```bash
curl "http://localhost:8000/api/logs?limit=20" | jq
curl "http://localhost:8000/api/logs?source_type=fortigate&severity=critical" | jq
curl "http://localhost:8000/api/devices" | jq
```

## Pourquoi le port 5514 et pas 514 ?

Le port syslog standard (514) est un port privilégié (<1024) : l'écouter
nécessite d'exécuter le service en root ou de lui donner la capability
`CAP_NET_BIND_SERVICE`. Pour le développement, on utilise 5514.

En production, deux options :
1. Donner la capability au conteneur : `setcap 'cap_net_bind_service=+ep' /usr/local/bin/python3.12`
2. Faire pointer les équipements vers un relais léger (ex: `rsyslog` ou
   `syslog-ng` sur le port 514) qui retransmet vers `argus:5514`. C'est
   l'option recommandée : elle évite de faire tourner l'app en root et
   permet de tamponner les logs en cas de redémarrage du backend.

## Configuration des équipements (à faire côté réseau)

| Équipement | Où configurer |
|---|---|
| FortiGate | `Log & Report > Log Settings > Send Logs to Syslog` → IP du serveur ARGUS, port 514/5514 |
| ESET PROTECT | `Server Settings > Syslog Server` → activer, format CEF |
| Synology DSM | `Log Center > Log Sending > Send logs to syslog server` |
| Windows | Installer un agent de forwarding (NXLog Community Edition recommandé) configuré pour envoyer vers ARGUS |
| Switch/Routeur | `logging host <ip_argus>` (Cisco-like) ou équivalent constructeur |

## Endpoints disponibles

| Méthode | Route | Usage |
|---|---|---|
| GET | `/api/logs` | Filtrable par `source_type`, `severity`, `q`, `since`, `until` — alimente les pages Logs / Requêtes / Tableau de bord |
| GET | `/api/devices` | Inventaire des équipements, `status` calculé depuis `last_seen` (< 5 min = online) |
| PATCH | `/api/devices/{id}` | Renseigner manuellement `vendor`, `model`, `version`, `name` — non déductible du syslog seul |
| GET | `/api/stats/overview?hours=24` | Agrégats pour le dashboard : total d'événements, répartition par sévérité, top catégories, volume horaire par source |
| POST | `/api/agent/chat` | Agent IA (Gemini + function calling sur `search_logs`, `get_stats_overview`, `list_devices`) |
| GET | `/api/reports` | Historique des rapports générés |
| POST | `/api/reports/generate` | Génère un rapport `{"period": "daily"\|"weekly"}` à la demande |
| GET | `/api/reports/{id}/download` | Télécharge le PDF |
| GET | `/health` | Vérification de disponibilité, utilisée par le frontend pour l'indicateur "Système Opérationnel" |

## Rapports PDF (automatiques + à la demande)

Générés avec **reportlab** à partir des vraies données (`/api/stats/overview` +
événements critiques + inventaire équipements), stockés sur disque
(`REPORTS_DIR`, monté en volume Docker pour survivre aux redémarrages) et
indexés dans la table `reports`.

Planification automatique via **APScheduler** (`ENABLE_SCHEDULED_REPORTS=true`) :
- Quotidien à 05:00 UTC
- Hebdomadaire le lundi à 06:00 UTC

Génération manuelle :
```bash
curl -X POST http://localhost:8000/api/reports/generate \
  -H "Content-Type: application/json" -d '{"period": "daily"}'
```

## Agent IA (Gemini)

L'agent utilise le SDK officiel **`google-genai`** (pas l'ancien `google-generativeai`,
déprécié) avec function calling manuel : Gemini décide quel outil appeler
(`search_logs`, `get_stats_overview`, `list_devices`), le backend l'exécute contre
PostgreSQL, renvoie le résultat au modèle, qui formule la réponse finale en français.

1. Créer une clé gratuite sur https://aistudio.google.com/apikey
2. La renseigner dans `.env` : `GEMINI_API_KEY=...`
3. Redémarrer : `docker compose up --build`

> Les modèles gratuits disponibles changent régulièrement côté Google (ex: `gemini-2.0-flash`
> a été retiré le 3 mars 2026). Si l'agent renvoie une erreur `429 RESOURCE_EXHAUSTED` avec
> `limit: 0`, ça signifie que le modèle configuré dans `GEMINI_MODEL` n'est plus sur le tier
> gratuit — vérifier la liste actuelle sur https://ai.google.dev/gemini-api/docs/pricing et
> mettre à jour `GEMINI_MODEL` dans `.env` en conséquence (actuellement : `gemini-2.5-flash`
> ou `gemini-2.5-flash-lite`).

Tester directement :
```bash
curl -X POST http://localhost:8000/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Resume les evenements critiques d aujourd hui"}'
```

Sans clé configurée, l'endpoint répond avec un message explicite plutôt que planter —
pratique pour développer le reste de la plateforme sans dépendre de Gemini.

## Comment ajouter un nouveau parser

1. Créer `app/collector/parsers/mon_vendor.py`, hériter de `BaseParser`
2. Implémenter `matches()` (détection rapide) et `parse()` (extraction → `NormalizedLog`)
3. L'enregistrer avec `register(MonVendorParser())` en bas du fichier
4. L'importer dans `app/collector/parsers/__init__.py`

Aucune autre partie du système n'a besoin de changer — le pipeline,
l'API et (bientôt) l'agent IA travaillent uniquement sur le schéma
`NormalizedLog` commun, jamais sur le format brut d'un vendeur en particulier.

## Schéma normalisé (`NormalizedLog`)

```
timestamp, source_ip, source_type, source_device,
severity (critical|warning|info),
event_type, src_ip, dst_ip, user,
message, raw, extra (JSONB — champs spécifiques au vendeur)
```

Ce schéma est volontairement le même que celui utilisé dans la maquette
frontend (page Journaux) — le mapping vers l'UI sera direct.

## Ce qui n'est pas encore fait (prochaines phases)

- **Phase 2** : agent conversationnel (function calling sur `/api/logs`)
- **Phase 3** : corrélation multi-sources (hors périmètre V1, prévu plus tard)
- **Phase 5 (V1)** : génération automatique de rapports PDF planifiés —
  prochaine étape après la validation de cette base d'ingestion
- Migrations Alembic (le MVP crée les tables automatiquement au démarrage)
- Authentification sur l'API (à ajouter avant tout déploiement réel)
