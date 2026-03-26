from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any
from app.services.livekit_token import create_participant_token

router = APIRouter(prefix="/voice", tags=["Voice Agent"])

class TokenRequest(BaseModel):
    participant_name: str

@router.post("/token")
def get_voice_token(request: TokenRequest):
    print(f"\n\n!!! TOKEN REQUEST RECEIVED for {request.participant_name} !!!\n\n")
    """
    Generate a secure token for the Next.js frontend to connect 
    to the LiveKit room and talk to the Voice Agent.
    """
    # Use a dynamic room name starting with 'call-' so it triggers the SAME dispatch rule as SIP phone calls
    import uuid
    room_name = f"call-custom-{uuid.uuid4().hex[:8]}" 
    print(f"\n\n!!! TOKEN REQUEST RECEIVED FOR ROOM: {room_name} !!!\n\n")
    import json
    metadata = json.dumps({"agent_name": "hospital-bot-local-v1"})
    
    try:
        token = create_participant_token(room_name, request.participant_name, metadata=metadata)
        return {
            "token": token,
            "room_name": room_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
