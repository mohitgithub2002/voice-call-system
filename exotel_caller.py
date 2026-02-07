"""
Exotel Voice Call Module
Makes automated voice calls with Hindi TTS for fee reminders using Exotel API
https://developer.exotel.com/api/make-a-call-api
"""

import os
import requests
from typing import Dict, Optional


class ExotelCaller:
    """Handles Exotel voice calls for fee reminders."""
    
    def __init__(self):
        self.api_key = os.getenv('EXOTEL_API_KEY')
        self.api_token = os.getenv('EXOTEL_API_TOKEN')
        self.account_sid = os.getenv('EXOTEL_ACCOUNT_SID')
        self.caller_id = os.getenv('EXOTEL_CALLER_ID')
        self.app_id = os.getenv('EXOTEL_APP_ID')
        self.subdomain = os.getenv('EXOTEL_SUBDOMAIN', 'api.in.exotel.com')
        self.org_name = os.getenv('ORG_NAME', 'फीस विभाग')
        
        if not all([self.api_key, self.api_token, self.account_sid, self.caller_id, self.app_id]):
            raise ValueError(
                "Missing Exotel credentials. "
                "Please set EXOTEL_API_KEY, EXOTEL_API_TOKEN, EXOTEL_ACCOUNT_SID, "
                "EXOTEL_CALLER_ID, and EXOTEL_APP_ID in .env file"
            )
        
        # Build base URL for API calls
        self.base_url = f"https://{self.api_key}:{self.api_token}@{self.subdomain}/v1/Accounts/{self.account_sid}"
    
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
    
    def _format_phone_number(self, phone_number: str) -> str:
        """
        Format phone number for Exotel API.
        Exotel expects numbers in format: 0XXXXXXXXXX (with STD code)
        or E.164 format without the + prefix.
        """
        # Remove any spaces, dashes, or parentheses
        phone = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        
        # Handle +91 prefix (India)
        if phone.startswith('+91'):
            phone = '0' + phone[3:]  # Replace +91 with 0
        elif phone.startswith('91') and len(phone) == 12:
            phone = '0' + phone[2:]  # Replace 91 with 0
        elif phone.startswith('+'):
            phone = phone[1:]  # Just remove the +
        elif not phone.startswith('0') and len(phone) == 10:
            phone = '0' + phone  # Add leading 0 for 10-digit numbers
            
        return phone
    
    def make_call(self, student: Dict, dry_run: bool = False) -> Dict:
        """
        Make a voice call to a student using Exotel.
        
        Args:
            student: Student data dict with phone_number, student_name, etc.
            dry_run: If True, don't actually make the call
            
        Returns:
            Dict with call status and details
        """
        phone_number = self._format_phone_number(student['phone_number'])
        message = self.generate_hindi_message(student)
        
        if dry_run:
            return {
                'status': 'dry_run',
                'phone': phone_number,
                'message': message,
                'student_name': student['student_name']
            }
        
        try:
            # Exotel API endpoint for connecting to a call flow (applet)
            url = f"{self.base_url}/Calls/connect.json"

            student_name = str(student['student_name']).replace(" ", "%20") 
            amount = str(student['pending_fees']).replace(" ", "%20")
            due_date = str(student['due_date']).replace(" ", "%20")
            
            # Build the applet URL
            applet_url = f"http://my.exotel.com/{self.account_sid}/exoml/start_voice/{self.app_id}"
            
            # POST data
            data = {
                'From': phone_number,
                'CallerId': self.caller_id,
                'Url': applet_url,
                'CallType': 'trans',  # Transactional call
                'TimeLimit': 120,     # 2 minutes max
                'TimeOut': 30,        # Ring for 30 seconds
                'CustomField': student_name,
                
            }
            
            # Make the API call
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                call_data = result.get('Call', {})
                
                return {
                    'status': 'initiated',
                    'call_sid': call_data.get('Sid', 'unknown'),
                    'phone': phone_number,
                    'student_name': student['student_name']
                }
            else:
                return {
                    'status': 'error',
                    'error': f"API returned status {response.status_code}: {response.text}",
                    'phone': phone_number,
                    'student_name': student['student_name']
                }
                
        except requests.exceptions.Timeout:
            return {
                'status': 'error',
                'error': 'API request timed out',
                'phone': phone_number,
                'student_name': student['student_name']
            }
        except requests.exceptions.RequestException as e:
            return {
                'status': 'error',
                'error': str(e),
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
            url = f"{self.base_url}/Calls/{call_sid}.json"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                call_data = result.get('Call', {})
                return call_data.get('Status')
            return None
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
    
    try:
        caller = ExotelCaller()
        print("Generated message:")
        print(caller.generate_hindi_message(test_student))
        print(f"\nFormatted phone: {caller._format_phone_number(test_student['phone_number'])}")
    except ValueError as e:
        print(f"Note: {e}")
        print("\nMessage preview (without credentials):")
        print(f"""
        नमस्ते {test_student['student_name']} जी,
        
        यह फीस विभाग से बात हो रही है।
        
        आपकी {test_student['pending_fees']} रुपये की फीस बकाया है।
        
        कृपया {test_student['due_date']} से पहले भुगतान करें।
        
        धन्यवाद।
        """)
