from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    source = Column(String)  # e.g., 'voice_call', 'website', 'property_inquiry'
    status = Column(String)  # e.g., 'new', 'contacted', 'qualified', 'converted'
    
    # Property preferences stored as JSON
    property_preferences = Column(JSON, default=dict)
    
    # Conversation history stored as JSON array
    conversation_history = Column(JSON, default=list)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_contact = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    property_views = relationship("PropertyView", back_populates="lead")
    inquiries = relationship("PropertyInquiry", back_populates="lead")
    
    # Lead scoring and qualification
    score = Column(Integer, default=0)  # 0-100 score based on various factors
    qualification_notes = Column(String)
    
    # Additional contact information
    address = Column(String)
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)
    
    # Communication preferences
    preferred_contact_method = Column(String)  # 'email', 'phone', 'sms'
    best_time_to_contact = Column(String)
    
    # Budget information
    min_budget = Column(Integer)
    max_budget = Column(Integer)
    
    # Timeline
    purchase_timeline = Column(String)  # 'immediate', '3_months', '6_months', etc.
    
    def to_dict(self):
        """Convert lead to dictionary format."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "source": self.source,
            "status": self.status,
            "property_preferences": self.property_preferences,
            "score": self.score,
            "created_at": self.created_at.isoformat(),
            "last_contact": self.last_contact.isoformat(),
            "purchase_timeline": self.purchase_timeline,
            "budget_range": f"${self.min_budget:,} - ${self.max_budget:,}" if self.min_budget and self.max_budget else None
        }
