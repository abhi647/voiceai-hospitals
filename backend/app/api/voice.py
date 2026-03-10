from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any
from app.services.livekit_token import create_participant_token

router = APIRouter(prefix="/voice", tags=["Voice Agent"])

class TokenRequest(BaseModel):
    participant_name: str

@router.post("/token")
def get_voice_token(request: TokenRequest):
    """
    Generate a secure token for the Next.js frontend to connect 
    to the LiveKit room and talk to the Voice Agent.
    """
    # Use a dynamic room name so every connection gets a fresh room and triggers a new agent dispatch
    import uuid
    room_name = f"hospital-reception-{uuid.uuid4().hex[:8]}" 
    
    try:
        token = create_participant_token(room_name, request.participant_name)
        return {
            "token": token,
            "room_name": room_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
