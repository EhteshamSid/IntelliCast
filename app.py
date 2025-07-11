from flask import Flask, request, jsonify, send_from_directory, render_template_string
import uuid
import os
from politics_bot import PoliticsChatbotAgentic
import json

app = Flask(__name__)
chatbot = PoliticsChatbotAgentic()

SESSIONS_FILE = 'sessions.json'

def load_sessions():
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_sessions():
    with open(SESSIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)

sessions = load_sessions()

# Serve the frontend
@app.route('/')
def index():
    # We'll use a template string for now; can move to a file later
    return render_template_string(open('templates/index.html').read())

# Chat endpoint
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json(force=True) or {}
    message = data.get('message', '')
    session_id = data.get('session_id')
    if not session_id or session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 400
    history = sessions[session_id]['history']
    # Call the chatbot (sync for now)
    import asyncio
    result = asyncio.run(chatbot.chat(message, history))
    # Add to history
    sessions[session_id]['history'].append({
        'message': message,
        'response': result['response'],
        'is_political': result.get('is_political', False),
        'timestamp': result.get('timestamp', '')
    })
    save_sessions()
    return jsonify(result)

# List/create/delete sessions
@app.route('/sessions', methods=['GET', 'POST'])
def session_list():
    if request.method == 'POST':
        # Create new session
        session_id = str(uuid.uuid4())
        sessions[session_id] = {'history': []}
        save_sessions()
        return jsonify({'session_id': session_id})
    else:
        # List sessions
        return jsonify([
            {'session_id': sid, 'length': len(s["history"])}
            for sid, s in sessions.items()
        ])

@app.route('/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    if session_id in sessions:
        del sessions[session_id]
        save_sessions()
        return '', 204
    return jsonify({'error': 'Session not found'}), 404

# Get summary for a session
@app.route('/summary/<session_id>')
def summary(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 400
    summary = chatbot.get_conversation_summary(sessions[session_id]['history'])
    return jsonify(summary)

# Get history for a session
@app.route('/sessions/<session_id>/history')
def session_history(session_id):
    if session_id not in sessions:
        return jsonify({'error': 'Invalid session'}), 400
    return jsonify(sessions[session_id]['history'])

# Serve static files (JS/CSS)
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    app.run(debug=True, port=5000) 