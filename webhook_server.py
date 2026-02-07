"""
Vobiz Webhook Server
Flask server that handles Vobiz callbacks and returns TTS XML for fee reminders
Deploy this on your server and set VOBIZ_ANSWER_URL to point to it

Usage:
    python webhook_server.py

For production, use gunicorn:
    gunicorn webhook_server:app -b 0.0.0.0:5000
"""

import os
import xml.sax.saxutils
from flask import Flask, request, Response, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from vobiz_caller import VobizCaller

app = Flask(__name__)

# Organization name from environment or default
ORG_NAME = os.getenv('ORG_NAME', 'फीस विभाग')

# Initialize Vobiz caller (will be None if credentials are missing)
try:
    vobiz_caller = VobizCaller()
except ValueError:
    vobiz_caller = None


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return {'status': 'ok', 'service': 'vobiz-webhook'}


def _get_param(key: str, default: str = '') -> str:
    """Get param from query string or POST body (Vobiz may send POST body)."""
    return (request.args.get(key) or request.form.get(key) or default).strip() or default


@app.route('/answer', methods=['GET', 'POST'])
def answer_call():
    """
    Handle Vobiz answer callback.
    Returns XML with Hindi TTS message for fee reminder.
    Vobiz docs: answer_url must return valid XML.
    Student data is in URL query (we build it); Vobiz may also POST its params in body.
    """
    # Get student details from query params (our URL) or form (if present)
    student_name = _get_param('student_name', 'Student')
    amount = _get_param('amount', '0')
    due_date = _get_param('due_date', '')
    org_name = _get_param('org_name') or ORG_NAME

    # Build Hindi TTS message with commas for natural pauses between sentences
    hindi_message = f"""
नमस्ते {student_name} जी।
यह {org_name} से बात हो रही है।
आपकी {amount} रुपये की फीस बकाया है।
कृपया {due_date} से पहले भुगतान करें।
धन्यवाद।
    """.strip()
    hindi_message_safe = xml.sax.saxutils.escape(hindi_message)

    # Return Vobiz XML: Speak once (loop=0), then Hangup to end the call
    xml_response = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Speak language="hi-IN" voice="WOMAN" >
        {hindi_message_safe}
    </Speak>
