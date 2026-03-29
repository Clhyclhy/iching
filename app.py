import asyncio
import hashlib
import os
from pathlib import Path
import uuid

from quart import Quart, jsonify, render_template, request, session

try:
    from .iching import IChingBot
except ImportError:
    from iching import IChingBot

# Initialize Flask app
app = Quart(__name__)


def _load_or_create_secret_key(data_dir):
    env_key = os.getenv("APP_SECRET_KEY")
    if env_key:
        return env_key

    key_file = data_dir / "secret_key.txt"
    if key_file.exists():
        return key_file.read_text(encoding="utf-8").strip()

    generated = hashlib.sha256(os.urandom(64)).hexdigest()
    key_file.write_text(generated, encoding="utf-8")
    return generated


base_data_dir = Path(__file__).resolve().parent / "data" / "web"
base_data_dir.mkdir(parents=True, exist_ok=True)

# Stable secret key across restarts unless APP_SECRET_KEY is provided.
app.secret_key = _load_or_create_secret_key(base_data_dir)

# Initialize the IChingBot
bot = IChingBot(data_dir=base_data_dir)

@app.route('/')
async def index():
    """Render the main chat interface."""
    # Ensure the user has a unique ID in their session
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return await render_template('index.html')

@app.route('/chat', methods=['POST'])
async def chat():
    """Handle chat messages from the web interface."""
    data = await request.get_json(silent=True)
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400

    user_message = data['message']
    if not isinstance(user_message, str):
        return jsonify({'error': 'message must be a string'}), 400

    user_message = user_message.strip()
    if not user_message:
        return jsonify({'error': 'message cannot be empty'}), 400
    if len(user_message) > 500:
        return jsonify({'error': 'message is too long (max 500 chars)'}), 400

    # Simple session management (using Flask session)
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())

    user_id = session['user_id']

    # Process the message through the bot
    try:
        bot_response = await asyncio.to_thread(bot.chat, user_id, user_message)
    except Exception:
        return jsonify({'error': 'internal server error'}), 500
    
    # Format the response for HTML display (convert newlines to <br>)
    formatted_response = bot_response.replace('\n', '<br>')
    
    return jsonify({'response': formatted_response})

if __name__ == '__main__':
    # Quart dev server for local development; use Hypercorn/Uvicorn in production.
    debug_mode = os.getenv('APP_DEBUG', 'false').lower() == 'true'
    host = os.getenv('APP_HOST', '127.0.0.1')
    port = int(os.getenv('APP_PORT', '5000'))
    app.run(debug=debug_mode, host=host, port=port)
