from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadUpdate
from app.utils.email import send_lead_notification


class LeadManager:
    def __init__(self, db: Session):
        self.db = db

    async def create_lead(self, lead_data: LeadCreate) -> Lead:
        """Create a new lead from conversation or property inquiry."""
        lead = Lead(
            name=lead_data.name,
            email=lead_data.email,
            phone=lead_data.phone,
            source=lead_data.source,
            status="new",
            property_preferences=lead_data.property_preferences,
            conversation_history=lead_data.conversation_history,
            last_contact=datetime.utcnow()
        )
        self.db.add(lead)
        await self.db.commit()
        await self.db.refresh(lead)

        # Send notification to agents
        await send_lead_notification(lead)
        

        
        return lead

    async def update_lead_status(self, lead_id: int, status: str) -> Lead:
        """Update lead status and trigger necessary actions."""
        lead = await self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        lead.status = status
        lead.last_updated = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(lead)
        

        
        return lead

    async def get_lead_by_phone(self, phone: str) -> Optional[Lead]:
        """Retrieve lead by phone number."""
        return await self.db.query(Lead).filter(Lead.phone == phone).first()

    async def get_lead_by_email(self, email: str) -> Optional[Lead]:
        """Retrieve lead by email."""
        return await self.db.query(Lead).filter(Lead.email == email).first()

    async def update_conversation_history(self, lead_id: int, new_messages: List[Dict]) -> Lead:
        """Update the conversation history for a lead."""
        lead = await self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")
        
        lead.conversation_history.extend(new_messages)
        lead.last_contact = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(lead)
        
        return lead

    async def get_leads_requiring_followup(self) -> List[Lead]:
        """Get leads that need follow-up based on last contact time."""
        threshold = datetime.utcnow() - timedelta(days=3)  # 3 days without contact
        return await self.db.query(Lead).filter(
            Lead.status.in_(['new', 'in_progress']),
            Lead.last_contact < threshold
        ).all()

    async def score_lead(self, lead_id: int) -> float:
        """Calculate lead score based on various factors."""
        lead = await self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            raise ValueError(f"Lead {lead_id} not found")

        score = 0.0
        
        # Score based on completeness of information
        if lead.email:
            score += 0.2
        if lead.phone:
            score += 0.2
        if lead.property_preferences:
            score += 0.3
            
        # Score based on engagement
        if lead.conversation_history:
            score += min(len(lead.conversation_history) * 0.1, 0.3)
            
        return min(score, 1.0)  # Normalize to 0-1 range
