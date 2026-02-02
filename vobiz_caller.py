"""
Vobiz Voice Call Module
Makes automated voice calls with Hindi TTS for fee reminders using Vobiz API
https://www.docs.vobiz.ai/call/overview
"""

import os
import requests
from typing import Dict, Optional
from urllib.parse import urlencode


class VobizCaller:
    """Handles Vobiz voice calls for fee reminders."""
    
    def __init__(self):
        self.auth_id = os.getenv('VOBIZ_AUTH_ID')
        self.auth_token = os.getenv('VOBIZ_AUTH_TOKEN')
        self.caller_id = os.getenv('VOBIZ_CALLER_ID')
        self.answer_url = os.getenv('VOBIZ_ANSWER_URL')
        self.org_name = os.getenv('ORG_NAME', 'फीस विभाग')
        
        if not all([self.auth_id, self.auth_token, self.caller_id, self.answer_url]):
            raise ValueError(
                "Missing Vobiz credentials. "
                "Please set VOBIZ_AUTH_ID, VOBIZ_AUTH_TOKEN, VOBIZ_CALLER_ID, "
                "and VOBIZ_ANSWER_URL in .env file"
            )
        
        # Build base URL for API calls
        self.base_url = f"https://api.vobiz.ai/api/v1/Account/{self.auth_id}"
    
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
        Format phone number for Vobiz API.
        Vobiz expects numbers in E.164 format (with country code, no +).
        Example: 919876543210 for Indian numbers
        """
        # Remove any spaces, dashes, or parentheses
        phone = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        
        # Handle +91 prefix (India)
        if phone.startswith('+'):
            phone = phone[1:]  # Remove the +
        elif phone.startswith('0') and len(phone) == 11:
            phone = '91' + phone[1:]  # Replace leading 0 with 91
        elif len(phone) == 10:
            phone = '91' + phone  # Add 91 for 10-digit numbers
            
        return phone
    
    def _build_answer_url(self, student: Dict) -> str:
        """
        Build the full answer_url including our query params for this student.

        Vobiz docs: answer_url is "URL called when the call is answered. Must return valid XML."
        We send this full URL (with query string) in the Make Call request. When the call
        is answered, Vobiz performs an HTTP request to that exact URL—so the query params
        are part of the URL we provided, not something Vobiz adds. Our server receives
        them in the request (e.g. request.args in Flask).
        """
        params = {
            'student_name': student['student_name'],
            'amount': student['pending_fees'],
            'due_date': student['due_date'],
            'org_name': self.org_name
        }
        return f"{self.answer_url}?{urlencode(params)}"

    def _build_hangup_url(self) -> str:
        """Build hangup callback URL from answer_url base (same host, /hangup path)."""
        base = self.answer_url.split('?')[0].rstrip('/')
        if base.endswith('/answer'):
            return base[:-7] + '/hangup'
        return base + '/hangup' if base else '/hangup'
    
    def make_call(self, student: Dict, dry_run: bool = False) -> Dict:
        """
        Make a voice call to a student using Vobiz.
        
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
            # Vobiz API endpoint for making calls
            url = f"{self.base_url}/Call/"
            
            # Build the answer URL with student parameters
            answer_url = self._build_answer_url(student)
            
            # Request headers
            headers = {
                'X-Auth-ID': self.auth_id,
                'X-Auth-Token': self.auth_token,
                'Content-Type': 'application/json'
            }
            
            # JSON body (Vobiz Make Call API)
            hangup_url = self._build_hangup_url()
            data = {
                'from': self.caller_id,
                'to': phone_number,
                'answer_url': answer_url,
                'answer_method': 'POST',
                'ring_timeout': '30',
                'time_limit': '120',  # 2 minutes max
                'hangup_url': hangup_url,
                'hangup_method': 'POST',
            }
            
            # Make the API call
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200 or response.status_code == 201:
                result = response.json()
                
                return {
                    'status': 'initiated',
                    'call_uuid': result.get('call_uuid', 'unknown'),
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
    
    def get_call_status(self, call_uuid: str) -> Optional[Dict]:
        """Get the status of a call by UUID."""
        try:
            url = f"{self.base_url}/Call/{call_uuid}/"
            headers = {
                'X-Auth-ID': self.auth_id,
                'X-Auth-Token': self.auth_token,
            }
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
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
        caller = VobizCaller()
        print("Generated message:")
        print(caller.generate_hindi_message(test_student))
        print(f"\nFormatted phone: {caller._format_phone_number(test_student['phone_number'])}")
        print(f"Answer URL: {caller._build_answer_url(test_student)}")
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
