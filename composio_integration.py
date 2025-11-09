"""
Composio Email Integration for BacklineMD
Handles email sending for patient communication, task notifications, etc.
"""
import os
import asyncio
from composio_openai import ComposioToolSet, Action
from openai import OpenAI

# Initialize Composio with API key from environment
COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY", "ak_Z8mFgdJ1BQjPfypujoYn")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize toolset
toolset = ComposioToolSet(api_key=COMPOSIO_API_KEY)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


async def send_email_via_composio(
    to_email: str,
    subject: str,
    body: str,
    user_id: str = "backlinemd-system"
):
    """
    Send email using Composio Gmail integration
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        body: Email body content
        user_id: User identifier for Composio connection
    
    Returns:
        dict: Result of email send operation
    """
    try:
        # Get Gmail tools for the user
        tools = toolset.get_tools(
            actions=[Action.GMAIL_SEND_EMAIL],
            user_id=user_id
        )
        
        # Create message for the agent
        prompt = f"""
        Send an email with the following details:
        To: {to_email}
        Subject: {subject}
        Body: {body}
        """
        
        # Use OpenAI to execute the action
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that sends emails on behalf of BacklineMD healthcare platform."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            tools=tools,
            tool_choice="auto"
        )
        
        # Process tool calls
        if response.choices[0].message.tool_calls:
            tool_calls = response.choices[0].message.tool_calls
            result = toolset.handle_tool_calls(
                response,
                user_id=user_id
            )
            return {
                "success": True,
                "message": "Email sent successfully",
                "result": result
            }
        else:
            return {
                "success": False,
                "message": "No tool calls made",
                "response": response.choices[0].message.content
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to send email: {str(e)}",
            "error": str(e)
        }


async def send_patient_notification_email(
    patient_email: str,
    patient_name: str,
    notification_type: str,
    details: dict
):
    """
    Send notification email to patient
    
    Args:
        patient_email: Patient's email address
        patient_name: Patient's full name
        notification_type: Type of notification (appointment, task_completed, etc.)
        details: Additional details for the email
    """
    # Generate email based on notification type
    subjects = {
        "appointment_scheduled": "Your Appointment is Scheduled - BacklineMD",
        "appointment_reminder": "Appointment Reminder - BacklineMD",
        "task_completed": "Your Task Has Been Completed - BacklineMD",
        "consent_form": "Consent Form Ready for Signature - BacklineMD",
        "claim_update": "Insurance Claim Update - BacklineMD",
    }
    
    subject = subjects.get(notification_type, "Notification from BacklineMD")
    
    # Generate body based on type
    if notification_type == "appointment_scheduled":
        body = f"""
Dear {patient_name},

Your appointment has been scheduled successfully.

Details:
- Date: {details.get('date', 'TBD')}
- Time: {details.get('time', 'TBD')}
- Type: {details.get('type', 'Consultation')}
- Provider: {details.get('provider', 'BacklineMD')}

Please arrive 15 minutes early for check-in.

Best regards,
BacklineMD Team
        """
    elif notification_type == "consent_form":
        body = f"""
Dear {patient_name},

A consent form is ready for your review and signature.

Form: {details.get('form_name', 'Medical Consent Form')}

Please log in to your patient portal to review and sign the form.

Best regards,
BacklineMD Team
        """
    else:
        body = f"""
Dear {patient_name},

{details.get('message', 'You have a new notification from BacklineMD.')}

Best regards,
BacklineMD Team
        """
    
    return await send_email_via_composio(
        to_email=patient_email,
        subject=subject,
        body=body
    )


# Initialize connection helper
async def initialize_composio_connection(user_id: str = "backlinemd-system"):
    """
    Initialize Composio connection for Gmail
    Returns connection URL for OAuth flow
    """
    try:
        connection_request = toolset.initiate_connection(
            entity_id=user_id,
            auth_mode="OAUTH2",
            auth_config={
                "app": "gmail"
            }
        )
        
        return {
            "success": True,
            "redirect_url": connection_request.redirectUrl,
            "message": "Please authorize Gmail access by visiting the redirect URL"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to initialize connection"
        }


if __name__ == "__main__":
    # Test the email sending
    async def test():
        result = await send_patient_notification_email(
            patient_email="test@example.com",
            patient_name="John Doe",
            notification_type="appointment_scheduled",
            details={
                "date": "2025-11-15",
                "time": "10:00 AM",
                "type": "Initial Consultation",
                "provider": "Dr. James O'Brien"
            }
        )
        print(result)
    
    asyncio.run(test())
