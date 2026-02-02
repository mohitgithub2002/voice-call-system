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
from flask import Flask, request, Response

app = Flask(__name__)

# Organization name from environment or default
ORG_NAME = os.getenv('ORG_NAME', 'फीस विभाग')


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return {'status': 'ok', 'service': 'vobiz-webhook'}


@app.route('/answer', methods=['GET', 'POST'])
def answer_call():
    """
    Handle Vobiz answer callback.
    Returns XML with Hindi TTS message for fee reminder.
    """
    # Get student details from query parameters
    student_name = request.args.get('student_name', 'Student')
    amount = request.args.get('amount', '0')
    due_date = request.args.get('due_date', '')
    org_name = request.args.get('org_name', ORG_NAME)
    
    # Build Hindi TTS message
    hindi_message = f"""
नमस्ते {student_name} जी,
यह {org_name} से बात हो रही है।
आपकी {amount} रुपये की फीस बकाया है।
कृपया {due_date} से पहले भुगतान करें।
धन्यवाद।
    """.strip()
    
    # Return Vobiz XML response with Speak element
    xml_response = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Speak language="hi-IN" voice="WOMAN" loop="1">
        {hindi_message}
    </Speak>
</Response>'''
    
    return Response(xml_response, mimetype='application/xml')


@app.route('/hangup', methods=['GET', 'POST'])
def hangup_callback():
    """
    Handle Vobiz hangup callback.
    Log call completion for analytics.
    """
    call_uuid = request.args.get('call_uuid', '')
    call_status = request.args.get('call_status', '')
    duration = request.args.get('duration', '0')
    
    # Log the call completion (you can add database logging here)
    print(f"Call completed: UUID={call_uuid}, Status={call_status}, Duration={duration}s")
    
    return {'status': 'received'}


if __name__ == "__main__":
    port = int(os.getenv('WEBHOOK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    print(f"Starting Vobiz Webhook Server on port {port}")
    print(f"Answer URL: http://localhost:{port}/answer")
    print(f"Hangup URL: http://localhost:{port}/hangup")
    print(f"Health Check: http://localhost:{port}/health")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
