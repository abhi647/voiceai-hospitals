import asyncio
import logging
import os
import traceback
from dotenv import load_dotenv

from livekit.agents import AutoSubscribe, JobContext, JobRequest, WorkerOptions, cli, llm
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import anthropic, elevenlabs, silero

load_dotenv()
logger = logging.getLogger("voice-agent")
logging.basicConfig(level=logging.DEBUG)


async def entrypoint(ctx: JobContext):
    """Main entrypoint for the voice agent when a job starts."""
    
    try:
        # Connect to LiveKit room
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        logger.info(f"Agent connected to room: {ctx.room.name}")
        
        # Check API Keys
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        eleven_api_key = os.environ.get("ELEVEN_API_KEY", "")
        
        logger.info(f"Anthropic key present: {bool(anthropic_api_key)}")
        logger.info(f"ElevenLabs key present: {bool(eleven_api_key)}")

        if not anthropic_api_key:
            logger.error("Missing ANTHROPIC_API_KEY")
        if not eleven_api_key:
            logger.error("Missing ELEVEN_API_KEY")

        # Create the Agent using ElevenLabs for both STT and TTS, and Claude for LLM
        agent = Agent(
            instructions=(
                "You are a helpful and empathetic hospital front desk assistant. "
                "Your job is to answer incoming calls, understand the patient's needs, "
                "provide information, help them book or reschedule appointments, and escalate "
                "to human staff if there is an emergency or high distress. Keep responses brief and conversational."
            ),
            vad=silero.VAD.load(),
            stt=elevenlabs.STT(
                api_key=eleven_api_key,
            ),
            llm=anthropic.LLM(
                model="claude-3-haiku-20240307",
                api_key=anthropic_api_key,
            ),
            tts=elevenlabs.TTS(
                voice_id="pXr6cxbX2mUgTLejYHov",
                api_key=eleven_api_key,
            ),
        )
        logger.info("Agent created with ElevenLabs STT/TTS and Claude LLM.")

        # Create session and start the voice agent
        session = AgentSession()
        logger.info("AgentSession created, starting...")
        await session.start(agent=agent, room=ctx.room)
        logger.info("AgentSession started successfully!")
        
        # First message right after connection
        await session.say(
            "Hello, thank you for calling the hospital front desk. How can I help you today?",
            allow_interruptions=True,
        )
        logger.info("Initial greeting sent.")
        
    except Exception as e:
        logger.error(f"Error in entrypoint: {e}")
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            agent_name="voice-assistant",
            entrypoint_fnc=entrypoint,
        )
    )
