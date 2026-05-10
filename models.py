from sqlalchemy import Column, Integer, String, Date, ForeignKey, JSON, DateTime, Table
from sqlalchemy.orm import relationship
from database import Base
import datetime

contact_tags = Table(
    'contact_tags',
    Base.metadata,
    Column('contact_id', Integer, ForeignKey('contacts.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    color = Column(String, default="primary") # e.g. primary, success, danger, warning, info
    
    contacts = relationship("Contact", secondary=contact_tags, back_populates="tags")

class Admin(Base):
    __tablename__ = 'admins'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="subadmin") # "superadmin" or "subadmin"
    
    activities = relationship("ActivityLog", back_populates="admin")

class ActivityLog(Base):
    __tablename__ = 'activity_logs'
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    admin_id = Column(Integer, ForeignKey('admins.id'))
    action = Column(String) # e.g. "CREATE", "UPDATE", "DELETE"
    target = Column(String) # e.g. "Contact", "Event", "Admin"
    details = Column(String) # Additional context
    
    admin = relationship("Admin", back_populates="activities")

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
    tags = relationship("Tag", secondary=contact_tags, back_populates="contacts")

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
