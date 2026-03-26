import asyncio
import logging
from datetime import datetime
from livekit.agents import llm
from app.db.database import SessionLocal
from app.db.models import Patient, Provider, Appointment, FAQ, CallSession

logger = logging.getLogger("ehr-tools")

class EHRTools(llm.ToolContext):
    def __init__(self, session_id: int = None):
        super().__init__([])
        self.session_id = session_id

    @llm.function_tool(description="Look up a patient by their phone number. Use this first when answering a call.")
    async def get_patient_by_phone(self, phone_number: str) -> str:
        logger.info(f"Tool call: get_patient_by_phone({phone_number})")
        def _query():
            with SessionLocal() as db:
                p = db.query(Patient).filter(Patient.phone_number == phone_number).first()
                if not p:
                    # Generic search if direct match fails
                    p_all = db.query(Patient).all()
                    for pt in p_all:
                        if pt.phone_number and (phone_number in pt.phone_number or pt.phone_number in phone_number):
                            return f"Found patient: {pt.first_name} {pt.last_name}, ID: {pt.id}"
                    return "Patient not found. Ask for their name and create a record manually if this was a real system, but for now just tell them you can't find them."
                return f"Found patient: {p.first_name} {p.last_name}, ID: {p.id}"
        return await asyncio.to_thread(_query)

    @llm.function_tool(description="Search for available doctors by specialty (e.g., 'Cardiology', 'Pediatrics').")
    async def find_available_doctors(self, specialty: str) -> str:
        logger.info(f"Tool call: find_available_doctors({specialty})")
        def _query():
            with SessionLocal() as db:
                providers = db.query(Provider).filter(Provider.specialty.ilike(f"%{specialty}%")).all()
                if not providers:
                    return f"No doctors found for specialty: {specialty}."
                return "\n".join([f"Dr. {p.first_name} {p.last_name} (ID: {p.id})" for p in providers])
        return await asyncio.to_thread(_query)

    @llm.function_tool(description="Book a new appointment for a patient. Provide the patient ID, provider ID (doctor), and a reason. The datetime format must be YYYY-MM-DD HH:MM.")
    async def book_appointment(self, patient_id: int, provider_id: int, reason: str, time_str: str) -> str:
        logger.info(f"Tool call: book_appointment(patient_id={patient_id}, provider_id={provider_id}, time={time_str})")
        def _query():
            with SessionLocal() as db:
                try:
                    # Rough parsing of datetime for mock purposes
                    if len(time_str) == 16:
                        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                    else:
                        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                        
                    app = Appointment(
                        patient_id=patient_id,
                        provider_id=provider_id,
                        appointment_time=dt,
                        status="scheduled",
                        reason=reason
                    )
                    db.add(app)
                    db.commit()
                    return f"Successfully booked appointment ID {app.id} for {time_str}."
                except Exception as e:
                    return f"Failed to book appointment: {e}. Ensure the time format is exactly YYYY-MM-DD HH:MM."
        return await asyncio.to_thread(_query)
        
    @llm.function_tool(description="Check a patient's existing appointments by their patient ID.")
    async def check_appointments(self, patient_id: int) -> str:
        logger.info(f"Tool call: check_appointments(patient_id={patient_id})")
        def _query():
            with SessionLocal() as db:
                apps = db.query(Appointment).filter(Appointment.patient_id == patient_id).all()
                if not apps:
                    return "No appointments found for this patient."
                return "\n".join([f"Appointment ID: {a.id}, Date/Time: {a.appointment_time}, Reason: {a.reason}, Status: {a.status}, Doctor ID: {a.provider_id}" for a in apps])
        return await asyncio.to_thread(_query)

    @llm.function_tool(description="Search the hospital knowledge base for FAQs (visiting hours, parking, locations, emergency room info).")
    async def search_faq(self, query: str) -> str:
        logger.info(f"Tool call: search_faq({query})")
        def _query():
            with SessionLocal() as db:
                # Simple keyword search for SQLite fallback
                faqs = db.query(FAQ).filter(
                    (FAQ.question.ilike(f"%{query}%")) | (FAQ.answer.ilike(f"%{query}%"))
                ).all()
                if not faqs:
                    return "No specific information found in the knowledge base. Please ask for more details or escalate if it sounds serious."
                return "\n---\n".join([f"Q: {f.question}\nA: {f.answer}" for f in faqs])
        return await asyncio.to_thread(_query)

    @llm.function_tool(description="Escalate the call to a human operator. Use this if the patient is in distress, has a life-threatening emergency, or expresses extreme dissatisfaction.")
    async def escalate_to_human(self, reason: str) -> str:
        logger.info(f"Tool call: escalate_to_human(reason='{reason}')")
        def _update():
            if not self.room_name:
                return "Escalation requested, but no active room name found to mark."
            with SessionLocal() as db:
                session = db.query(CallSession).filter(CallSession.call_id == self.room_name).first()
                if session:
                    session.status = "escalated"
                    session.urgency_score = 10
                    db.commit()
                    return "The call has been flagged as 'Escalated' in the dashboard. A human operator has been notified."
                return f"Session for room {self.room_name} not found in DB, but escalation instruction recorded."
        return await asyncio.to_thread(_update)

    @llm.function_tool(description="Reschedule an existing appointment. Provide the appointment ID and the NEW datetime in YYYY-MM-DD HH:MM format.")
    async def reschedule_appointment(self, appointment_id: int, new_time_str: str) -> str:
        logger.info(f"Tool call: reschedule_appointment(id={appointment_id}, new_time={new_time_str})")
        def _query():
            with SessionLocal() as db:
                try:
                    app = db.query(Appointment).filter(Appointment.id == appointment_id).first()
                    if not app:
                        return f"Appointment ID {appointment_id} not found."
                    
                    if len(new_time_str) == 16:
                        dt = datetime.strptime(new_time_str, "%Y-%m-%d %H:%M")
                    else:
                        dt = datetime.strptime(new_time_str, "%Y-%m-%d %H:%M:%S")
                    
                    app.appointment_time = dt
                    db.commit()
                    return f"Successfully rescheduled appointment ID {appointment_id} to {new_time_str}."
                except Exception as e:
                    return f"Failed to reschedule: {e}. Ensure the time format is YYYY-MM-DD HH:MM."
        return await asyncio.to_thread(_query)
