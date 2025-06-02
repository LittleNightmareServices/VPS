from flask import jsonify, request, send_from_directory, render_template # Added render_template
from app import app, socketio # Import socketio
from flask_socketio import emit # For emitting SocketIO messages
import os # For send_from_directory path manipulation

# Import file management functions
from app.file_management import list_files, handle_file_upload, get_file_download_path, SERVER_FILES_ROOT

# Import server management functions
from app.server_management import (
    start_minecraft_server,
    stop_minecraft_server,
    restart_minecraft_server,
    get_minecraft_server_status,
    send_command_to_server,
    get_server_log_realtime, # Though not fully implemented, good to have for structure
    get_historical_logs
)

# Import backup management functions
from app.backup_management import create_manual_backup


# +++++ Frontend Routes +++++

@app.route('/')
def index_route():
    return render_template('index.html')

# +++++ File Management API Endpoints +++++

@app.route('/api/server/files', defaults={'subpath': '.'}, methods=['GET'])
@app.route('/api/server/files/<path:subpath>', methods=['GET'])
def list_server_files_route(subpath):
    files, error = list_files(subpath)
    if error:
        return jsonify({"error": error}), 400 if "Path not found" in error else 500
    return jsonify({"files": files}), 200

@app.route('/api/server/files/upload', defaults={'subpath': '.'}, methods=['POST'])
@app.route('/api/server/files/upload/<path:subpath>', methods=['POST'])
def upload_server_file_route(subpath):
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    success, message = handle_file_upload(file, save_path=subpath)
    if success:
        return jsonify({"message": message}), 201
    else:
        return jsonify({"error": message}), 500

@app.route('/api/server/files/download/<path:filepath>', methods=['GET'])
def download_server_file_route(filepath):
    absolute_path = get_file_download_path(filepath)
    if not absolute_path:
        return jsonify({"error": "File not found or access denied"}), 404

    try:
        # send_from_directory needs the directory and the filename separately
        directory = os.path.dirname(absolute_path)
        filename = os.path.basename(absolute_path)
        return send_from_directory(directory, filename, as_attachment=True)
    except Exception as e:
        # Log error e
        return jsonify({"error": "Could not send file"}), 500

# +++++ Server Management API Endpoints +++++

@app.route('/api/server/start', methods=['POST'])
def start_server_route():
    success = start_minecraft_server()
    if success:
        return jsonify({"message": "Server starting..."}), 202
    else:
        return jsonify({"message": "Failed to start server"}), 500


@app.route('/api/server/stop', methods=['POST'])
def stop_server_route():
    success = stop_minecraft_server()
    if success:
        return jsonify({"message": "Server stopping..."}), 202
    else:
        return jsonify({"message": "Failed to stop server"}), 500


@app.route('/api/server/restart', methods=['POST'])
def restart_server_route():
    success = restart_minecraft_server()
    if success:
        return jsonify({"message": "Server restarting..."}), 202
    else:
        return jsonify({"message": "Failed to restart server"}), 500


@app.route('/api/server/status', methods=['GET'])
def status_server_route():
    status = get_minecraft_server_status()
    return jsonify({"status": status}), 200

# +++++ Backup Management API Endpoints +++++

@app.route('/api/server/backup/create', methods=['POST'])
def create_backup_route():
    success, message = create_manual_backup()
    if success:
        # Message from create_manual_backup typically is "Backup created successfully: <filename>"
        return jsonify({"message": message}), 201
    else:
        # Message here would be the error reason
        return jsonify({"error": f"Failed to create backup: {message}"}), 500

# +++++ SocketIO Event Handlers for Console +++++

@socketio.on('connect', namespace='/console')
def handle_console_connect():
    print("Client connected to /console")
    # For now, just emit a welcome. Real log streaming would be more complex.
    emit('console_log', {'data': 'Connected to server console.'})
    # Call get_server_log_realtime if you want to start streaming logs immediately
    # For example, one might pass a lambda that emits:
    # get_server_log_realtime(lambda log_line: socketio.emit('console_log', {'data': log_line}, namespace='/console'))


@socketio.on('disconnect', namespace='/console')
def handle_console_disconnect():
    print("Client disconnected from /console")


@socketio.on('send_command', namespace='/console')
def handle_send_command(data):
    command = data.get('command')
    if command:
        print(f"Received command via SocketIO: {command}")
        # In a real implementation, this would interact with the server process
        response = send_command_to_server(command)
        emit('command_status', {'data': response}) # Or {'status': 'success/failure', 'message': ...}
        # Potentially also emit the command to the console_log if the server echoes commands
        emit('console_log', {'data': f"> {command}"}) # Simulate command echo
    else:
        emit('command_status', {'data': 'Error: No command provided'})

@socketio.on('request_initial_log', namespace='/console')
def handle_request_initial_log():
    print("Client requested initial logs for /console")
    historical_logs = get_historical_logs()
    emit('console_log', {'data': historical_logs if historical_logs else 'No historical logs available.'})
