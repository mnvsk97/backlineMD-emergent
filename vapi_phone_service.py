"""
Vapi Phone Call Service for BacklineMD
Handles phone calls to patients using Vapi AI
"""

import asyncio
import os
import logging
from typing import Dict, Any, Optional

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Vapi configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY")
VAPI_ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID")
VAPI_PHONE_NUMBER_ID = os.getenv("VAPI_PHONE_NUMBER_ID")
VAPI_API_URL = "https://api.vapi.ai/call"


class VapiPhoneService:
    """Service for making phone calls via Vapi REST API"""
    
    def __init__(self):
        self.api_key = VAPI_API_KEY
        self.assistant_id = VAPI_ASSISTANT_ID
        self.phone_number_id = VAPI_PHONE_NUMBER_ID
        self.api_url = VAPI_API_URL
    
    async def call_patient(
        self,
        patient_phone: str,
        patient_name: str,
        context: Optional[str] = None,
        appointment_slots: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Call a patient to schedule an appointment using Vapi REST API"""
        if not self.api_key:
            return {"success": False, "error": "VAPI_API_KEY not set"}
        
        if not self.phone_number_id:
            return {"success": False, "error": "VAPI_PHONE_NUMBER_ID not set"}
        
        try:
            first_name = patient_name.split()[0] if patient_name else "there"
            first_message = f"Hello {first_name}, this is calling from the fertility clinic. We've received your documents and would like to schedule your initial consultation. Are you available to discuss appointment times?"
            
            # Prepare appointment slots text
            slots_text = ", ".join(appointment_slots) if appointment_slots else "Please suggest times within clinic hours (Monday-Friday 9:00 AM - 4:00 PM)"
            
            # Prepare request payload matching the working pattern
            payload = {
                "phoneNumberId": self.phone_number_id,
                "customer": {
                    "number": patient_phone,
                    "name": patient_name,
                },
                "assistantId": self.assistant_id,
                "assistantOverrides": {
                    "variableValues": {
                        "patientName": first_name,
                        "context": context or "",
                        "appointmentSlots": slots_text,
                    },
                    "firstMessage": first_message,
                },
                "metadata": {
                    "patientName": patient_name,
                    "context": context or "",
                    "appointmentSlots": slots_text,
                    "source": "backlinemd",
                },
            }

            # Make API call using httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                
                if response.status_code not in [200, 201]:
                    error_text = response.text
                    logger.error(f"Vapi API error: {error_text}")
                    try:
                        error_detail = response.json()
                        error_msg = error_detail.get("message", error_text)
                    except:
                        error_msg = error_text
                    return {"success": False, "error": f"Vapi API error: {error_msg}"}
                
                result = response.json()
            
            logger.info(f"Vapi call initiated for {patient_name} at {patient_phone}")
            
            return {
                "success": True,
                "patient_phone": patient_phone,
                "patient_name": patient_name,
                "call_id": result.get("id") or result.get("callId"),
                "status": result.get("status", "initiated"),
            }
            
        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error: {e.response.status_code} - {e.response.text}"
            logger.error(f"Error calling patient {patient_phone}: {error_msg}")
            return {"success": False, "error": error_msg}
        except Exception as e:
            logger.error(f"Error calling patient {patient_phone}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


# Global instance
_phone_service = None


async def get_phone_service() -> VapiPhoneService:
    """Get or create the global phone service instance"""
    global _phone_service
    if _phone_service is None:
        _phone_service = VapiPhoneService()
    return _phone_service


async def call_patient_for_appointment(
    patient_phone: str,
    patient_name: str,
    patient_id: str,
    context: Optional[str] = None,
) -> Dict[str, Any]:
    """Call a patient to schedule an appointment"""
    service = await get_phone_service()
    
    # Mock available appointment slots
    available_slots = [
        "Monday, 9:00 AM",
        "Monday, 10:00 AM",
        "Monday, 2:00 PM",
        "Tuesday, 9:00 AM",
        "Tuesday, 11:00 AM",
        "Wednesday, 10:00 AM",
        "Wednesday, 1:00 PM",
        "Thursday, 9:00 AM",
        "Thursday, 3:00 PM",
        "Friday, 10:00 AM",
    ]
    
    return await service.call_patient(
        patient_phone=patient_phone,
        patient_name=patient_name,
        context=context,
        appointment_slots=available_slots,
    )

if __name__ == "__main__":
    asyncio.run(call_patient_for_appointment("+14159050147", "John Doe", "+14159050147"))