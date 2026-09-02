from datetime import datetime
from typing import Any, Optional

from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.repository import query_logs, stats_overview, list_devices


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

# ---------------------------------------------------------------
# Déclarations des outils exposés à Gemini. Chaque nom doit
# correspondre à une clé de TOOL_EXECUTORS ci-dessous.
# ---------------------------------------------------------------
TOOLS = [
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="search_logs",
            description=(
                "Recherche des journaux (logs) normalisés dans la base ARGUS. "
                "Utiliser pour toute question sur des événements précis : "
                "logs d'une source, d'une IP, d'une sévérité, ou correspondant à un mot-clé."
            ),
            parameters={
                "type": "OBJECT",
                "properties": {
                    "source_type": {
                        "type": "STRING",
                        "description": "Filtrer par équipement source.",
                        "enum": ["fortigate", "eset", "synology", "windows", "network"],
                    },
                    "severity": {
                        "type": "STRING",
                        "description": "Filtrer par niveau de gravité.",
                        "enum": ["critical", "warning", "info"],
                    },
                    "q": {
                        "type": "STRING",
                        "description": "Recherche libre : adresse IP, nom d'hôte, mot-clé dans le message.",
                    },
                    "since": {
                        "type": "STRING",
                        "description": (
                            "Borne de début au format ISO 8601 (ex: 2026-08-06T00:00:00Z). "
                            "À calculer à partir de la date/heure actuelle fournie dans les "
                            "instructions système pour toute question relative ('aujourd'hui', "
                            "'cette semaine', 'dernières 24h', etc.)."
                        ),
                    },
                    "until": {
                        "type": "STRING",
                        "description": "Borne de fin au format ISO 8601. Optionnel — omettre pour aller jusqu'à maintenant.",
                    },
                    "limit": {
                        "type": "INTEGER",
                        "description": "Nombre maximum de résultats (défaut 20, max 200).",
                    },
                },
            },
        ),
        types.FunctionDeclaration(
            name="get_stats_overview",
            description=(
                "Retourne des statistiques agrégées sur une fenêtre glissante : "
                "total d'événements, répartition par sévérité, top catégories, "
                "volume horaire par source. Utiliser pour les questions de synthèse "
                "('résume la journée', 'quelles sont les tendances', etc.)."
            ),
            parameters={
                "type": "OBJECT",
                "properties": {
                    "hours": {
                        "type": "INTEGER",
                        "description": "Taille de la fenêtre en heures (défaut 24, max 168).",
                    },
                },
            },
        ),
        types.FunctionDeclaration(
            name="list_devices",
            description=(
                "Liste l'inventaire des équipements surveillés (IP, statut, "
                "nombre de logs, dernière activité). Utiliser pour les questions "
                "sur l'état des équipements ou leur activité."
            ),
            parameters={"type": "OBJECT", "properties": {}},
        ),
    ])
]


def _serialize_log(entry) -> dict:
    return {
        "timestamp": entry.timestamp.isoformat() if isinstance(entry.timestamp, datetime) else str(entry.timestamp),
        "source_type": entry.source_type,
        "source_device": entry.source_device,
        "severity": entry.severity,
        "event_type": entry.event_type,
        "src_ip": entry.src_ip,
        "dst_ip": entry.dst_ip,
        "user": entry.user,
        "message": entry.message,
    }


def _serialize_device(d) -> dict:
    return {
        "name": d.name,
        "ip": d.ip,
        "source_type": d.source_type,
        "status": getattr(d, "status", None),
        "logs_count": d.logs_count,
        "last_seen": d.last_seen.isoformat() if isinstance(d.last_seen, datetime) else str(d.last_seen),
    }


async def _exec_search_logs(args: dict, session: AsyncSession) -> Any:
    since = _parse_iso(args.get("since"))
    until = _parse_iso(args.get("until"))
    logs = await query_logs(
        session,
        source_type=args.get("source_type"),
        severity=args.get("severity"),
        q=args.get("q"),
        since=since,
        until=until,
        limit=min(int(args.get("limit", 20) or 20), 200),
    )
    return {"count": len(logs), "logs": [_serialize_log(l) for l in logs]}


async def _exec_get_stats_overview(args: dict, session: AsyncSession) -> Any:
    hours = min(int(args.get("hours", 24) or 24), 168)
    return await stats_overview(session, hours=hours)


async def _exec_list_devices(args: dict, session: AsyncSession) -> Any:
    devices = await list_devices(session)
    return {"count": len(devices), "devices": [_serialize_device(d) for d in devices]}


TOOL_EXECUTORS = {
    "search_logs": _exec_search_logs,
    "get_stats_overview": _exec_get_stats_overview,
    "list_devices": _exec_list_devices,
}


async def execute_tool(name: str, args: dict, session: AsyncSession) -> Any:
    executor = TOOL_EXECUTORS.get(name)
    if executor is None:
        return {"error": f"Outil inconnu: {name}"}
    try:
        return await executor(args, session)
    except Exception as e:  # noqa: BLE001 — on renvoie l'erreur au modèle plutôt que de planter la requête
        return {"error": str(e)}
