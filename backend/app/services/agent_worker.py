import asyncio
import logging
import os
import sys
import traceback
from dotenv import load_dotenv

# Add the 'backend' directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import anthropic, elevenlabs, silero, openai

from app.db.database import SessionLocal
from app.db.models import CallSession, Transcript
from app.services.ehr_tools import EHRTools

load_dotenv()
logger = logging.getLogger("voice-agent")

async def entrypoint(ctx: JobContext):
    logger.info(f"Connecting to room: {ctx.room.name}")
    try:
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        
        # 1. Create Dashboard Session (Non-Blocking)
        session_id = None
        try:
            def _create():
                with SessionLocal() as db:
                    s = CallSession(call_id=ctx.room.name, status="active", intent="unknown")
                    db.add(s)
                    db.commit()
                    db.refresh(s)
                    return s.id
            session_id = await asyncio.to_thread(_create)
            logger.info(f"Dashboard session active: {session_id}")
        except Exception as e:
            logger.error(f"Dashboard Session Error: {e}")

        def log_transcript(role: str, content: str):
            if not session_id: return
            def _log():
                try:
                    with SessionLocal() as db:
                        t = Transcript(session_id=session_id, role=role, content=content)
                        db.add(t)
                        db.commit()
                except Exception as ex:
                    logger.error(f"Transcript Error: {ex}")
            asyncio.create_task(asyncio.to_thread(_log))

        agent = Agent(
            instructions=(
                "CRITICAL: YOU MUST SPEAK ONLY IN ENGLISH. "
                "You are an empathetic, efficient, and professional hospital front desk receptionist. "
                "Your job is to answer incoming calls and help patients with appointments and FAQs."
                "\n\nWORKFLOW:\n"
                "1. If booking/rescheduling, ask for their phone number first.\n"
                "2. Use tools to find available doctors or hospital information.\n"
                "3. If in distress, escalate to a human.\n"
                "\n\nSTRICT RULES:\n"
                "- SPEAK ONLY ENGLISH. DO NOT SWITCH TO SPANISH.\n"
                "- Keep responses brief and natural.\n"
                "- Never expose database IDs."
            ),
            tools=llm.find_function_tools(EHRTools(session_id=session_id)),
            stt=elevenlabs.STT(),
            llm=anthropic.LLM(model="claude-3-haiku-20240307"),
            tts=elevenlabs.TTS(voice_id="pXr6cxbX2mUgTLejYHov"),
            vad=silero.VAD.load(),
        )

        session = AgentSession()
        
        @session.on("user_input_transcribed")
        def _on_user(event):
            if event.is_final:
                log_transcript("user", event.transcript)

        @session.on("conversation_item_added")
        def _on_item(event):
            if event.item.role == "assistant" and hasattr(event.item, "content"):
                log_transcript("agent", event.item.content)

        await session.start(agent=agent, room=ctx.room)
        
        greeting = "Hello, this is the hospital front desk. How can I help you today?"
        await session.say(greeting, allow_interruptions=True)
        log_transcript("agent", greeting)

    except Exception as e:

        logger.error(f"AGENT CRASH: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    print("\n\nAGENT WORKER STARTING\n\n")
    logger.info("Starting Finalized Agent Worker...")
    
    ws_url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            ws_url=ws_url,
            api_key=api_key,
            api_secret=api_secret,
            agent_name="hospital-bot-local-v1",
        )
    )


