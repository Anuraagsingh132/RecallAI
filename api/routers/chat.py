import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from core.database import AsyncSessionLocal
from models.base import User, Conversation, Message
from api.dependencies import get_current_user
from services.retrieval import retrieve_context
from services.generation import stream_answer
from pydantic import BaseModel

router = APIRouter(prefix="/conversations", tags=["chat"])

from typing import List, Optional

class MessageRequest(BaseModel):
    content: str
    document_ids: Optional[List[uuid.UUID]] = None

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

from fastapi.responses import StreamingResponse
import json

@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: uuid.UUID, 
    request: MessageRequest,
    current_user: User = Depends(get_current_user)
):
    """The core RAG endpoint with SSE streaming."""
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
        
        # 3. Fetch History (up to 20 previous messages)
        result = await session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .where(Message.id != user_msg_id)
            .order_by(Message.created_at.desc())
            .limit(20)
        )
        recent_messages = result.scalars().all()
        chat_history_models = list(reversed(recent_messages))
        chat_history = [{"role": m.role, "content": m.content} for m in chat_history_models]

    async def event_generator():
        from services.generation import stream_answer
        # 4. Retrieve Context
        context, sources = await retrieve_context(request.content, current_user.id, request.document_ids)
        
        # Yield sources instantly
        yield f"event: sources\ndata: {json.dumps(sources)}\n\n"
        
        # 5. Generate and yield tokens
        full_answer = ""
        async for token in stream_answer(request.content, context, chat_history):
            full_answer += token
            # Yield token event
            # We encode the token to JSON string to safely escape newlines and quotes
            yield f"event: token\ndata: {json.dumps(token)}\n\n"
            
        # 6. Save AI Message
        async with AsyncSessionLocal() as session:
            ai_msg_id = uuid.uuid4()
            ai_msg = Message(id=ai_msg_id, conversation_id=conversation_id, role="model", content=full_answer)
            session.add(ai_msg)
            await session.commit()
            
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

class ConversationUpdate(BaseModel):
    title: str

@router.patch("/{conversation_id}")
async def rename_conversation(
    conversation_id: uuid.UUID,
    request: ConversationUpdate,
    current_user: User = Depends(get_current_user)
):
    """Rename a conversation."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        )
        conv = result.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conv.title = request.title
        await session.commit()
    return {"message": "Conversation renamed successfully"}

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
):
    """Delete a conversation completely."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        )
        conv = result.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        await session.delete(conv)
        await session.commit()
    return {"message": "Conversation deleted successfully"}

@router.delete("/{conversation_id}/messages")
async def clear_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user)
):
    """Clear all messages in a conversation."""
    async with AsyncSessionLocal() as session:
        # Verify ownership
        result = await session.execute(
            select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == current_user.id)
        )
        conv = result.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Delete messages manually since cascading delete is for conversation delete
        # With SQLModel/SQLAlchemy async, we can execute a delete statement
        from sqlalchemy import delete
        await session.execute(delete(Message).where(Message.conversation_id == conversation_id))
        await session.commit()
    return {"message": "Conversation cleared successfully"}
