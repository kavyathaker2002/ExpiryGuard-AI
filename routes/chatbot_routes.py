import os
import uuid

from flask import Blueprint, jsonify, request, session
from database import get_db
from routes.auth_routes import login_required
from ai.chat_assistant import fallback_answer, general_knowledge_answer, inventory_snapshot
from ai.provider_client import ProviderUnavailable, answer_chat

chatbot_bp = Blueprint('chatbot', __name__)
_chat_memory = {}


@chatbot_bp.route('/api/chatbot/message', methods=['POST'])
@login_required
def chat_message():
    data = request.get_json(silent=True) or {}
    user_msg = str(data.get('message', '')).strip()[:1500]
    if not user_msg:
        return jsonify({'reply': 'Please enter a question about your inventory.', 'mode': 'database_fallback', 'actions': []}), 400

    lang = session.get('lang', 'en')
    db = get_db()
    cursor = db.cursor()
    snapshot = inventory_snapshot(cursor, session['user_id'])
    chat_id = session.setdefault('chat_id', uuid.uuid4().hex)
    history = _chat_memory.get((session['user_id'], chat_id), [])
    messages = history[-8:] + [{'role': 'user', 'content': user_msg}]
    database_reply, database_supported = fallback_answer(user_msg, snapshot, history)

    if database_supported:
        reply = database_reply
        mode = 'database_fallback'
    elif os.environ.get('OPENAI_API_KEY', '').strip():
        try:
            reply = answer_chat(messages, snapshot, lang)
            if not reply:
                raise ProviderUnavailable('AI provider returned an empty response')
            mode = 'ai'
        except ProviderUnavailable:
            reply = general_knowledge_answer(user_msg, history, snapshot)
            mode = 'database_fallback'
    else:
        reply = general_knowledge_answer(user_msg, history, snapshot)
        mode = 'database_fallback'

    history.extend([{'role': 'user', 'content': user_msg}, {'role': 'assistant', 'content': reply}])
    _chat_memory[(session['user_id'], chat_id)] = history[-10:]
    if len(_chat_memory) > 1000:
        _chat_memory.pop(next(iter(_chat_memory)))
    return jsonify({'reply': reply, 'mode': mode, 'actions': []})
