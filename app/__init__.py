import os
from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)

# Configure UPLOAD_FOLDER. This should align with SERVER_FILES_ROOT in file_management.py
# Ensure it's an absolute path.
app.config['UPLOAD_FOLDER'] = os.path.abspath("servers")
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize SocketIO
# We use eventlet as the async mode, ensure it's installed (added to requirements.txt)
socketio = SocketIO(app, async_mode='eventlet')

# Import routes after app initialization to avoid circular imports
# This is important as routes might import 'socketio' from here.
from app import routes
