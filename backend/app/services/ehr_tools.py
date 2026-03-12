import asyncio
import logging
from datetime import datetime
from livekit.agents import llm
from app.db.database import SessionLocal
from app.db.models import Patient, Provider, Appointment

logger = logging.getLogger("ehr-tools")

class EHRTools(llm.ToolContext):
    def __init__(self):
        super().__init__([])

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
