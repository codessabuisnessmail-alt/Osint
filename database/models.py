from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

Base = declarative_base()

class OSINTResult(Base):
    __tablename__ = 'osint_results'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(500), nullable=False)
    platform = Column(String(50), nullable=False)
    username = Column(String(100))
    profile_data = Column(JSON)
    confidence_score = Column(Float, nullable=False)
    status_code = Column(Integer)
    error_message = Column(Text)
    is_bot_detected = Column(Boolean, default=False)
    detection_method = Column(String(100))
    html_hash = Column(String(64))
    screenshot_hash = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'url': self.url,
            'platform': self.platform,
            'username': self.username,
            'profile_data': self.profile_data,
            'confidence_score': self.confidence_score,
            'status_code': self.status_code,
            'error_message': self.error_message,
            'is_bot_detected': self.is_bot_detected,
            'detection_method': self.detection_method,
            'html_hash': self.html_hash,
            'screenshot_hash': self.screenshot_hash,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Snapshot(Base):
    __tablename__ = 'snapshots'
    
    id = Column(Integer, primary_key=True)
    osint_result_id = Column(Integer, nullable=False)
    html_content = Column(Text)
    screenshot_path = Column(String(500))
    html_hash = Column(String(64), unique=True)
    screenshot_hash = Column(String(64))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'osint_result_id': self.osint_result_id,
            'html_content': self.html_content[:1000] + '...' if len(self.html_content or '') > 1000 else self.html_content,
            'screenshot_path': self.screenshot_path,
            'html_hash': self.html_hash,
            'screenshot_hash': self.screenshot_hash,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ScrapingTask(Base):
    __tablename__ = 'scraping_tasks'
    
    id = Column(Integer, primary_key=True)
    task_id = Column(String(100), unique=True, nullable=False)
    url = Column(String(500), nullable=False)
    platform = Column(String(50), nullable=False)
    status = Column(String(20), default='pending')  # pending, running, completed, failed
    priority = Column(Integer, default=1)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'url': self.url,
            'platform': self.platform,
            'status': self.status,
            'priority': self.priority,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

# Database connection
def get_database_url():
    from config import Config
    return f"postgresql://{Config.POSTGRES_USER}:{Config.POSTGRES_PASSWORD}@{Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}/{Config.POSTGRES_DB}"

def create_tables():
    engine = create_engine(get_database_url())
    Base.metadata.create_all(engine)
    return engine

def get_session():
    engine = create_engine(get_database_url())
    Session = sessionmaker(bind=engine)
    return Session()
