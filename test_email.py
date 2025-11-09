"""
Test email sending functionality
"""
import asyncio
from composio_integration import send_email_via_composio

async def test_email():
    print("Testing email sending...")
    try:
        result = await send_email_via_composio(
            to_email='mnvsk97@gmail.com',
            subject='Test Email from BacklineMD',
            body='This is a test email to verify the email sending functionality is working correctly.',
            user_id='backlinemd-system'
        )
        print('Email test result:', result)
        if result.get('success'):
            print('✓ Email sent successfully!')
        else:
            print('✗ Email failed:', result.get('message', 'Unknown error'))
    except Exception as e:
        print(f'✗ Error sending email: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_email())

