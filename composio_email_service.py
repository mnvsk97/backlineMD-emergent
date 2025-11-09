"""
Composio Email Service for BacklineMD
Simplified implementation using Composio Agent and Runner pattern
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional

from composio import Composio
from agents import Agent, Runner
from dotenv import load_dotenv
from composio_openai_agents import OpenAIAgentsProvider


load_dotenv()

logger = logging.getLogger(__name__)

# Composio configuration
COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY", "ak_Z8mFgdJ1BQjPfypujoYn")
EXTERNAL_USER_ID = os.getenv("COMPOSIO_EXTERNAL_USER_ID", "pg-test-f5bc24e1-23e5-4cc5-99fa-3a00cb1784e5")

# Initialize Composio
composio = Composio(api_key=COMPOSIO_API_KEY, provider=OpenAIAgentsProvider())


class ComposioEmailService:
    """Service for sending emails via Composio"""
    
    def __init__(self):
        self.composio = composio
        self.external_user_id = EXTERNAL_USER_ID
        self._email_agent = None
    
    def _get_email_agent(self) -> Agent:
        """Get or create the email agent"""
        if self._email_agent is None:
            tools = self.composio.tools.get(
                user_id=self.external_user_id,
                tools=["GMAIL_SEND_EMAIL"]
            )
            self._email_agent = Agent(
                name="Email Manager",
                instructions="You are a helpful assistant that sends emails via Gmail. Always send emails exactly as requested.",
                tools=tools
            )
        return self._email_agent
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send an email via Composio Gmail"""
        try:
            email_body = html_body if html_body else body
            email_instruction = f"Send an email to {to_email} with the subject '{subject}' and the body '{email_body}'"
            
            agent = self._get_email_agent()
            result = await Runner.run(starting_agent=agent, input=email_instruction)
            
            message_id = None
            if hasattr(result, 'final_output') and isinstance(result.final_output, dict):
                message_id = result.final_output.get("id") or result.final_output.get("message_id")
            
            logger.info(f"Email sent to {to_email}: {message_id or 'no ID'}")
            return {"success": True, "to": to_email, "subject": subject, "message_id": message_id}
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}", exc_info=True)
            return {"success": False, "error": str(e)}


# Global instance
_email_service = None


async def get_email_service() -> ComposioEmailService:
    """Get or create the global email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = ComposioEmailService()
    return _email_service


async def send_welcome_email(patient_email: str, patient_name: str) -> Dict[str, Any]:
    """Send welcome email to new patient"""
    service = await get_email_service()
    
    subject = "Welcome to Our Fertility Clinic - Next Steps"
    html_body = f"""<html><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50;">Welcome, {patient_name}!</h2>
            <p>Thank you for reaching out to our fertility clinic. We're here to support you on your journey to parenthood.</p>
            <h3 style="color: #3498db;">What Happens Next?</h3>
            <p>To help us provide you with the best care, we'll need the following documents:</p>
            <ul style="margin: 20px 0; padding-left: 30px;">
                <li><strong>Government-issued ID</strong> (driver's license or passport)</li>
                <li><strong>Insurance card</strong> (front and back)</li>
                <li><strong>Previous medical records</strong> (if available)</li>
                <li><strong>Lab results</strong> from any recent fertility testing</li>
                <li><strong>Imaging reports</strong> (ultrasounds, HSG, etc.)</li>
            </ul>
            <p>You can send these documents by replying to this email with attachments, or upload them through our patient portal.</p>
            <h3 style="color: #3498db;">Our Process</h3>
            <ol style="margin: 20px 0; padding-left: 30px;">
                <li>We'll review your documents and medical history</li>
                <li>Our care coordinator will call you to schedule your initial consultation</li>
                <li>During your consultation, our fertility specialist will discuss your options</li>
                <li>We'll work with your insurance to ensure coverage for recommended treatments</li>
            </ol>
            <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                If you have any questions, please don't hesitate to reply to this email or call us at (555) 123-4567.
            </p>
            <p style="color: #7f8c8d; font-size: 0.9em; margin-top: 20px;">Best regards,<br>The Fertility Clinic Team</p>
        </div></body></html>"""
    
    plain_body = f"""Welcome, {patient_name}!

Thank you for reaching out to our fertility clinic. We're here to support you on your journey to parenthood.

What Happens Next?

To help us provide you with the best care, we'll need the following documents:
- Government-issued ID (driver's license or passport)
- Insurance card (front and back)
- Previous medical records (if available)
- Lab results from any recent fertility testing
- Imaging reports (ultrasounds, HSG, etc.)

You can send these documents by replying to this email with attachments, or upload them through our patient portal.

Our Process:
1. We'll review your documents and medical history
2. Our care coordinator will call you to schedule your initial consultation
3. During your consultation, our fertility specialist will discuss your options
4. We'll work with your insurance to ensure coverage for recommended treatments

If you have any questions, please don't hesitate to reply to this email or call us at (555) 123-4567.

Best regards,
The Fertility Clinic Team"""
    
    return await service.send_email(to_email=patient_email, subject=subject, body=plain_body, html_body=html_body)


async def send_document_received_email(patient_email: str, patient_name: str) -> Dict[str, Any]:
    """Send confirmation email when documents are received"""
    service = await get_email_service()
    
    subject = "Documents Received - Consultation Scheduled Soon"
    html_body = f"""<html><body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2c3e50;">Thank You, {patient_name}!</h2>
            <p>We've successfully received your documents and our team is currently reviewing them.</p>
            <h3 style="color: #27ae60;">What's Next?</h3>
            <p>Our care coordinator will be calling you shortly to schedule your initial consultation. Please have your calendar ready so we can find a time that works best for you.</p>
            <p><strong>Our clinic hours are:</strong><br>Monday - Friday: 9:00 AM - 4:00 PM<br>(We are closed on weekends)</p>
            <p>During your consultation, our fertility specialist will:</p>
            <ul style="margin: 20px 0; padding-left: 30px;">
                <li>Review your medical history and test results</li>
                <li>Discuss your fertility goals and concerns</li>
                <li>Recommend a personalized treatment plan</li>
                <li>Answer any questions you may have</li>
            </ul>
            <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                If you have any questions before your consultation, please feel free to reply to this email.
            </p>
            <p style="color: #7f8c8d; font-size: 0.9em; margin-top: 20px;">Best regards,<br>The Fertility Clinic Team</p>
        </div></body></html>"""
    
    plain_body = f"""Thank You, {patient_name}!

We've successfully received your documents and our team is currently reviewing them.

What's Next?

Our care coordinator will be calling you shortly to schedule your initial consultation. Please have your calendar ready so we can find a time that works best for you.

Our clinic hours are:
Monday - Friday: 9:00 AM - 4:00 PM
(We are closed on weekends)

During your consultation, our fertility specialist will:
- Review your medical history and test results
- Discuss your fertility goals and concerns
- Recommend a personalized treatment plan
- Answer any questions you may have

If you have any questions before your consultation, please feel free to reply to this email.

Best regards,
The Fertility Clinic Team"""
    
    return await service.send_email(to_email=patient_email, subject=subject, body=plain_body, html_body=html_body)

if __name__ == "__main__":
    asyncio.run(send_welcome_email("mnvsk97+test@gmail.com", "Hi There"))