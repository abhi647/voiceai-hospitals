import datetime
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine
from app.db.models import Base, Patient, Provider, Appointment

# Create tables
Base.metadata.create_all(bind=engine)

def seed_db():
    db = SessionLocal()
    
    # Check if we already have data
    if db.query(Patient).first():
        print("Database already seeded!")
        return
        
    print("Seeding database...")
    
    # Providers
    p1 = Provider(first_name="Alice", last_name="Smith", specialty="Cardiology", department="Heart Center")
    p2 = Provider(first_name="Bob", last_name="Jones", specialty="General Practice", department="Primary Care")
    db.add_all([p1, p2])
    db.commit()
    
    # Patients
    pat1 = Patient(first_name="John", last_name="Doe", phone_number="+15551234567", email="john@example.com")
    pat2 = Patient(first_name="Jane", last_name="Roe", phone_number="+15559876543", email="jane@example.com")
    db.add_all([pat1, pat2])
    db.commit()
    
    # Appointments
    today = datetime.datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0)
    a1 = Appointment(patient_id=pat1.id, provider_id=p1.id, appointment_time=today + datetime.timedelta(days=1), status="scheduled", reason="Routine Checkup")
    a2 = Appointment(patient_id=pat2.id, provider_id=p2.id, appointment_time=today + datetime.timedelta(days=2), status="scheduled", reason="Follow-up")
    db.add_all([a1, a2])
    db.commit()
    
    db.close()
    print("Seeding complete.")

if __name__ == "__main__":
    seed_db()
