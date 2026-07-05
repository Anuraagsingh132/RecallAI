import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from core.database import AsyncSessionLocal
from models.base import User, Conversation, Message
from api.dependencies import get_current_user
from services.retrieval import retrieve_context
from services.generation import generate_answer, AnswerResponse
from pydantic import BaseModel

router = APIRouter(prefix="/conversations", tags=["chat"])

class MessageRequest(BaseModel):
    content: str

@router.post("")
async def create_conversation(current_user: User = Depends(get_current_user)):
    """Initialize a new empty conversation."""
    conv_id = uuid.uuid4()
    async with AsyncSessionLocal() as session:
        conv = Conversation(id=conv_id, user_id=current_user.id)
        session.add(conv)
        await session.commit()
    return {"conversation_id": str(conv_id)}

@router.get("")
async def list_conversations(current_user: User = Depends(get_current_user)):
    """List all conversations for a user."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Conversation)
            .where(Conversation.user_id == current_user.id)
            .order_by(Conversation.created_at.desc())
        )
        return result.scalars().all()

@router.get("/{conversation_id}/messages")
async def get_messages(conversation_id: uuid.UUID, current_user: User = Depends(get_current_user)):
    """Retrieves chat history."""
    async with AsyncSessionLocal() as session:
        # Verify ownership
        result = await session.execute(
            select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        result = await session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        return result.scalars().all()

@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: uuid.UUID, 
    request: MessageRequest,
    current_user: User = Depends(get_current_user)
) -> AnswerResponse:
    """The core RAG endpoint. Accepts user message, runs retrieval, generates AI response, saves both."""
    async with AsyncSessionLocal() as session:
        # 1. Verify ownership
        result = await session.execute(
            select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        # 2. Save User Message
        user_msg_id = uuid.uuid4()
        user_msg = Message(id=user_msg_id, conversation_id=conversation_id, role="user", content=request.content)
        session.add(user_msg)
        await session.commit()
        
        # 3. Fetch History (up to 20 previous messages as per board decision)
        # We fetch top 20, but we need them in chronological order, so we fetch DESC limit 20 then reverse.
        # Actually since we just inserted the user message, we can fetch 21 and reverse, then drop the last one, or just exclude user_msg_id.
        result = await session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .where(Message.id != user_msg_id)
            .order_by(Message.created_at.desc())
            .limit(20)
        )
        recent_messages = result.scalars().all()
        # Reverse to chronological
        chat_history_models = list(reversed(recent_messages))
        chat_history = [{"role": m.role, "content": m.content} for m in chat_history_models]
        
    # 4. Retrieve Context
    context = await retrieve_context(request.content, current_user.id)
    
    # 5. Generate Answer
    ai_response = await generate_answer(request.content, context, chat_history)
    
    # 6. Save AI Message
    async with AsyncSessionLocal() as session:
        ai_msg_id = uuid.uuid4()
        # If no answer found, we might want to still save the exact text returned or a default string
        final_answer = ai_response.answer if ai_response.answer_found else "I cannot find the answer in the provided documents."
        ai_msg = Message(id=ai_msg_id, conversation_id=conversation_id, role="model", content=final_answer)
        session.add(ai_msg)
        await session.commit()
        
    return ai_response
