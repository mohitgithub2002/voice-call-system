"""
Twilio Voice Call Module
Makes automated voice calls with Hindi TTS for fee reminders
"""

import os
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse
from typing import Dict, Optional


class TwilioCaller:
    """Handles Twilio voice calls with Hindi text-to-speech."""
    
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_PHONE_NUMBER')
        self.org_name = os.getenv('ORG_NAME', 'फीस विभाग')
        
        if not all([self.account_sid, self.auth_token, self.from_number]):
            raise ValueError(
                "Missing Twilio credentials. "
                "Please set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_PHONE_NUMBER in .env file"
            )
        
        self.client = Client(self.account_sid, self.auth_token)
    
    def generate_hindi_message(self, student: Dict) -> str:
        """Generate Hindi reminder message for a student."""
        message = f"""
        नमस्ते {student['student_name']} जी,
        
        यह {self.org_name} से बात हो रही है।
        
        आपकी {student['pending_fees']} रुपये की फीस बकाया है।
        
        कृपया {student['due_date']} से पहले भुगतान करें।
        
        धन्यवाद।
        """
        return message.strip()
    
    def create_twiml(self, message: str) -> str:
        """Create TwiML response with Hindi speech."""
        response = VoiceResponse()
        
        # Use Hindi voice with Google TTS
        response.say(
            message,
            voice='Google.hi-IN-Wavenet-A',  # Hindi female voice
            language='hi-IN'
        )
        
        # Pause before ending
        response.pause(length=1)
        
        return str(response)
    
    def make_call(self, student: Dict, dry_run: bool = False) -> Dict:
        """
        Make a voice call to a student.
        
        Args:
            student: Student data dict with phone_number, student_name, etc.
            dry_run: If True, don't actually make the call
            
        Returns:
            Dict with call status and details
        """
        phone_number = student['phone_number']
        message = self.generate_hindi_message(student)
        
        if dry_run:
            return {
                'status': 'dry_run',
                'phone': phone_number,
                'message': message,
                'student_name': student['student_name']
            }
        
        try:
            # Create TwiML for the call
            twiml = self.create_twiml(message)
            
            # Make the call
            call = self.client.calls.create(
                to=phone_number,
                from_=self.from_number,
                twiml=twiml
            )
            
            return {
                'status': 'initiated',
                'call_sid': call.sid,
                'phone': phone_number,
                'student_name': student['student_name']
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'phone': phone_number,
                'student_name': student['student_name']
            }
    
    def get_call_status(self, call_sid: str) -> Optional[str]:
        """Get the status of a call by SID."""
        try:
            call = self.client.calls(call_sid).fetch()
            return call.status
        except Exception:
            return None


if __name__ == "__main__":
    # Test message generation
    from dotenv import load_dotenv
    load_dotenv()
    
    test_student = {
        'student_name': 'राहुल शर्मा',
        'phone_number': '+919876543210',
        'pending_fees': '5000',
        'due_date': '15-02-2026'
    }
    
    caller = TwilioCaller()
    print("Generated message:")
    print(caller.generate_hindi_message(test_student))
