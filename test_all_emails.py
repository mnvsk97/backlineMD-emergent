"""
Test all email functions
"""
import asyncio
from composio_integration import send_welcome_email, send_consent_form_email, send_appointment_scheduled_email

async def test_all_emails():
    print("=" * 60)
    print("Testing All Email Functions")
    print("=" * 60)
    print()
    
    # Test 1: Welcome Email
    print("1. Testing send_welcome_email...")
    print("-" * 60)
    try:
        result = await send_welcome_email(
            patient_email="test@example.com",
            patient_name="Test Patient"
        )
        if result.get('success'):
            print("✅ Welcome email sent successfully!")
            print(f"   Message: {result.get('message')}")
        else:
            print("❌ Welcome email failed!")
            print(f"   Error: {result.get('message')}")
            if result.get('error'):
                print(f"   Details: {result.get('error')}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    print()
    
    # Test 2: Consent Form Email
    print("2. Testing send_consent_form_email...")
    print("-" * 60)
    try:
        result = await send_consent_form_email(
            patient_email="test@example.com",
            patient_name="Test Patient"
        )
        if result.get('success'):
            print("✅ Consent form email sent successfully!")
            print(f"   Message: {result.get('message')}")
        else:
            print("❌ Consent form email failed!")
            print(f"   Error: {result.get('message')}")
            if result.get('error'):
                print(f"   Details: {result.get('error')}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    print()
    
    # Test 3: Appointment Scheduled Email
    print("3. Testing send_appointment_scheduled_email...")
    print("-" * 60)
    try:
        result = await send_appointment_scheduled_email(
            patient_email="test@example.com",
            patient_name="Test Patient",
            date="2025-11-20",
            time="10:00 AM",
            type="Initial Consultation",
            provider="Dr. James O'Brien"
        )
        if result.get('success'):
            print("✅ Appointment scheduled email sent successfully!")
            print(f"   Message: {result.get('message')}")
        else:
            print("❌ Appointment scheduled email failed!")
            print(f"   Error: {result.get('message')}")
            if result.get('error'):
                print(f"   Details: {result.get('error')}")
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
    print()
    
    print("=" * 60)
    print("Testing Complete!")
    print("=" * 60)
    print()
    print("Note: All emails are sent to mnvsk97@gmail.com (demo email)")
    print("Check that inbox to verify emails were received.")

if __name__ == "__main__":
    asyncio.run(test_all_emails())

