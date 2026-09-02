import logging
from datetime import datetime, timezone

from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.tools import TOOLS, execute_tool
from app.config import settings

logger = logging.getLogger("argus.agent")


def _system_instruction() -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"""Tu es ARGUS, l'assistant IA d'une plateforme SOC (Security \
Operations Center) qui centralise les journaux de FortiGate, ESET PROTECT, Synology, \
Windows et des équipements réseau.

Date et heure actuelles (UTC) : {now}

Règles :
- Réponds toujours en français, de façon claire et concise, adaptée à un administrateur système.
- Utilise systématiquement les outils disponibles (search_logs, get_stats_overview, \
list_devices) pour appuyer tes réponses sur des données réelles — ne devine jamais un \
chiffre ou un événement.
- Pour toute question relative à une période ("aujourd'hui", "cette semaine", "dernières \
24h"), calcule toi-même le paramètre `since` (et `until` si pertinent) de search_logs en \
ISO 8601 à partir de la date/heure actuelles ci-dessus — ne suppose jamais que l'absence \
de filtre de date donne "aujourd'hui" par défaut.
- Si une question porte sur une IP précise, utilise le paramètre `q` de search_logs.
- Structure les réponses avec des puces quand tu listes plusieurs événements.
- Si aucune donnée ne correspond à la question, dis-le clairement plutôt que d'inventer.
- Reste concis : privilégie une réponse synthétique de quelques phrases ou une courte liste, \
pas un rapport complet, sauf si on te le demande explicitement.
"""


MAX_TOOL_ITERATIONS = 5


def _history_to_contents(history: list[dict]) -> list[types.Content]:
    contents = []
    for turn in history:
        role = "model" if turn.get("role") == "agent" else "user"
        text = turn.get("text", "")
        if text:
            contents.append(types.Content(role=role, parts=[types.Part(text=text)]))
    return contents


def _extract_text(response: types.GenerateContentResponse) -> str:
    if not response.candidates:
        return ""
    parts = response.candidates[0].content.parts or []
    return "".join(p.text for p in parts if getattr(p, "text", None))


async def chat(message: str, history: list[dict], session: AsyncSession) -> dict:
    if not settings.gemini_api_key:
        return {
            "reply": (
                "L'agent IA n'est pas configuré : ajoute ta clé Gemini gratuite "
                "(https://aistudio.google.com/apikey) dans GEMINI_API_KEY côté backend, "
                "puis redémarre le service."
            ),
            "tool_calls": [],
        }

    client = genai.Client(api_key=settings.gemini_api_key)
    config = types.GenerateContentConfig(system_instruction=_system_instruction(), tools=TOOLS)

    contents = _history_to_contents(history)
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

    tool_calls_made: list[dict] = []

    for _ in range(MAX_TOOL_ITERATIONS):
        try:
            response = await client.aio.models.generate_content(
                model=settings.gemini_model, contents=contents, config=config,
            )
        except Exception as e:  # noqa: BLE001
            logger.exception("Gemini call failed")
            return {"reply": f"Erreur lors de l'appel à l'agent IA : {e}", "tool_calls": tool_calls_made}

        calls = response.function_calls or []
        if not calls:
            return {"reply": _extract_text(response) or "Je n'ai pas de réponse à te proposer.", "tool_calls": tool_calls_made}

        # Répond à tous les appels de fonction demandés dans ce tour
        contents.append(response.candidates[0].content)
        for call in calls:
            args = dict(call.args or {})
            tool_calls_made.append({"name": call.name, "args": args})
            result = await execute_tool(call.name, args, session)
            contents.append(types.Content(
                role="user",
                parts=[types.Part.from_function_response(name=call.name, response={"result": result})],
            ))

    return {
        "reply": "L'analyse nécessite trop d'étapes intermédiaires — reformule ta question de façon plus ciblée.",
        "tool_calls": tool_calls_made,
    }
