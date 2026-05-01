from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
import json
from datetime import date
import random
import os

import models
from database import engine, SessionLocal, Base, get_db

app = FastAPI()

# Create tables if they do not exist
models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    # Check if we already have data
    if db.query(models.Contact).count() == 0:
        # Generate 3 Events
        events_data = [
            models.Event(name="Vesak 2024", date=date(2024, 5, 23)),
            models.Event(name="Meditation Retreat 2025", date=date(2025, 8, 15)),
            models.Event(name="Kathina 2024", date=date(2024, 11, 10))
        ]
        db.add_all(events_data)
        db.commit()

        # Generate 10 Contacts
        names = ["Budi Santoso", "Siti Aminah", "Rina Gunawan", "Agus Wijaya", "Dewi Lestari", 
                 "Hendrik", "Linda", "Susanto", "Yulia", "Eko Prasetyo"]
        
        contacts = []
        for i in range(10):
            extra = {}
            if i % 2 == 0:
                extra["address"] = f"Jalan Merdeka No {i+1}, Jakarta"
            if i % 3 == 0:
                extra["job"] = "Student" if i < 5 else "Entrepreneur"
                
            contact = models.Contact(
                name=names[i],
                phone=f"0812345678{i:02d}",
                extra_info=extra
            )
            contacts.append(contact)
        
        db.add_all(contacts)
        db.commit()

        # Assign random contacts to events
        all_events = db.query(models.Event).all()
        all_contacts = db.query(models.Contact).all()
        
        for event in all_events:
            # Assign 3 to 6 random contacts to each event
            attendees = random.sample(all_contacts, random.randint(3, 6))
            for attendee in attendees:
                attendance = models.EventAttendance(
                    contact_id=attendee.id,
                    event_id=event.id,
                    companions=random.choice([0, 1, 2, 5])
                )
                db.add(attendance)
        db.commit()

        # Generate 5 Blood Donors
        donor_names = ["Arif", "Hendra", "Nia", "Maya", "Rizki"]
        blood_types = ["A", "B", "O", "AB", "O"]
        dobs = [date(1990, 5, 12), date(1985, 11, 30), date(2000, 1, 15), date(1995, 7, 22), date(1982, 3, 5)]
        
        donors = []
        for i in range(5):
            donor = models.BloodDonor(
                name=donor_names[i],
                phone=f"0856789012{i:02d}",
                blood_type=blood_types[i],
                date_of_birth=dobs[i]
            )
            donors.append(donor)
            
        db.add_all(donors)
        db.commit()
    
    db.close()


@app.get("/", response_class=HTMLResponse)
def read_contacts(request: Request, db: Session = Depends(get_db)):
    contacts = db.query(models.Contact).order_by(func.lower(models.Contact.name).asc()).all()
    events = db.query(models.Event).all()
    return templates.TemplateResponse(request=request, name="index.html", context={"contacts": contacts, "events": events})

@app.post("/contact/add")
def add_contact(
    name: str = Form(...),
    phone: str = Form(...),
    extra_keys: list[str] = Form([]),
    extra_values: list[str] = Form([]),
    db: Session = Depends(get_db)
):
    extra_info = {}
    for k, v in zip(extra_keys, extra_values):
        if k and v:
            extra_info[k] = v
            
    contact = models.Contact(name=name, phone=phone, extra_info=extra_info)
    db.add(contact)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/contact/quick-attend")
def quick_attend_event(
    contact_id: int = Form(...),
    event_id: int = Form(...),
    companions: int = Form(0),
    db: Session = Depends(get_db)
):
    # Check if already attending
    existing = db.query(models.EventAttendance).filter_by(contact_id=contact_id, event_id=event_id).first()
    if existing:
        existing.companions = companions
    else:
        attendance = models.EventAttendance(contact_id=contact_id, event_id=event_id, companions=companions)
        db.add(attendance)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/contact/{contact_id}/edit")
def edit_contact(
    request: Request,
    contact_id: int,
    name: str = Form(...),
    phone: str = Form(...),
    extra_keys: list[str] = Form([]),
    extra_values: list[str] = Form([]),
    update_extra: bool = Form(False),
    db: Session = Depends(get_db)
):
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if contact:
        contact.name = name
        contact.phone = phone
        
        if update_extra:
            extra_info = {}
            for k, v in zip(extra_keys, extra_values):
                if k and v:
                    extra_info[k] = v
            contact.extra_info = extra_info
            
        db.commit()
    referer = request.headers.get("referer", "/")
    return RedirectResponse(url=referer, status_code=303)

@app.post("/contact/{contact_id}/delete")
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if contact:
        db.query(models.EventAttendance).filter(models.EventAttendance.contact_id == contact_id).delete()
        db.delete(contact)
        db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/contact/{contact_id}", response_class=HTMLResponse)
