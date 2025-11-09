"""
Composio Email Integration for BacklineMD
Handles email sending for patient communication, task notifications, etc.
"""

import asyncio
import os

from agents import Agent, Runner
from composio import Composio
from composio_openai_agents import OpenAIAgentsProvider
from dotenv import load_dotenv

load_dotenv()

composio = Composio(
    api_key=os.getenv("COMPOSIO_API_KEY"), provider=OpenAIAgentsProvider()
)

# Hardcoded email for demo/testing
DEMO_EMAIL = "mnvsk97@gmail.com"


async def send_email_via_composio(
    to_email: str,
    subject: str,
    body: str,
    user_id: str = "pg-test-f5bc24e1-23e5-4cc5-99fa-3a00cb1784e5",
):
    """
    Send email using Composio Gmail integration

    Args:
        to_email: Recipient email address (always sends to mnvsk97@gmail.com for demo)
        subject: Email subject
        body: Email body content
        user_id: User identifier for Composio connection

    Returns:
        dict: Result of email send operation
    """
    try:
        # Always send to demo email for testing
        actual_to_email = DEMO_EMAIL

        # Check if account is already connected, if not, link it
        try:
            # Try to get tools first (will fail if not connected)
            tools = composio.tools.get(user_id=user_id, tools=["GMAIL_SEND_EMAIL"])
        except Exception:
            # If not connected, get the link URL
            connection_request = composio.connected_accounts.link(
                user_id=user_id,
                auth_config_id="ac_xbQn8c52f2FK",
            )
            redirect_url = connection_request.redirect_url
            print(f"Please authorize the app by visiting this URL: {redirect_url}")
            # Try again after linking
            tools = composio.tools.get(user_id=user_id, tools=["GMAIL_SEND_EMAIL"])

        agent = Agent(
            name="Email Manager",
            instructions="You are a helpful assistant that sends emails on behalf of BacklineMD healthcare platform.",
            tools=tools,
        )

        # Create the email prompt
        email_prompt = f"Send an email to {actual_to_email} with the subject '{subject}' and the body '{body}'"

        # Run the agent
        result = await Runner.run(
            starting_agent=agent,
            input=email_prompt,
        )

        return {
            "success": True,
            "message": "Email sent successfully",
            "result": (
                result.final_output if hasattr(result, "final_output") else str(result)
            ),
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to send email: {str(e)}",
            "error": str(e),
        }


async def send_welcome_email(patient_email: str = None, patient_name: str = None):
    """
    Send welcome email to patient
    """
    body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; background-color: #f5f6fa;">
          <div style="max-width: 540px; margin: 40px auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); overflow: hidden;">
            <div style="background-color: #0058a3; padding: 24px; color: #fff;">
              <h2 style="margin: 0;">Welcome to BacklineMD</h2>
            </div>
            <div style="padding: 32px 24px;">
              <p>Dear {patient_name},</p>
              <p>
                Welcome to BacklineMD! We're excited to have you on board.
              </p>
              <p>
                Please click the link below to complete your profile and get started:
              </p>
              <p style="text-align: center;">
                <a href="<!-- INSERT_WELCOME_LINK_HERE -->"
                   style="display:inline-block; padding:12px 28px; background:#0058a3; color:#fff; border-radius:4px; text-decoration:none; font-size:16px; font-weight:bold;">
                  Complete Your Profile
                </a>
              </p>
              <p>
                If you have any questions or need assistance, please reply to this email or contact our support team.
              </p>
              <p>
                Thank you for choosing BacklineMD!
              </p>
              <p style="margin-top:32px;">
                Best regards,<br/>
                <span style="color:#0058a3; font-weight: bold;">BacklineMD Team</span>
              </p>
            </div>
            <div style="background-color:#f0f4f8; text-align:center; font-size:12px; color:#888; padding:12px;">
              © {2024} BacklineMD – Confidential and Secure Communication
            </div>
          </div>
        </body>
        </html>
    """
    return await send_email_via_composio(
        to_email=DEMO_EMAIL, subject="Welcome to BacklineMD", body=body
    )


async def send_consent_form_email(patient_email: str = None, patient_name: str = None):
    """
    Send consent form email to patient
    """

    body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; background-color: #f5f6fa;">
          <div style="max-width: 540px; margin: 40px auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); overflow: hidden;">
            <div style="background-color: #0058a3; padding: 24px; color: #fff;">
              <h2 style="margin: 0;">Consent Form Signature Request</h2>
            </div>
            <div style="padding: 32px 24px;">
              <p>Dear {patient_name},</p>
              <p>
                We kindly request your review and signature on an important consent form to confirm your agreement and facilitate your ongoing care with BacklineMD.
              </p>
              <p>
                To proceed, please click the secure link below to view and sign your consent form:
              </p>
              <p style="text-align: center;">
                <a href="<!-- INSERT_CONSENT_FORM_LINK_HERE -->"
                   style="display:inline-block; padding:12px 28px; background:#0058a3; color:#fff; border-radius:4px; text-decoration:none; font-size:16px; font-weight:bold;">
                  Review & Sign Consent Form
                </a>
              </p>
              <p>
                If you have any questions or require assistance, please reply to this email or contact our support team.
              </p>
              <p>
                Thank you for your attention and for choosing BacklineMD!
              </p>
              <p style="margin-top:32px;">
                Best regards,<br/>
                <span style="color:#0058a3; font-weight: bold;">BacklineMD Team</span>
              </p>
            </div>
            <div style="background-color:#f0f4f8; text-align:center; font-size:12px; color:#888; padding:12px;">
              © {2024} BacklineMD – Confidential and Secure Communication
            </div>
          </div>
        </body>
        </html>
    """
    return await send_email_via_composio(
        to_email=DEMO_EMAIL, subject="Consent Form - BacklineMD", body=body
    )


