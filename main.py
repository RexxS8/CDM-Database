from fastapi import FastAPI, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
import json
from datetime import date
import random
import os

import models
from database import engine, SessionLocal, Base, get_db

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="super-secret-key-cdm")

# Create tables if they do not exist
models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    
    if db.query(models.Admin).count() == 0:
        admin = models.Admin(username="ADMINCDM", password="CDM123", role="superadmin")
        db.add(admin)
        db.commit()

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


import time

def get_current_admin(request: Request, db: Session = Depends(get_db)):
    admin_id = request.session.get("admin_id")
    if not admin_id:
        return None
    return db.query(models.Admin).filter(models.Admin.id == admin_id).first()

def require_admin(request: Request, db: Session = Depends(get_db)):
    admin = get_current_admin(request, db)
    if not admin:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
        
    # Handle 5-minute session timeout for ALL users (superadmin and subadmin)
    last_activity = request.session.get("last_activity")
    current_time = time.time()
    if last_activity and current_time - last_activity > 300: # 5 minutes = 300 seconds
        request.session.clear()
        # Redirect to login with timeout message if possible, or just login
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login?timeout=1"})
    
    request.session["last_activity"] = current_time
        
    return admin

def log_activity(db: Session, admin_id: int, action: str, target: str, details: str = ""):
    log = models.ActivityLog(admin_id=admin_id, action=action, target=target, details=details)
    db.add(log)
    db.commit()

@app.get("/login", response_class=HTMLResponse)
def read_login(request: Request):
    timeout = request.query_params.get("timeout")
    error = "Sesi Anda telah berakhir karena tidak ada aktivitas selama 5 menit. Silakan login kembali." if timeout else None
    return templates.TemplateResponse(request=request, name="login.html", context={"error": error})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    admin = db.query(models.Admin).filter(models.Admin.username == username, models.Admin.password == password).first()
    if admin:
        request.session["admin_id"] = admin.id
        request.session["role"] = admin.role
        request.session["last_activity"] = time.time()
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html", context={"error": "Invalid username or password"})

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)

@app.get("/superadmin", response_class=HTMLResponse)
def read_superadmin(request: Request, db: Session = Depends(get_db), admin: models.Admin = Depends(require_admin)):
    if admin.role != "superadmin":
        return RedirectResponse(url="/", status_code=303)
    admins = db.query(models.Admin).all()
    logs = db.query(models.ActivityLog).order_by(models.ActivityLog.timestamp.desc()).limit(100).all()
    
    # Quick Statistics
    stats = {
        "total_contacts": db.query(models.Contact).count(),
        "total_events": db.query(models.Event).count(),
        "total_tags": db.query(models.Tag).count(),
        "total_donors": db.query(models.BloodDonor).count()
    }
    
    return templates.TemplateResponse(request=request, name="superadmin.html", context={"admins": admins, "logs": logs, "stats": stats, "admin": admin})

@app.post("/superadmin/add-admin")
def add_admin(
    request: Request,
    username: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(require_admin)
):
    if admin.role != "superadmin":
        return RedirectResponse(url="/", status_code=303)
    new_admin = models.Admin(username=username, password=password, role="subadmin")
    db.add(new_admin)
    db.commit()
    log_activity(db, admin.id, "CREATE", "Admin", f"Created subadmin: {username}")
    return RedirectResponse(url="/superadmin", status_code=303)

@app.post("/superadmin/delete-admin/{target_id}")
def delete_admin(
    request: Request,
    target_id: int,
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(require_admin)
):
    if admin.role != "superadmin":
        return RedirectResponse(url="/", status_code=303)
    if admin.id == target_id:
        return RedirectResponse(url="/superadmin", status_code=303)
    target_admin = db.query(models.Admin).filter(models.Admin.id == target_id).first()
    if target_admin:
        db.delete(target_admin)
        db.commit()
        log_activity(db, admin.id, "DELETE", "Admin", f"Deleted subadmin: {target_admin.username}")
    return RedirectResponse(url="/superadmin", status_code=303)

