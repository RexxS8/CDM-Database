import re

with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# We only want to modify endpoints after read_contacts
split_idx = content.find('@app.get("/", response_class=HTMLResponse)')

top_part = content[:split_idx]
bottom_part = content[split_idx:]

# Define replacements for bottom part
replacements = [
    (
        r'def read_contacts\(request: Request, db: Session = Depends\(get_db\)\):',
        r'def read_contacts(request: Request, db: Session = Depends(get_db), admin: models.Admin = Depends(require_admin)):'
    ),
    (
        r'return templates\.TemplateResponse\(request=request, name="index\.html", context=\{"contacts": contacts, "events": events\}\)',
        r'return templates.TemplateResponse(request=request, name="index.html", context={"contacts": contacts, "events": events, "admin": admin})'
    ),
    (
        r'def add_contact\(\n    name: str = Form\(\.\.\.\),\n    phone: str = Form\(\.\.\.\),\n    extra_keys: list\[str\] = Form\(\[\]\),\n    extra_values: list\[str\] = Form\(\[\]\),\n    db: Session = Depends\(get_db\)\n\):',
        r'def add_contact(\n    name: str = Form(...),\n    phone: str = Form(...),\n    extra_keys: list[str] = Form([]),\n    extra_values: list[str] = Form([]),\n    db: Session = Depends(get_db),\n    admin: models.Admin = Depends(require_admin)\n):'
    ),
    (
        r'    db\.add\(contact\)\n    db\.commit\(\)',
        r'    db.add(contact)\n    db.commit()\n    log_activity(db, admin.id, "CREATE", "Contact", f"Added contact: {name}")'
    ),
    (
        r'def quick_attend_event\(\n    contact_id: int = Form\(\.\.\.\),\n    event_id: int = Form\(\.\.\.\),\n    companions: int = Form\(0\),\n    db: Session = Depends\(get_db\)\n\):',
        r'def quick_attend_event(\n    contact_id: int = Form(...),\n    event_id: int = Form(...),\n    companions: int = Form(0),\n    db: Session = Depends(get_db),\n    admin: models.Admin = Depends(require_admin)\n):'
    ),
    (
        r'        db\.add\(attendance\)\n    db\.commit\(\)',
        r'        db.add(attendance)\n    db.commit()\n    log_activity(db, admin.id, "CREATE", "EventAttendance", f"Contact {contact_id} to Event {event_id}")'
    ),
    (
        r'def edit_contact\(\n    request: Request,\n    contact_id: int,\n    name: str = Form\(\.\.\.\),\n    phone: str = Form\(\.\.\.\),\n    extra_keys: list\[str\] = Form\(\[\]\),\n    extra_values: list\[str\] = Form\(\[\]\),\n    update_extra: bool = Form\(False\),\n    db: Session = Depends\(get_db\)\n\):',
        r'def edit_contact(\n    request: Request,\n    contact_id: int,\n    name: str = Form(...),\n    phone: str = Form(...),\n    extra_keys: list[str] = Form([]),\n    extra_values: list[str] = Form([]),\n    update_extra: bool = Form(False),\n    db: Session = Depends(get_db),\n    admin: models.Admin = Depends(require_admin)\n):'
    ),
    (
        r'        db\.commit\(\)',
        r'        db.commit()\n        log_activity(db, admin.id, "UPDATE", "Contact", f"Edited contact: {contact_id}")'
    ),
    (
        r'def delete_contact\(contact_id: int, db: Session = Depends\(get_db\)\):',
        r'def delete_contact(contact_id: int, db: Session = Depends(get_db), admin: models.Admin = Depends(require_admin)):'
    ),
    (
        r'        db\.delete\(contact\)\n        db\.commit\(\)',
        r'        db.delete(contact)\n        db.commit()\n        log_activity(db, admin.id, "DELETE", "Contact", f"Deleted contact: {contact_id}")'
    ),
    (
        r'def read_contact_detail\(request: Request, contact_id: int, db: Session = Depends\(get_db\)\):',
        r'def read_contact_detail(request: Request, contact_id: int, db: Session = Depends(get_db), admin: models.Admin = Depends(require_admin)):'
    ),
    (
        r'return templates\.TemplateResponse\(request=request, name="contact_detail\.html", context=\{"contact": contact, "events": events\}\)',
        r'return templates.TemplateResponse(request=request, name="contact_detail.html", context={"contact": contact, "events": events, "admin": admin})'
    ),
    (
        r'def contact_attend_event\(\n    contact_id: int,\n    event_id: int = Form\(\.\.\.\),\n    companions: int = Form\(0\),\n    db: Session = Depends\(get_db\)\n\):',
        r'def contact_attend_event(\n    contact_id: int,\n    event_id: int = Form(...),\n    companions: int = Form(0),\n    db: Session = Depends(get_db),\n    admin: models.Admin = Depends(require_admin)\n):'
    ),
    (
        r'def read_events\(request: Request, search: str \| None = None, db: Session = Depends\(get_db\)\):',
        r'def read_events(request: Request, search: str | None = None, db: Session = Depends(get_db), admin: models.Admin = Depends(require_admin)):'
    ),
    (
        r'return templates\.TemplateResponse\(request=request, name="events\.html", context=\{"events_data": events_data, "search_term": search or ""\}\)',
        r'return templates.TemplateResponse(request=request, name="events.html", context={"events_data": events_data, "search_term": search or "", "admin": admin})'
    ),
    (
        r'def add_event\(name: str = Form\(\.\.\.\), event_date: date = Form\(\.\.\.\), db: Session = Depends\(get_db\)\):',
        r'def add_event(name: str = Form(...), event_date: date = Form(...), db: Session = Depends(get_db), admin: models.Admin = Depends(require_admin)):'
    ),
    (
        r'    db\.add\(event\)\n    db\.commit\(\)',
        r'    db.add(event)\n    db.commit()\n    log_activity(db, admin.id, "CREATE", "Event", f"Added event: {name}")'
    ),
    (
        r'def read_event_detail\(request: Request, event_id: int, search: str \| None = None, db: Session = Depends\(get_db\)\):',
        r'def read_event_detail(request: Request, event_id: int, search: str | None = None, db: Session = Depends(get_db), admin: models.Admin = Depends(require_admin)):'
    ),
    (
        r'return templates\.TemplateResponse\(request=request, name="event_detail\.html", context=\{"event": event, "attendances": attendances, "total_attendees": total_attendees, "all_contacts": all_contacts, "search_term": search or ""\}\)',
        r'return templates.TemplateResponse(request=request, name="event_detail.html", context={"event": event, "attendances": attendances, "total_attendees": total_attendees, "all_contacts": all_contacts, "search_term": search or "", "admin": admin})'
    ),
    (
        r'def event_detail_add_contact\(\n    event_id: int,\n    contact_id: int = Form\(\.\.\.\),\n    companions: int = Form\(0\),\n    db: Session = Depends\(get_db\)\n\):',
        r'def event_detail_add_contact(\n    event_id: int,\n    contact_id: int = Form(...),\n    companions: int = Form(0),\n    db: Session = Depends(get_db),\n    admin: models.Admin = Depends(require_admin)\n):'
    ),
    (
        r'def event_detail_add_new_contact\(\n    event_id: int,\n    name: str = Form\(\.\.\.\),\n    phone: str = Form\(\.\.\.\),\n    companions: int = Form\(0\),\n    db: Session = Depends\(get_db\)\n\):',
        r'def event_detail_add_new_contact(\n    event_id: int,\n    name: str = Form(...),\n    phone: str = Form(...),\n    companions: int = Form(0),\n    db: Session = Depends(get_db),\n    admin: models.Admin = Depends(require_admin)\n):'
    ),
    (
        r'    attendance = models\.EventAttendance\(contact_id=contact\.id, event_id=event_id, companions=companions\)\n    db\.add\(attendance\)\n    db\.commit\(\)',
        r'    attendance = models.EventAttendance(contact_id=contact.id, event_id=event_id, companions=companions)\n    db.add(attendance)\n    db.commit()\n    log_activity(db, admin.id, "CREATE", "EventAttendance", f"New Contact {name} to Event {event_id}")'
    ),
    (
        r'def read_blood_donors\(request: Request, db: Session = Depends\(get_db\)\):',
        r'def read_blood_donors(request: Request, db: Session = Depends(get_db), admin: models.Admin = Depends(require_admin)):'
    ),
    (
        r'return templates\.TemplateResponse\(request=request, name="blood_donors\.html", context=\{"donors_data": donors_with_age\}\)',
        r'return templates.TemplateResponse(request=request, name="blood_donors.html", context={"donors_data": donors_with_age, "admin": admin})'
    ),
    (
        r'def add_blood_donor\(\n    name: str = Form\(\.\.\.\),\n    phone: str = Form\(\.\.\.\),\n    blood_type: str = Form\(\.\.\.\),\n    date_of_birth: date = Form\(\.\.\.\),\n    db: Session = Depends\(get_db\)\n\):',
        r'def add_blood_donor(\n    name: str = Form(...),\n    phone: str = Form(...),\n    blood_type: str = Form(...),\n    date_of_birth: date = Form(...),\n    db: Session = Depends(get_db),\n    admin: models.Admin = Depends(require_admin)\n):'
    ),
    (
        r'    db\.add\(donor\)\n    db\.commit\(\)',
        r'    db.add(donor)\n    db.commit()\n    log_activity(db, admin.id, "CREATE", "BloodDonor", f"Added donor: {name}")'
    ),
    (
        r'def edit_blood_donor\(\n    donor_id: int,\n    name: str = Form\(\.\.\.\),\n    phone: str = Form\(\.\.\.\),\n    blood_type: str = Form\(\.\.\.\),\n    date_of_birth: date = Form\(\.\.\.\),\n    db: Session = Depends\(get_db\)\n\):',
        r'def edit_blood_donor(\n    donor_id: int,\n    name: str = Form(...),\n    phone: str = Form(...),\n    blood_type: str = Form(...),\n    date_of_birth: date = Form(...),\n    db: Session = Depends(get_db),\n    admin: models.Admin = Depends(require_admin)\n):'
    ),
    (
        r'        donor\.date_of_birth = date_of_birth\n        db\.commit\(\)',
        r'        donor.date_of_birth = date_of_birth\n        db.commit()\n        log_activity(db, admin.id, "UPDATE", "BloodDonor", f"Edited donor: {donor_id}")'
    ),
    (
        r'def delete_blood_donor\(donor_id: int, db: Session = Depends\(get_db\)\):',
        r'def delete_blood_donor(donor_id: int, db: Session = Depends(get_db), admin: models.Admin = Depends(require_admin)):'
    ),
    (
        r'        db\.delete\(donor\)\n        db\.commit\(\)',
        r'        db.delete(donor)\n        db.commit()\n        log_activity(db, admin.id, "DELETE", "BloodDonor", f"Deleted donor: {donor_id}")'
    )
]

for old, new in replacements:
    bottom_part = re.sub(old, new, bottom_part, count=1)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(top_part + bottom_part)
