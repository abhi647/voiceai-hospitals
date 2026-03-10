from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.db.database import get_db
from app.db.models import Patient, Provider, Appointment

router = APIRouter(prefix="/ehr", tags=["Mock EHR"])

@router.get("/patients", response_model=List[Dict[str, Any]])
def get_patients(db: Session = Depends(get_db)):
    patients = db.query(Patient).all()
    return [{"id": p.id, "first_name": p.first_name, "last_name": p.last_name, "phone": p.phone_number} for p in patients]

@router.get("/patients/phone/{phone_number}")
def get_patient_by_phone(phone_number: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.phone_number == phone_number).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"id": patient.id, "first_name": patient.first_name, "last_name": patient.last_name}

@router.get("/providers")
def get_providers(db: Session = Depends(get_db)):
    providers = db.query(Provider).all()
    return [{"id": p.id, "name": f"Dr. {p.first_name} {p.last_name}", "specialty": p.specialty} for p in providers]

@router.get("/appointments/patient/{patient_id}")
def get_patient_appointments(patient_id: int, db: Session = Depends(get_db)):
    appointments = db.query(Appointment).filter(Appointment.patient_id == patient_id).all()
    return [{
        "id": a.id,
        "time": a.appointment_time,
        "status": a.status,
        "reason": a.reason,
        "provider_id": a.provider_id
    } for a in appointments]
