import aiohttp
from typing import Dict, Any, Optional
from app.core.config import settings

class CRMIntegration:
    def __init__(self):
        self.base_url = settings.CRM_API_URL
        self.api_key = settings.CRM_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def create_or_update_lead(self, lead_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create or update a lead in the CRM system."""
        try:
            async with aiohttp.ClientSession() as session:
                # Check if lead exists
                search_url = f"{self.base_url}/leads/search"
                search_params = {
                    "email": lead_data.get("email"),
                    "phone": lead_data.get("phone")
                }
                
                async with session.get(search_url, headers=self.headers, params=search_params) as resp:
                    existing_lead = await resp.json()
                
                if existing_lead:
                    # Update existing lead
                    lead_id = existing_lead["id"]
                    update_url = f"{self.base_url}/leads/{lead_id}"
                    async with session.put(update_url, headers=self.headers, json=lead_data) as resp:
                        return await resp.json()
                else:
                    # Create new lead
                    create_url = f"{self.base_url}/leads"
                    async with session.post(create_url, headers=self.headers, json=lead_data) as resp:
                        return await resp.json()
                        
        except Exception as e:
            print(f"Error syncing with CRM: {str(e)}")
            return None

    async def create_task(self, lead_id: str, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a follow-up task in the CRM system."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/tasks"
                task_data["lead_id"] = lead_id
                
                async with session.post(url, headers=self.headers, json=task_data) as resp:
                    return await resp.json()
                    
        except Exception as e:
            print(f"Error creating CRM task: {str(e)}")
            return None

    async def update_lead_status(self, lead_id: str, status: str) -> Optional[Dict[str, Any]]:
        """Update lead status in the CRM system."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/leads/{lead_id}"
                data = {"status": status}
                
                async with session.patch(url, headers=self.headers, json=data) as resp:
                    return await resp.json()
                    
        except Exception as e:
            print(f"Error updating lead status in CRM: {str(e)}")
            return None

async def sync_lead_with_crm(lead) -> Optional[Dict[str, Any]]:
    """Sync lead data with CRM system."""
    crm = CRMIntegration()
    
    lead_data = {
        "name": lead.name,
        "email": lead.email,
        "phone": lead.phone,
        "source": lead.source,
        "status": lead.status,
        "property_preferences": lead.property_preferences,
        "score": lead.score,
        "budget": {
            "min": lead.min_budget,
            "max": lead.max_budget
        },
        "timeline": lead.purchase_timeline,
        "last_contact": lead.last_contact.isoformat(),
        "notes": lead.qualification_notes
    }
    
    return await crm.create_or_update_lead(lead_data)