@app.post("/tags/add")
def add_tag(
    request: Request,
    name: str = Form(...),
    color: str = Form("primary"),
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(require_admin)
):
    if admin.role != "superadmin":
        return RedirectResponse(url="/", status_code=303)
    tag = models.Tag(name=name, color=color)
    db.add(tag)
    db.commit()
    log_activity(db, admin.id, "CREATE", "Tag", f"Created tag: {name}")
    referer = request.headers.get("referer", "/")
    return RedirectResponse(url=referer, status_code=303)

@app.post("/tags/{tag_id}/delete")
def delete_tag(
    request: Request,
    tag_id: int,
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(require_admin)
):
    if admin.role != "superadmin":
        return RedirectResponse(url="/", status_code=303)
    tag = db.query(models.Tag).filter(models.Tag.id == tag_id).first()
    if tag:
        db.delete(tag)
        db.commit()
        log_activity(db, admin.id, "DELETE", "Tag", f"Deleted tag: {tag.name}")
    referer = request.headers.get("referer", "/")
    return RedirectResponse(url=referer, status_code=303)



@app.get("/", response_class=HTMLResponse)
def read_contacts(request: Request, db: Session = Depends(get_db), admin: models.Admin = Depends(require_admin)):
    contacts = db.query(models.Contact).order_by(func.lower(models.Contact.name).asc()).all()
    events = db.query(models.Event).all()
    all_tags = db.query(models.Tag).order_by(models.Tag.name.asc()).all()
    return templates.TemplateResponse(request=request, name="index.html", context={"contacts": contacts, "events": events, "all_tags": all_tags, "admin": admin})

@app.post("/contact/add")
def add_contact(
    name: str = Form(...),
    phone: str = Form(...),
    extra_keys: list[str] = Form([]),
    extra_values: list[str] = Form([]),
    tag_ids: list[str] = Form([]),
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(require_admin)
):
    extra_info = {}
    for k, v in zip(extra_keys, extra_values):
        if k and v:
            extra_info[k] = v
            
    contact = models.Contact(name=name, phone=phone, extra_info=extra_info)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    
    # Assign tags after contact is created so it has an ID
    if tag_ids:
        final_tags = []
        for t_id in tag_ids:
            if t_id.isdigit():
                tag = db.query(models.Tag).filter(models.Tag.id == int(t_id)).first()
                if tag:
                    final_tags.append(tag)
            else:
                # Dynamic new tag creation
                existing_tag = db.query(models.Tag).filter(models.Tag.name == t_id).first()
                if existing_tag:
                    final_tags.append(existing_tag)
                else:
                    new_tag = models.Tag(name=t_id, color="primary")
                    db.add(new_tag)
                    db.commit()
                    db.refresh(new_tag)
                    final_tags.append(new_tag)
                    log_activity(db, admin.id, "CREATE", "Tag", f"Dynamically created tag: {t_id}")
        
        contact.tags.extend(final_tags)
        db.commit()

    log_activity(db, admin.id, "CREATE", "Contact", f"Added new contact: '{name}'")
    return RedirectResponse(url="/", status_code=303)

@app.post("/contact/quick-attend")
def quick_attend_event(
    contact_id: int = Form(...),
    event_id: int = Form(...),
    companions: int = Form(0),
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(require_admin)
):
    # Check if already attending
    existing = db.query(models.EventAttendance).filter_by(contact_id=contact_id, event_id=event_id).first()
    if existing:
        existing.companions = companions
    else:
        attendance = models.EventAttendance(contact_id=contact_id, event_id=event_id, companions=companions)
        db.add(attendance)
    db.commit()
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    log_activity(db, admin.id, "CREATE", "EventAttendance", f"Registered '{contact.name}' for event '{event.name}' ({companions} companions)")
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
    tag_ids: list[str] = Form([]),
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(require_admin)
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
            
        # Update tags
        contact.tags.clear()
        if tag_ids:
            final_tags = []
            for t_id in tag_ids:
                if t_id.isdigit():
                    tag = db.query(models.Tag).filter(models.Tag.id == int(t_id)).first()
                    if tag:
                        final_tags.append(tag)
                else:
                    existing_tag = db.query(models.Tag).filter(models.Tag.name == t_id).first()
                    if existing_tag:
                        final_tags.append(existing_tag)
                    else:
                        new_tag = models.Tag(name=t_id, color="primary")
                        db.add(new_tag)
                        db.commit()
                        db.refresh(new_tag)
                        final_tags.append(new_tag)
                        log_activity(db, admin.id, "CREATE", "Tag", f"Dynamically created tag: {t_id}")
            contact.tags.extend(final_tags)
            
        db.commit()
        log_activity(db, admin.id, "UPDATE", "Contact", f"Updated profile details for contact '{contact.name}'")
    referer = request.headers.get("referer", "/")
    return RedirectResponse(url=referer, status_code=303)