</Response>'''

    return Response(xml_response, mimetype='application/xml')


@app.route('/hangup', methods=['GET', 'POST'])
def hangup_callback():
    """
    Handle Vobiz hangup callback.
    Vobiz sends: from, to, call_uuid, call_status, start_time, answer_time, end_time, hangup_time (no duration).
    """
    call_uuid = _get_param('call_uuid', '')
    call_status = _get_param('call_status', '')
    start_time = _get_param('start_time', '')
    answer_time = _get_param('answer_time', '')
    end_time = _get_param('end_time', '')
    hangup_time = _get_param('hangup_time', '')

    # Log the call completion (you can add database logging here)
    print(f"Call completed: UUID={call_uuid}, Status={call_status}, start={start_time}, answer={answer_time}, end={end_time}, hangup={hangup_time}")

    return {'status': 'received'}


@app.route('/exotel/answer', methods=['GET', 'HEAD'])
def exotel_answer():
    """
    Handle Exotel dynamic greeting callback.
    
    Exotel makes a GET request with these query parameters:
        - CallSid: unique identifier of the call
        - From: the calling party number
        - To: the Exotel company number being called
        - DialWhomNumber: the number being dialed (may be empty)
        - CustomField: custom data (not used - we lookup from CSV)
    
    Looks up student data from sample_students.csv based on the From number.
    
    Returns:
        Plain text message to be read out via Exotel's TTS engine.
        Content-Type MUST be 'text/plain'.
    """
    import csv
    
    # For HEAD requests, just return headers without body
    if request.method == 'HEAD':
        response = Response('', mimetype='text/plain')
        return response
    
    # Get Exotel query parameters
    call_sid = request.args.get('CallSid', '')
    from_number = request.args.get('From', '')
    to_number = request.args.get('To', '')
    dial_whom = request.args.get('DialWhomNumber', '')
    
    # Log the incoming request
    print(f"Exotel Answer Request: CallSid={call_sid}, From={from_number}, To={to_number}")
    
    # Normalize phone number - extract last 10 digits
    def normalize_phone(phone: str) -> str:
        """Extract last 10 digits from phone number."""
        digits = ''.join(filter(str.isdigit, str(phone)))
        return digits[-10:] if len(digits) >= 10 else digits
    
    normalized_from = normalize_phone(from_number)
    
    # Default values
    student_name = 'Student'
    amount = '0'
    due_date = ''
    org_name = ORG_NAME
    student_found = False
    
    # Look up student in CSV file
    csv_path = os.path.join(os.path.dirname(__file__), 'sample_students.csv')
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                csv_phone = normalize_phone(row.get('phone_number', ''))
                if csv_phone == normalized_from:
                    student_name = row.get('student_name', student_name)
                    amount = row.get('pending_fees', amount)
                    due_date = row.get('due_date', due_date)
                    student_found = True
                    print(f"Found student: {student_name}, Amount: {amount}, Due: {due_date}")
                    break
    except FileNotFoundError:
        print(f"CSV file not found: {csv_path}")
    except Exception as e:
        print(f"Error reading CSV: {e}")
    
    if not student_found:
        print(f"No student found for phone: {from_number} (normalized: {normalized_from})")
    
    # Build Hindi TTS message with SSML format
    hindi_text = f"""नमस्ते। यह {org_name} की फीस रिमाइंडर कॉल है।
    {student_name}, की ₹{amount} फीस बकाया है।
    अंतिम तिथि {due_date} है। कृपया जल्द भुगतान करें। धन्यवाद।"""
    
    # Wrap in SSML speak and voice tags
    ssml_response = f"""<speak>
  <voice language="hi-IN">
    {hindi_text}
  </voice>
</speak>"""
    
    # Return plain text response as required by Exotel
    response = Response(ssml_response, mimetype='text/plain')
    return response


@app.route('/api/call', methods=['POST'])
def make_call():
    """
    API endpoint to initiate a fee reminder call.
    
    Request Body (JSON):
        {
            "student_name": "राहुल शर्मा",
            "phone_number": "+919876543210",
            "pending_fees": "5000",
            "due_date": "15-02-2026"
        }
    
    Response:
        {
            "success": true,
            "status": "initiated",
            "call_uuid": "...",
            "message": "Call initiated successfully"
        }
    """
    # Check if Vobiz caller is initialized
    if vobiz_caller is None:
        return jsonify({
            'success': False,
            'error': 'Vobiz credentials not configured. Please set VOBIZ_AUTH_ID, VOBIZ_AUTH_TOKEN, VOBIZ_CALLER_ID, and VOBIZ_ANSWER_URL in .env file'
        }), 500
    
    # Get JSON data from request
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'error': 'Request body must be JSON'
        }), 400
    
    # Validate required fields
    required_fields = ['student_name', 'phone_number', 'pending_fees', 'due_date']
    missing_fields = [field for field in required_fields if field not in data or not data[field]]
    
    if missing_fields:
        return jsonify({
            'success': False,
            'error': f'Missing required fields: {", ".join(missing_fields)}'
        }), 400
    
    # Prepare student data
    student = {
        'student_name': str(data['student_name']).strip(),
        'phone_number': str(data['phone_number']).strip(),
        'pending_fees': str(data['pending_fees']).strip(),
        'due_date': str(data['due_date']).strip()
    }
    
    # Make the call
    result = vobiz_caller.make_call(student)
    
    if result['status'] == 'initiated':
        return jsonify({
            'success': True,
            'status': 'initiated',
            'call_uuid': result.get('call_uuid'),
            'phone': result.get('phone'),
            'student_name': result.get('student_name'),
            'message': 'Call initiated successfully'
        }), 200
    else:
        return jsonify({
            'success': False,
            'status': 'error',
            'error': result.get('error', 'Unknown error'),
            'phone': result.get('phone'),
            'student_name': result.get('student_name')
        }), 500


@app.route('/api/call/status/<call_uuid>', methods=['GET'])
def get_call_status(call_uuid):
    """
    Get the status of a call by its UUID.
    
    Response:
        {
            "success": true,
            "call_uuid": "...",
            "status": "..."
        }
    """
    if vobiz_caller is None:
        return jsonify({
            'success': False,
            'error': 'Vobiz credentials not configured'
        }), 500
    
    status = vobiz_caller.get_call_status(call_uuid)
    
    if status:
        return jsonify({
            'success': True,
            'call_uuid': call_uuid,
            'data': status
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': 'Call not found or error fetching status'
        }), 404


if __name__ == "__main__":
    port = int(os.getenv('WEBHOOK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    print(f"Starting Vobiz Webhook Server on port {port}")
    print(f"")
    print(f"📡 Webhook Endpoints:")
    print(f"   Answer URL:  http://localhost:{port}/answer")
    print(f"   Hangup URL:  http://localhost:{port}/hangup")
    print(f"")
    print(f"🔌 API Endpoints:")
    print(f"   POST /api/call         - Make a call")
    print(f"   GET  /api/call/status/<uuid> - Get call status")
    print(f"")
    print(f"❤️  Health Check: http://localhost:{port}/health")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
