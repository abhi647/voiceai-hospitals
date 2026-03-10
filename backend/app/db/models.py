import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.database import Base

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    dob = Column(DateTime)
    phone_number = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    appointments = relationship("Appointment", back_populates="patient")

class Provider(Base):
    __tablename__ = "providers"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    specialty = Column(String)
    department = Column(String)
    
    appointments = relationship("Appointment", back_populates="provider")

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    provider_id = Column(Integer, ForeignKey("providers.id"))
    appointment_time = Column(DateTime)
    status = Column(String) # 'scheduled', 'completed', 'canceled'
    reason = Column(String)
    
    patient = relationship("Patient", back_populates="appointments")
    provider = relationship("Provider", back_populates="appointments")

class CallSession(Base):
    __tablename__ = "call_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    call_id = Column(String, unique=True, index=True)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    caller_number = Column(String)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    status = Column(String) # 'active', 'completed', 'escalated'
    urgency_score = Column(Integer, default=0)
    intent = Column(String, nullable=True)
    
class Transcript(Base):
    __tablename__ = "transcripts"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("call_sessions.id"))
    role = Column(String) # 'user', 'agent'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
class FAQ(Base):
    __tablename__ = "faqs"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String)
    answer = Column(Text)
    # Embedding stored as a JSON string for SQLite (or we can use ChromaDB/in-memory array later)
    embedding_json = Column(Text, nullable=True)
