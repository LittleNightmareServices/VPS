import os
import zipfile
import datetime

# Define paths
# BACKUPS_DIR is relative to the project root (where run.py is)
BACKUPS_DIR = os.path.abspath("backups")
# SERVER_FILES_TO_BACKUP_DIR is also relative to the project root
SERVER_FILES_TO_BACKUP_DIR = os.path.abspath("servers")

def create_manual_backup():
    """
    Creates a zip archive of the SERVER_FILES_TO_BACKUP_DIR and stores it in BACKUPS_DIR.
    Returns:
        (bool, str): Tuple of (success_status, message)
    """
    try:
        # Check if the directory to backup exists
        if not os.path.isdir(SERVER_FILES_TO_BACKUP_DIR):
            return False, f"Server directory '{SERVER_FILES_TO_BACKUP_DIR}' not found."

        # Check if there's anything to backup (optional, but good to avoid empty backups)
        if not os.listdir(SERVER_FILES_TO_BACKUP_DIR):
            return False, f"Server directory '{SERVER_FILES_TO_BACKUP_DIR}' is empty. No backup created."

        # Create the backups directory if it doesn't exist
        os.makedirs(BACKUPS_DIR, exist_ok=True)

        # Generate a filename for the backup
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"backup_{timestamp}.zip"
        backup_filepath = os.path.join(BACKUPS_DIR, backup_filename)

        # Create a zip archive
        with zipfile.ZipFile(backup_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(SERVER_FILES_TO_BACKUP_DIR):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Arcname is the path inside the zip file
                    # This makes sure files are stored with paths relative to SERVER_FILES_TO_BACKUP_DIR
                    arcname = os.path.relpath(file_path, SERVER_FILES_TO_BACKUP_DIR)
                    zipf.write(file_path, arcname)
                # Optionally, add empty directories if desired (usually not necessary for server files)
                # for dir_name in dirs:
                #     dir_path = os.path.join(root, dir_name)
                #     arcname = os.path.relpath(dir_path, SERVER_FILES_TO_BACKUP_DIR)
                #     # Create an empty directory entry in zip
                #     zipf.writestr(zipfile.ZipInfo(arcname + "/"), "")


        return True, f"Backup created successfully: {backup_filename}"

    except Exception as e:
        # Log the exception e for server-side diagnostics
        print(f"Error during backup creation: {e}")
        return False, f"Failed to create backup: {e}"

if __name__ == '__main__':
    # Quick test (assuming you have a 'servers' directory with some files)
    # Create dummy server files for testing
    if not os.path.exists(SERVER_FILES_TO_BACKUP_DIR):
        os.makedirs(SERVER_FILES_TO_BACKUP_DIR)
    with open(os.path.join(SERVER_FILES_TO_BACKUP_DIR, "test_server_file.txt"), "w") as f:
        f.write("This is a test file for backup.")
    
    success, message = create_manual_backup()
    print(f"Success: {success}, Message: {message}")
    # Check if backup zip exists in "backups" directory
    if success:
        backup_file_path_to_check = os.path.join(BACKUPS_DIR, message.split(": ")[1])
        print(f"Backup file created at: {backup_file_path_to_check}")
        print(f"Does it exist? {os.path.exists(backup_file_path_to_check)}")
