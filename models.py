from sqlalchemy import Column, Integer, String, Date, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base

class EventAttendance(Base):
    __tablename__ = 'event_attendance'
    id = Column(Integer, primary_key=True, index=True)
    contact_id = Column(Integer, ForeignKey('contacts.id'))
    event_id = Column(Integer, ForeignKey('events.id'))
    companions = Column(Integer, default=0)

    contact = relationship("Contact", back_populates="attendances")
    event = relationship("Event", back_populates="attendances")

class Contact(Base):
    __tablename__ = 'contacts'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone = Column(String, index=True)
    extra_info = Column(JSON, default={})

    attendances = relationship("EventAttendance", back_populates="contact")

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    date = Column(Date)

    attendances = relationship("EventAttendance", back_populates="event")

class BloodDonor(Base):
    __tablename__ = 'blood_donors'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    phone = Column(String, index=True)
    blood_type = Column(String, index=True)
    date_of_birth = Column(Date)