@app.post("/contact/{contact_id}/delete")
def delete_contact(contact_id: int, db: Session = Depends(get_db), admin: models.Admin = Depends(require_admin)):
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if contact:
        db.query(models.EventAttendance).filter(models.EventAttendance.contact_id == contact_id).delete()
        db.delete(contact)
        db.commit()
        log_activity(db, admin.id, "DELETE", "Contact", f"Deleted contact '{contact.name}' and their attendance history")
    return RedirectResponse(url="/", status_code=303)

@app.get("/contact/{contact_id}", response_class=HTMLResponse)
def read_contact_detail(request: Request, contact_id: int, db: Session = Depends(get_db), admin: models.Admin = Depends(require_admin)):
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    events = db.query(models.Event).all()
    all_tags = db.query(models.Tag).order_by(models.Tag.name.asc()).all()
    return templates.TemplateResponse(request=request, name="contact_detail.html", context={"contact": contact, "events": events, "all_tags": all_tags, "admin": admin})

@app.post("/contact/{contact_id}/attend")
def contact_attend_event(
    contact_id: int,
    event_id: int = Form(...),
    companions: int = Form(0),
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(require_admin)
):
    existing = db.query(models.EventAttendance).filter_by(contact_id=contact_id, event_id=event_id).first()
    if existing:
        existing.companions = companions
    else:
        attendance = models.EventAttendance(contact_id=contact_id, event_id=event_id, companions=companions)
        db.add(attendance)
    db.commit()
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    log_activity(db, admin.id, "CREATE", "EventAttendance", f"Registered '{contact.name}' for event '{event.name}' ({companions} companions)")    
    return RedirectResponse(url=f"/contact/{contact_id}", status_code=303)

@app.get("/events", response_class=HTMLResponse)
def read_events(request: Request, search: str | None = None, db: Session = Depends(get_db), admin: models.Admin = Depends(require_admin)):
    query = db.query(models.Event)
    if search:
        query = query.filter(models.Event.name.ilike(f"%{search}%"))
    events = query.order_by(models.Event.date.desc()).all()
    
    events_data = []
    for event in events:
        total = sum(1 + att.companions for att in event.attendances)
        events_data.append({"event": event, "total": total})
    return templates.TemplateResponse(request=request, name="events.html", context={"events_data": events_data, "search_term": search or "", "admin": admin})

@app.post("/events/add")
def add_event(name: str = Form(...), event_date: date = Form(...), db: Session = Depends(get_db), admin: models.Admin = Depends(require_admin)):
    event = models.Event(name=name, date=event_date)
    db.add(event)
    db.commit()
    log_activity(db, admin.id, "CREATE", "Event", f"Created new event: '{name}'")
    return RedirectResponse(url="/events", status_code=303)

@app.get("/events/{event_id}", response_class=HTMLResponse)
def read_event_detail(request: Request, event_id: int, search: str | None = None, db: Session = Depends(get_db), admin: models.Admin = Depends(require_admin)):
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    
    # Calculate overall total based on all attendances
    all_attendances = db.query(models.EventAttendance).filter(models.EventAttendance.event_id == event_id).all()
    total_attendees = sum(1 + att.companions for att in all_attendances)

    query = db.query(models.EventAttendance).join(models.Contact).filter(models.EventAttendance.event_id == event_id)
    if search:
        query = query.filter(or_(models.Contact.name.ilike(f"%{search}%"), models.Contact.phone.ilike(f"%{search}%")))
    
    attendances = query.order_by(func.lower(models.Contact.name).asc()).all()
    all_contacts = db.query(models.Contact).order_by(func.lower(models.Contact.name).asc()).all()
    
    return templates.TemplateResponse(request=request, name="event_detail.html", context={"event": event, "attendances": attendances, "total_attendees": total_attendees, "all_contacts": all_contacts, "search_term": search or "", "admin": admin})