def read_contact_detail(request: Request, contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    events = db.query(models.Event).all()
    return templates.TemplateResponse(request=request, name="contact_detail.html", context={"contact": contact, "events": events})

@app.post("/contact/{contact_id}/attend")
def contact_attend_event(
    contact_id: int,
    event_id: int = Form(...),
    companions: int = Form(0),
    db: Session = Depends(get_db)
):
    existing = db.query(models.EventAttendance).filter_by(contact_id=contact_id, event_id=event_id).first()
    if existing:
        existing.companions = companions
    else:
        attendance = models.EventAttendance(contact_id=contact_id, event_id=event_id, companions=companions)
        db.add(attendance)
    db.commit()
        
    return RedirectResponse(url=f"/contact/{contact_id}", status_code=303)

@app.get("/events", response_class=HTMLResponse)
def read_events(request: Request, search: str | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Event)
    if search:
        query = query.filter(models.Event.name.ilike(f"%{search}%"))
    events = query.order_by(models.Event.date.desc()).all()
    
    events_data = []
    for event in events:
        total = sum(1 + att.companions for att in event.attendances)
        events_data.append({"event": event, "total": total})
    return templates.TemplateResponse(request=request, name="events.html", context={"events_data": events_data, "search_term": search or ""})

@app.post("/events/add")
def add_event(name: str = Form(...), event_date: date = Form(...), db: Session = Depends(get_db)):
    event = models.Event(name=name, date=event_date)
    db.add(event)
    db.commit()
    return RedirectResponse(url="/events", status_code=303)

@app.get("/events/{event_id}", response_class=HTMLResponse)
def read_event_detail(request: Request, event_id: int, search: str | None = None, db: Session = Depends(get_db)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    
    # Calculate overall total based on all attendances
    all_attendances = db.query(models.EventAttendance).filter(models.EventAttendance.event_id == event_id).all()
    total_attendees = sum(1 + att.companions for att in all_attendances)

    query = db.query(models.EventAttendance).join(models.Contact).filter(models.EventAttendance.event_id == event_id)
    if search:
        query = query.filter(or_(models.Contact.name.ilike(f"%{search}%"), models.Contact.phone.ilike(f"%{search}%")))
    
    attendances = query.order_by(func.lower(models.Contact.name).asc()).all()
    all_contacts = db.query(models.Contact).order_by(func.lower(models.Contact.name).asc()).all()
    
    return templates.TemplateResponse(request=request, name="event_detail.html", context={"event": event, "attendances": attendances, "total_attendees": total_attendees, "all_contacts": all_contacts, "search_term": search or ""})

@app.post("/events/{event_id}/attend")
def event_detail_add_contact(
    event_id: int,
    contact_id: int = Form(...),
    companions: int = Form(0),
    db: Session = Depends(get_db)
):
    existing = db.query(models.EventAttendance).filter_by(contact_id=contact_id, event_id=event_id).first()
    if existing:
        existing.companions = companions
    else:
        attendance = models.EventAttendance(contact_id=contact_id, event_id=event_id, companions=companions)
        db.add(attendance)
    db.commit()
    return RedirectResponse(url=f"/events/{event_id}", status_code=303)

@app.post("/events/{event_id}/attend/new")
def event_detail_add_new_contact(
    event_id: int,
    name: str = Form(...),
    phone: str = Form(...),
    companions: int = Form(0),
    db: Session = Depends(get_db)
):
    # 1. Create Contact
    contact = models.Contact(name=name, phone=phone)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    
    # 2. Add Attendance
    attendance = models.EventAttendance(contact_id=contact.id, event_id=event_id, companions=companions)
    db.add(attendance)
    db.commit()
    return RedirectResponse(url=f"/events/{event_id}", status_code=303)

@app.get("/blood-donors", response_class=HTMLResponse)
def read_blood_donors(request: Request, db: Session = Depends(get_db)):
    donors = db.query(models.BloodDonor).order_by(func.lower(models.BloodDonor.name).asc()).all()
    
    # Calculate age for each donor
    today = date.today()
    donors_with_age = []
    for donor in donors:
        if donor.date_of_birth:
            age = today.year - donor.date_of_birth.year - ((today.month, today.day) < (donor.date_of_birth.month, donor.date_of_birth.day))
        else:
            age = None
        donors_with_age.append({"donor": donor, "age": age})

    return templates.TemplateResponse(request=request, name="blood_donors.html", context={"donors_data": donors_with_age})

@app.post("/blood-donors/add")
def add_blood_donor(
    name: str = Form(...),
    phone: str = Form(...),
    blood_type: str = Form(...),
    date_of_birth: date = Form(...),
    db: Session = Depends(get_db)
):
    donor = models.BloodDonor(name=name, phone=phone, blood_type=blood_type, date_of_birth=date_of_birth)
    db.add(donor)
    db.commit()
    return RedirectResponse(url="/blood-donors", status_code=303)

@app.post("/blood-donors/{donor_id}/edit")
def edit_blood_donor(
    donor_id: int,
    name: str = Form(...),
    phone: str = Form(...),
    blood_type: str = Form(...),
    date_of_birth: date = Form(...),
    db: Session = Depends(get_db)
):
    donor = db.query(models.BloodDonor).filter(models.BloodDonor.id == donor_id).first()
    if donor:
        donor.name = name
        donor.phone = phone
        donor.blood_type = blood_type
        donor.date_of_birth = date_of_birth
        db.commit()
    return RedirectResponse(url="/blood-donors", status_code=303)

@app.post("/blood-donors/{donor_id}/delete")
def delete_blood_donor(donor_id: int, db: Session = Depends(get_db)):
    donor = db.query(models.BloodDonor).filter(models.BloodDonor.id == donor_id).first()
    if donor:
        db.delete(donor)
        db.commit()
    return RedirectResponse(url="/blood-donors", status_code=303)