async def send_appointment_scheduled_email(
    patient_email: str = None,
    patient_name: str = None,
    date: str = None,
    time: str = None,
    type: str = None,
    provider: str = None,
):
    """
    Send appointment scheduled notification email to patient

    Args:
        patient_email: Patient's email address
        patient_name: Patient's full name
        date: Appointment date
        time: Appointment time
        type: Appointment type (Consultation, Follow-Up, etc.)
        provider: Name of the provider
    """
    subject = "Your Appointment is Scheduled - BacklineMD"

    body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333; background-color: #f5f6fa;">
          <div style="max-width: 540px; margin: 40px auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); overflow: hidden;">
            <div style="background-color: #0058a3; padding: 24px; color: #fff;">
              <h2 style="margin: 0;">Appointment Scheduled</h2>
            </div>
            <div style="padding: 32px 24px;">
              <p>Dear {patient_name if patient_name else 'Patient'},</p>
              <p>
                Your appointment has been scheduled successfully.
              </p>
              <div style="background-color: #f0f4f8; padding: 16px; border-radius: 4px; margin: 20px 0;">
                <p style="margin: 8px 0;"><strong>Date:</strong> {date if date else 'TBD'}</p>
                <p style="margin: 8px 0;"><strong>Time:</strong> {time if time else 'TBD'}</p>
                <p style="margin: 8px 0;"><strong>Type:</strong> {type if type else 'Consultation'}</p>
                <p style="margin: 8px 0;"><strong>Provider:</strong> {provider if provider else 'BacklineMD'}</p>
              </div>
              <p>
                Please arrive 15 minutes early for check-in.
              </p>
              <p>
                If you have any questions or need to reschedule, please contact us.
              </p>
              <p style="margin-top:32px;">
                Best regards,<br/>
                <span style="color:#0058a3; font-weight: bold;">BacklineMD Team</span>
              </p>
            </div>
            <div style="background-color:#f0f4f8; text-align:center; font-size:12px; color:#888; padding:12px;">
              © 2024 BacklineMD – Confidential and Secure Communication
            </div>
          </div>
        </body>
        </html>
    """

    return await send_email_via_composio(
        to_email=DEMO_EMAIL, subject=subject, body=body
    )


if __name__ == "__main__":
    # Test the email sending
    async def test():
        result = await send_appointment_scheduled_email(
            patient_email=DEMO_EMAIL,
            patient_name="Sai",
            date="2025-11-15",
            time="10:00 AM",
            type="Initial Consultation",
            provider="Dr. James O'Brien",
        )
        print(result)

    asyncio.run(test())
