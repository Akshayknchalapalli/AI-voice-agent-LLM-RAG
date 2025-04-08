from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import get_settings
import urllib.parse

settings = get_settings()

# Create a dummy engine for SQLAlchemy model definitions
# We'll use Supabase's REST API for actual database operations
engine = create_engine('sqlite:///:memory:')

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
