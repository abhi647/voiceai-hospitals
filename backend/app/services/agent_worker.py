import asyncio
import logging
import os
import sys
import traceback
from dotenv import load_dotenv

# Add the 'backend' directory to sys.path so 'app' module can be found in subprocesses
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

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

        from app.services.ehr_tools import EHRTools
        ehr_tools = EHRTools()

        # Create the Agent using ElevenLabs for both STT and TTS, and Claude for LLM
        agent = Agent(
            instructions=(
                "You are an empathetic, efficient, and professional hospital front desk receptionist. "
                "Your job is to answer incoming calls, understand the patient's requests, and use your tools to help them. "
                "\n\nCORE WORKFLOW:\n"
                "1. If the user wants to book, reschedule, or check an appointment, FIRST ask for their phone number to look up their Patient ID using get_patient_by_phone.\n"
                "2. If they want to book an appointment with a specific specialty, use find_available_doctors to find a Provider ID.\n"
                "3. Use the book_appointment or check_appointments tools using the precise IDs you gathered.\n"
                "\n\nRULES:\n"
                "- Keep responses conversational, brief, and spoken naturally (e.g., say 'Dr. Smith' instead of 'Doctor 1').\n"
                "- Never expose raw database IDs to the user; use their real names.\n"
                "- If the user expresses a life-threatening medical emergency or extreme distress, immediately instruct them to call 911 or go to the nearest emergency room, and state that you are escalating the call to a human."
            ),
            tools=llm.find_function_tools(ehr_tools),
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
