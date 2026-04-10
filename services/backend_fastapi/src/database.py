# services/backend_fastapi/src/database.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os
from dotenv import load_dotenv

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://admin:secretpassword@localhost:5432/smart_camera_db"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    camera_id = Column(String)
    event_type = Column(String) # Ví dụ: "Intrusion", "Object Detected"
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)