@app.post("/events/{event_id}/attend")
def event_detail_add_contact(
    event_id: int,
    contact_id: int = Form(...),
    companions: int = Form(0),
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(require_admin)
):
    existing = db.query(models.EventAttendance).filter_by(contact_id=contact_id, event_id=event_id).first()
    if existing:
        existing.companions = companions
    else:
        attendance = models.EventAttendance(contact_id=contact_id, event_id=event_id, companions=companions)
        db.add(attendance)
    db.commit()
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    log_activity(db, admin.id, "CREATE", "EventAttendance", f"Registered '{contact.name}' for event '{event.name}' ({companions} companions)")
    return RedirectResponse(url=f"/events/{event_id}", status_code=303)

@app.post("/events/{event_id}/attend/new")
def event_detail_add_new_contact(
    event_id: int,
    name: str = Form(...),
    phone: str = Form(...),
    companions: int = Form(0),
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(require_admin)
):
    # 1. Create Contact
    contact = models.Contact(name=name, phone=phone)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    log_activity(db, admin.id, "CREATE", "Contact", f"Added contact (via event): {name}")
    
    # 2. Add Attendance
    attendance = models.EventAttendance(contact_id=contact.id, event_id=event_id, companions=companions)
    db.add(attendance)
    db.commit()
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    log_activity(db, admin.id, "CREATE", "EventAttendance", f"Registered '{contact.name}' for event '{event.name}' ({companions} companions)")
    return RedirectResponse(url=f"/events/{event_id}", status_code=303)

@app.get("/blood-donors", response_class=HTMLResponse)
def read_blood_donors(request: Request, db: Session = Depends(get_db), admin: models.Admin = Depends(require_admin)):
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

    return templates.TemplateResponse(request=request, name="blood_donors.html", context={"donors_data": donors_with_age, "admin": admin})

@app.post("/blood-donors/add")
def add_blood_donor(
    name: str = Form(...),
    phone: str = Form(...),
    blood_type: str = Form(...),
    date_of_birth: date = Form(...),
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(require_admin)
):
    donor = models.BloodDonor(name=name, phone=phone, blood_type=blood_type, date_of_birth=date_of_birth)
    db.add(donor)
    db.commit()
    log_activity(db, admin.id, "CREATE", "BloodDonor", f"Added blood donor: '{name}'")
    return RedirectResponse(url="/blood-donors", status_code=303)

@app.post("/blood-donors/{donor_id}/edit")
def edit_blood_donor(
    donor_id: int,
    name: str = Form(...),
    phone: str = Form(...),
    blood_type: str = Form(...),
    date_of_birth: date = Form(...),
    db: Session = Depends(get_db),
    admin: models.Admin = Depends(require_admin)
):
    donor = db.query(models.BloodDonor).filter(models.BloodDonor.id == donor_id).first()
    if donor:
        donor.name = name
        donor.phone = phone
        donor.blood_type = blood_type
        donor.date_of_birth = date_of_birth
        db.commit()
        log_activity(db, admin.id, "UPDATE", "BloodDonor", f"Updated medical details for blood donor '{donor.name}'")
    return RedirectResponse(url="/blood-donors", status_code=303)

@app.post("/blood-donors/{donor_id}/delete")
def delete_blood_donor(donor_id: int, db: Session = Depends(get_db), admin: models.Admin = Depends(require_admin)):
    donor = db.query(models.BloodDonor).filter(models.BloodDonor.id == donor_id).first()
    if donor:
        db.delete(donor)
        db.commit()
        log_activity(db, admin.id, "DELETE", "BloodDonor", f"Deleted blood donor '{donor.name}'")
    return RedirectResponse(url="/blood-donors", status_code=303)
