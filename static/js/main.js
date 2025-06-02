document.addEventListener('DOMContentLoaded', function () {
    // General UI elements
    const serverStatusElement = document.getElementById('server-status');
    const startButton = document.getElementById('start-btn');
    const stopButton = document.getElementById('stop-btn');
    const restartButton = document.getElementById('restart-btn');
    const mainAlertPlaceholder = document.getElementById('alert-placeholder');

    // File Management UI elements
    const fileListContainer = document.getElementById('file-list-container');
    const currentPathElement = document.getElementById('current-path');
    const parentDirButton = document.getElementById('parent-dir-btn');
    const fileInput = document.getElementById('file-input');
    const uploadButton = document.getElementById('upload-btn');
    const fileAlertPlaceholder = document.getElementById('file-alert-placeholder');

    // Console UI elements
    const consoleOutputElement = document.getElementById('console-output');
    const consoleInputElement = document.getElementById('console-input');
    const sendCommandButton = document.getElementById('send-command-btn');

    // Backup UI elements
    const backupButton = document.getElementById('backup-btn');
    const backupAlertPlaceholder = document.getElementById('backup-alert-placeholder');

    let currentFilePath = ''; // Tracks the current path for file management
    let socket = null; // To be initialized after DOM load

    function showAlert(message, type = 'info', placeholder = mainAlertPlaceholder) {
        const wrapper = document.createElement('div');
        wrapper.innerHTML = [
            `<div class="alert alert-${type} alert-dismissible fade show" role="alert">`,
            `   <div>${message}</div>`,
            '   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
            '</div>'
        ].join('');
        
        // Clear previous alerts in the specified placeholder
        if (placeholder) {
            placeholder.innerHTML = ''; 
            placeholder.append(wrapper);
        } else {
            // Fallback if no placeholder is specified, though it's better to always specify
            mainAlertPlaceholder.innerHTML = '';
            mainAlertPlaceholder.append(wrapper);
        }
    }

    async function fetchServerStatus() {
        if (serverStatusElement) {
            serverStatusElement.textContent = 'Loading...';
            try {
                const response = await fetch('/api/server/status');
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                serverStatusElement.textContent = data.status || 'Unknown';
            } catch (error) {
                console.error('Error fetching server status:', error);
                serverStatusElement.textContent = 'Error';
                showAlert(`Could not fetch server status: ${error.message}`, 'danger', mainAlertPlaceholder);
            }
        }
    }

    async function controlServer(action) {
        const endpoint = `/api/server/${action}`;
        let userMessage = `Attempting to ${action} server...`;
        showAlert(userMessage, 'info', mainAlertPlaceholder);

        try {
            const response = await fetch(endpoint, { method: 'POST' });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || data.message || `Server returned status ${response.status}`);
            }
            
            userMessage = data.message || `${action.charAt(0).toUpperCase() + action.slice(1)} request sent successfully.`;
            showAlert(userMessage, 'success', mainAlertPlaceholder);
            
            setTimeout(fetchServerStatus, 2000); 

        } catch (error) {
            console.error(`Error during server ${action}:`, error);
            showAlert(`Failed to ${action} server: ${error.message}`, 'danger', mainAlertPlaceholder);
            fetchServerStatus(); 
        }
    }

    // --- File Management Functions ---

    function normalizePath(path) {
        // Replace backslashes with forward slashes and remove any trailing slash for consistency
        return path.replace(/\\/g, '/').replace(/\/$/, '');
    }
    
    async function fetchFileList(path = '') {
        currentFilePath = normalizePath(path);
        const requestPath = currentFilePath ? `/api/server/files/${currentFilePath}` : '/api/server/files';
        
        if (fileListContainer) fileListContainer.innerHTML = '<div class="list-group-item">Loading files...</div>';
        if (currentPathElement) currentPathElement.textContent = `/${currentFilePath}`;
        if (parentDirButton) parentDirButton.disabled = !currentFilePath;

        try {
            const response = await fetch(requestPath);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            renderFileList(data.files || []);
        } catch (error) {
            console.error('Error fetching file list:', error);
            if (fileListContainer) fileListContainer.innerHTML = `<div class="list-group-item list-group-item-danger">Error loading files: ${error.message}</div>`;
            showAlert(`Could not fetch file list for /${currentFilePath}: ${error.message}`, 'danger', fileAlertPlaceholder);
        }
    }

    function renderFileList(files) {
        if (!fileListContainer) return;
        fileListContainer.innerHTML = ''; // Clear previous list

        if (files.length === 0) {
            fileListContainer.innerHTML = '<div class="list-group-item">Directory is empty.</div>';
            return;
        }

        files.sort((a, b) => { // Sort: folders first, then alphabetically
            const isADir = a.endsWith('/');
            const isBDir = b.endsWith('/');
            if (isADir && !isBDir) return -1;
            if (!isADir && isBDir) return 1;
            return a.localeCompare(b);
        });

        files.forEach(item => {
            const isDirectory = item.endsWith('/');
            const itemName = isDirectory ? item.slice(0, -1) : item;
            const fullItemPath = currentFilePath ? `${currentFilePath}/${itemName}` : itemName;

            const itemElement = document.createElement('div');
            itemElement.className = 'list-group-item d-flex justify-content-between align-items-center';
            
            const nameSpan = document.createElement('span');
            nameSpan.textContent = itemName;
            if (isDirectory) {
                nameSpan.innerHTML = `📁 ${itemName}`; // Folder icon
                nameSpan.style.cursor = 'pointer';
                nameSpan.style.fontWeight = 'bold';
                nameSpan.onclick = () => fetchFileList(fullItemPath);
            } else {
                 nameSpan.innerHTML = `📄 ${itemName}`; // File icon
            }
            itemElement.appendChild(nameSpan);

            if (!isDirectory) {
                const downloadButton = document.createElement('button');
                downloadButton.className = 'btn btn-sm btn-outline-primary';
                downloadButton.textContent = 'Download';
                downloadButton.onclick = () => {
                    window.location.href = `/api/server/files/download/${fullItemPath}`;
                };
                itemElement.appendChild(downloadButton);
            }
            fileListContainer.appendChild(itemElement);
        });
    }

    async function uploadFile() {
        if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
            showAlert('Please select a file to upload.', 'warning', fileAlertPlaceholder);
            return;
        }
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);

        const uploadPath = currentFilePath ? `/api/server/files/upload/${currentFilePath}` : '/api/server/files/upload';
        showAlert(`Uploading ${file.name}...`, 'info', fileAlertPlaceholder);

        try {
            const response = await fetch(uploadPath, {
                method: 'POST',
                body: formData,
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || data.message || `Upload failed with status ${response.status}`);
            }
            showAlert(data.message || 'File uploaded successfully!', 'success', fileAlertPlaceholder);
            fetchFileList(currentFilePath); // Refresh file list
            fileInput.value = ''; // Clear the file input
        } catch (error) {
            console.error('Error uploading file:', error);
            showAlert(`Upload failed: ${error.message}`, 'danger', fileAlertPlaceholder);
        }
    }

    // Initial calls
    fetchServerStatus();
    fetchFileList(); // Load root directory files

    // Event Listeners for Server Controls
    if (startButton) startButton.addEventListener('click', () => controlServer('start'));
    if (stopButton) stopButton.addEventListener('click', () => controlServer('stop'));
    if (restartButton) restartButton.addEventListener('click', () => controlServer('restart'));
    
    // Event Listeners for File Management
    if (parentDirButton) {
        parentDirButton.addEventListener('click', () => {
            if (currentFilePath) {
                const parts = currentFilePath.split('/');
                parts.pop();
                fetchFileList(parts.join('/'));
            }
        });
    }
    if (uploadButton) uploadButton.addEventListener('click', uploadFile);
    
    // Make some functions globally available if needed
    window.fetchServerStatus = fetchServerStatus; 
    window.fetchFileList = fetchFileList; 

    // --- Socket.IO Console Functions ---
    function initializeSocketIO() {
        if (typeof io === "undefined") {
            console.error("Socket.IO client library not loaded.");
            showAlert("Error: Real-time console features are unavailable. Socket.IO library missing.", "danger", mainAlertPlaceholder);
            if(consoleOutputElement) consoleOutputElement.innerHTML = '<p class="text-danger">Console disabled: Socket.IO library failed to load.</p>';
            return;
        }

        socket = io('/console'); // Connect to the /console namespace

        socket.on('connect', () => {
            addLogMessage('Connected to server console.', 'system');
            socket.emit('request_initial_log');
        });

        socket.on('disconnect', () => {
            addLogMessage('Disconnected from server console. Attempting to reconnect...', 'system');
        });

        socket.on('console_log', (msg) => {
            if (msg && typeof msg.data !== 'undefined') {
                addLogMessage(msg.data);
            } else {
                // Handle cases where msg or msg.data might be undefined or not in expected format
                addLogMessage(JSON.stringify(msg), 'error'); // Log the raw message if format is unexpected
            }
        });

        socket.on('command_status', (msg) => {
             if (msg && typeof msg.data !== 'undefined') {
                addLogMessage(msg.data, 'system');
            } else {
                addLogMessage(JSON.stringify(msg), 'error');
            }
        });
        
        // Handle connection errors
        socket.on('connect_error', (error) => {
            addLogMessage(`Connection Error: ${error.message}`, 'error');
            console.error('Socket.IO connection error:', error);
        });
    }

    function addLogMessage(message, type = 'log') {
        if (!consoleOutputElement) return;

        const isScrolledToBottom = consoleOutputElement.scrollHeight - consoleOutputElement.clientHeight <= consoleOutputElement.scrollTop + 1;

        const messageElement = document.createElement('div'); // Using div for better block formatting
        messageElement.classList.add('console-message', `console-message-${type}`);
        
        // Sanitize message content before inserting to prevent XSS if messages could contain HTML
        // For now, assuming messages are plain text from server logs
        messageElement.textContent = message; 
        
        consoleOutputElement.appendChild(messageElement);

        if (isScrolledToBottom) {
            consoleOutputElement.scrollTop = consoleOutputElement.scrollHeight;
        }
    }

    function sendConsoleCommand() {
        if (!consoleInputElement || !socket || !socket.connected) {
             addLogMessage('Cannot send command: Not connected to console or input element missing.', 'error');
            return;
        }
        const command = consoleInputElement.value.trim();
        if (command) {
            // Optionally display command locally before sending, or wait for server echo if implemented
            // addLogMessage(`> ${command}`, 'user-command'); // Example of local echo
            socket.emit('send_command', { command: command });
            consoleInputElement.value = ''; // Clear input
        }
    }

    // Event listener for sending command via button
    if (sendCommandButton) {
        sendCommandButton.addEventListener('click', sendConsoleCommand);
    }

    // Event listener for sending command via Enter key in input field
    if (consoleInputElement) {
        consoleInputElement.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                sendConsoleCommand();
            }
        });
    }
    
    // Initialize Socket.IO after other initializations
    initializeSocketIO();

    // --- Backup Function ---
    async function createManualBackup() {
        if (!backupButton) return; // Should not happen if button exists

        showAlert('Starting manual backup...', 'info', backupAlertPlaceholder);
        backupButton.disabled = true;

        try {
            const response = await fetch('/api/server/backup/create', { method: 'POST' });
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || data.message || `Server returned status ${response.status}`);
            }
            
            showAlert(data.message || 'Backup request processed successfully.', 'success', backupAlertPlaceholder);

        } catch (error) {
            console.error('Error creating manual backup:', error);
            showAlert(`Backup failed: ${error.message}`, 'danger', backupAlertPlaceholder);
        } finally {
            backupButton.disabled = false;
        }
    }

    // Event Listener for Backup Button
    if (backupButton) {
        backupButton.addEventListener('click', createManualBackup);
    }

});
