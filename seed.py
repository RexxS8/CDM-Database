import random
from datetime import date, timedelta
from database import SessionLocal, engine
import models

def generate_random_date(start_age, end_age):
    today = date.today()
    start_date = today.replace(year=today.year - end_age)
    end_date = today.replace(year=today.year - start_age)
    days_between = (end_date - start_date).days
    random_number_of_days = random.randrange(days_between)
    return start_date + timedelta(days=random_number_of_days)

def seed_database():
    # Ensure tables are created
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Safety check to avoid duplicate seeding
    if db.query(models.Contact).count() >= 100:
        print("Database already has 100+ contacts. Skipping seeding to prevent duplicates.")
        db.close()
        return

    first_names = [
        "Budi", "Siti", "Agus", "Dewi", "Joko", "Rina", "Hendra", "Ayu", "Wahyu", "Lestari",
        "Eko", "Putri", "Rizki", "Indah", "Dwi", "Sri", "Andi", "Ratna", "Ahmad", "Nur"
    ]
    last_names = [
        "Santoso", "Wijaya", "Kusuma", "Setiawan", "Pratama", "Hidayat", "Saputra", "Wahyudi",
        "Gunawan", "Purnama", "Wibowo", "Nugroho", "Sari", "Lestari", "Susanto", "Putra", 
        "Utama", "Siregar", "Halim", "Suryono"
    ]
    jobs = ["Mahasiswa", "Wiraswasta", "Guru", "Karyawan Swasta", "PNS", "Pengusaha", "Freelancer", "Dokter", "Pedagang"]
    cities = ["Jakarta", "Surabaya", "Bandung", "Medan", "Semarang", "Makassar", "Palembang", "Tangerang", "Depok", "Bali"]

    print("Seeding Events...")
    if db.query(models.Event).count() < 3:
        events = [
            models.Event(name="Vesak Celebration 2024", date=date(2024, 5, 23)),
            models.Event(name="Meditation Retreat", date=date(2024, 8, 10)),
            models.Event(name="Kathina Ceremony 2024", date=date(2024, 11, 15))
        ]
        db.add_all(events)
        db.commit()

    all_events = db.query(models.Event).all()

    print("Seeding 100 Contacts and Event Attendances...")
    contacts = []
    for _ in range(100):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        phone = f"0812{random.randint(10000000, 99999999)}"
        
        extra_info = {
            "pekerjaan": random.choice(jobs),
            "alamat": f"Jln. {random.choice(first_names)} No. {random.randint(1, 100)}, {random.choice(cities)}"
        }
        
        contact = models.Contact(name=name, phone=phone, extra_info=extra_info)
        db.add(contact)
        contacts.append(contact)
        
    db.commit()

    # Assign each contact to random events
    for contact in contacts:
        # Assign to 1 or 2 random events to ensure good test coverage
        num_events = random.randint(1, 2)
        events_to_attend = random.sample(all_events, num_events)
        for event in events_to_attend:
            attendance = models.EventAttendance(
                contact_id=contact.id,
                event_id=event.id,
                companions=random.randint(0, 4)
            )
            db.add(attendance)
    db.commit()

    print("Seeding 100 Blood Donors...")
    blood_types = ["A", "B", "AB", "O"]
    for _ in range(100):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        phone = f"0856{random.randint(10000000, 99999999)}"
        b_type = random.choice(blood_types)
        dob = generate_random_date(18, 60)
        
        donor = models.BloodDonor(
            name=name,
            phone=phone,
            blood_type=b_type,
            date_of_birth=dob
        )
        db.add(donor)
        
    db.commit()
    db.close()
    print("Success: Database seeded with 100 Contacts and 100 Blood Donors!")

if __name__ == "__main__":
    seed_database()
