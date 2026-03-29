from flask import Flask, render_template, request, jsonify, session
try:
    from .iching import IChingBot
except ImportError:
    from iching import IChingBot
import uuid
import os

# Initialize Flask app
app = Flask(__name__)
# Secure secret key for session management
app.secret_key = os.urandom(24)

# Initialize the IChingBot
bot = IChingBot()

@app.route('/')
def index():
    """Render the main chat interface."""
    # Ensure the user has a unique ID in their session
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages from the web interface."""
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400

    user_message = data['message']
    
    # Simple session management (using Flask session)
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    
    user_id = session['user_id']

    # Process the message through the bot
    bot_response = bot.chat(user_id, user_message)
    
    # Format the response for HTML display (convert newlines to <br>)
    formatted_response = bot_response.replace('\n', '<br>')
    
    return jsonify({'response': formatted_response})

if __name__ == '__main__':
    # Run the Flask app
    # Host='0.0.0.0' allows external access if running on a server
    # Remember to set a proper secret key in production
    app.config['SESSION_TYPE'] = 'filesystem' 
    app.run(debug=True, host='0.0.0.0', port=5000)
