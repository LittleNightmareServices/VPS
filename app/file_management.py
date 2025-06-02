import os
from werkzeug.utils import secure_filename

SERVER_FILES_ROOT = os.path.abspath("servers")

# Ensure the root directory for server files exists
os.makedirs(SERVER_FILES_ROOT, exist_ok=True)

def _get_safe_path(relative_path="."):
    """
    Resolves a relative path against SERVER_FILES_ROOT and ensures it's within it.
    Prevents directory traversal attacks.
    """
    # Normalize the path to remove '..' etc.
    normalized_relative_path = os.path.normpath(relative_path)

    # Ensure the normalized path doesn't try to go "up" from its initial components
    if os.path.isabs(normalized_relative_path) or normalized_relative_path.startswith(".."):
        return None

    # Join with the root and get the absolute path
    absolute_path = os.path.join(SERVER_FILES_ROOT, normalized_relative_path)
    
    # Final check to ensure the resolved path is still under SERVER_FILES_ROOT
    if os.path.commonprefix([os.path.abspath(absolute_path), SERVER_FILES_ROOT]) != SERVER_FILES_ROOT:
        return None
    return absolute_path

def list_files(directory_path="."):
    """
    Lists files and directories within the given relative path under SERVER_FILES_ROOT.
    """
    safe_dir_path = _get_safe_path(directory_path)
    if not safe_dir_path or not os.path.isdir(safe_dir_path):
        return None, "Path not found or access denied"

    try:
        items = []
        for item in os.listdir(safe_dir_path):
            if os.path.isdir(os.path.join(safe_dir_path, item)):
                items.append(item + "/")
            else:
                items.append(item)
        return items, None
    except OSError as e:
        return None, f"Error listing files: {e}"

def handle_file_upload(file_storage, save_path="."):
    """
    Saves an uploaded file to the specified relative path within SERVER_FILES_ROOT.
    """
    if not file_storage or not file_storage.filename:
        return False, "No file provided"

    filename = secure_filename(file_storage.filename)
    if not filename: # secure_filename might return empty if the original filename is dangerous
        return False, "Invalid filename"

    target_dir = _get_safe_path(save_path)
    if not target_dir or not os.path.isdir(target_dir): # Check if target_dir is a directory
        # Attempt to create if it's a path within SERVER_FILES_ROOT but doesn't exist
        if target_dir and SERVER_FILES_ROOT in target_dir:
            try:
                os.makedirs(target_dir, exist_ok=True)
            except OSError:
                 return False, "Could not create save directory"
        else:
            return False, "Invalid save path"
            
    # Further check: ensure target_dir is indeed a directory now
    if not os.path.isdir(target_dir):
        return False, "Save path is not a directory"

    try:
        file_path = os.path.join(target_dir, filename)
        # Additional check to prevent saving outside SERVER_FILES_ROOT, though _get_safe_path should handle most.
        if os.path.commonprefix([os.path.abspath(file_path), SERVER_FILES_ROOT]) != SERVER_FILES_ROOT:
            return False, "Attempted to save file outside designated area"
        
        file_storage.save(file_path)
        return True, "File uploaded successfully"
    except Exception as e:
        # Log the exception e
        return False, f"Error saving file: {e}"


def get_file_download_path(filepath):
    """
    Returns the absolute path to the file if it exists within SERVER_FILES_ROOT
    and is safe to download. Otherwise, returns None.
    """
    safe_file_path = _get_safe_path(filepath)

    if not safe_file_path or not os.path.isfile(safe_file_path):
        return None

    # Ensure the file is directly within SERVER_FILES_ROOT or its subdirectories
    # _get_safe_path already does this, but an explicit check on the result is good.
    if SERVER_FILES_ROOT != os.path.commonpath((SERVER_FILES_ROOT, os.path.abspath(safe_file_path))):
         return None

    return safe_file_path
