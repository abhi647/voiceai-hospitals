from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api.ehr import router as ehr_router
from app.api.voice import router as voice_router
from app.api.dashboard import router as dashboard_router

# Load environment variables (Azure OpenAI, LiveKit, ElevenLabs)
load_dotenv()

app = FastAPI(
    title="Voice AI Platform API",
    description="API for the Voice AI Platform for Hospitals",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Voice AI Platform backend"}

@app.get("/")
async def root():
    return {"message": "Welcome to the Voice AI Platform API"}

app.include_router(ehr_router)
app.include_router(voice_router)
app.include_router(dashboard_router)
