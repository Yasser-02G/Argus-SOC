from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.service import chat as agent_chat
from app.database import get_session
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, session: AsyncSession = Depends(get_session)):
    result = await agent_chat(
        message=payload.message,
        history=[t.model_dump() for t in payload.history],
        session=session,
    )
    return ChatResponse(**result)
