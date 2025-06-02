from app import app, socketio # Import socketio

if __name__ == '__main__':
    # Use socketio.run to enable WebSocket support along with the Flask dev server.
    # The host and port are specified here. Eventlet will be used as per async_mode in __init__.py.
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
