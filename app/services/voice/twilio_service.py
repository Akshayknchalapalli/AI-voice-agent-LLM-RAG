from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from fastapi import HTTPException
from app.core.config import get_settings

settings = get_settings()

class TwilioService:
    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    def generate_voice_response(self, text: str) -> str:
        """Generate TwiML response for voice calls"""
        response = VoiceResponse()
        response.say(text)
        return str(response)

    async def start_outbound_call(self, to_number: str, from_number: str, webhook_url: str):
        """Initiate an outbound call"""
        try:
            call = self.client.calls.create(
                to=to_number,
                from_=from_number,
                url=webhook_url,
                status_callback=f"{webhook_url}/status",
                status_callback_event=['initiated', 'ringing', 'answered', 'completed']
            )
            return call.sid
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initiate call: {str(e)}")

    async def get_call_status(self, call_sid: str):
        """Get status of a call"""
        try:
            call = self.client.calls(call_sid).fetch()
            return {
                "status": call.status,
                "duration": call.duration,
                "direction": call.direction,
                "from": call.from_,
                "to": call.to,
                "timestamp": call.start_time
            }
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Call not found: {str(e)}")

twilio_service = TwilioService()
