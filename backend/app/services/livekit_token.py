import os
from dotenv import load_dotenv

load_dotenv()

# We need a small function to securely generate a LiveKit token
# so the frontend Next.js app can connect to the room.
from livekit import api

def create_participant_token(room_name: str, participant_identity: str) -> str:
    """Generate a valid token for a participant to join a LiveKit room."""
    # The SDK automatically uses LIVEKIT_API_KEY and LIVEKIT_API_SECRET
    # from the environment variables.
    
    token = api.AccessToken() \
        .with_identity(participant_identity) \
        .with_name(participant_identity) \
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
        ))
        
    return token.to_jwt()
