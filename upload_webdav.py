from enum import Enum
import os, errno
import sys
import shutil
import subprocess

# Definiere die Pfade
class Constants(Enum):
    LOCKFILE = '/tmp/webdav_sync.lock'
    TEMP_FOLDER = '/home/pi/Desktop/temp'
    WEBDAV_MOUNT_POINT = '/mnt/webdav'
    WEBDAV_SHARE_URL = 'https://webdav.example.com/share'
    WEBDAV_USERNAME = 'your_username'
    WEBDAV_PASSWORD = 'your_password'
    WEBDAV_AUTH = f'username={WEBDAV_USERNAME},password={WEBDAV_PASSWORD}'

try:
    # Überprüfe, ob das Skript bereits ausgeführt wird
    if os.path.exists(Constants.LOCKFILE.value):
        print("Das Skript wird bereits ausgeführt.")
        sys.exit(1)

    # Erstelle eine Lock-Datei, um zu verhindern, dass das Skript mehrmals gleichzeitig ausgeführt wird
    with open(Constants.LOCKFILE.value, 'w') as lock_file:
        lock_file.write(str(os.getpid()))

    # Mounte den WebDAV-Share
    mount_success = False
    try:
        subprocess.run(['sudo', 'mount', '-t', 'cifs', '-o', Constants.WEBDAV_AUTH.value, Constants.WEBDAV_SHARE_URL.value, Constants.WEBDAV_MOUNT_POINT.value])
        # FIXME nur weil der Code ausgeführt wurde und status 1 meldet heißt das nicht, dass das Mounting auch funktioniert hat :D
        mount_success = True
    except Exception as e:
        print("Fehler beim Mounten des WebDAV-Shares:", e)

    if mount_success:
        # Kopiere Dateien
        for item in os.listdir(Constants.TEMP_FOLDER.value):
            src_path = os.path.join(Constants.TEMP_FOLDER.value, item)
            dest_path = os.path.join(Constants.WEBDAV_MOUNT_POINT.value, item)
            if os.path.isfile(src_path) and not os.path.exists(dest_path):
                try:
                    shutil.copy2(src_path, dest_path)
                    print(f"Datei {item} kopiert.")
                except Exception as e:
                    # TODO Dateien sammeln und in der Exception (Zeile 60) in einen backup Folder kopieren
                    # beim nächsten Durchlauf des Skripts diese Dateien dann ebenfalls kopieren
                    print(f"Fehler beim Kopieren von {item}:", e)

        # Bereinige den temporären Ordner
        for item in os.listdir(Constants.TEMP_FOLDER.value):
            item_path = os.path.join(Constants.TEMP_FOLDER.value, item)
            if os.path.isfile(item_path):
                os.remove(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)

        # Trenne den WebDAV-Share
        subprocess.run(['sudo', 'umount', Constants.WEBDAV_MOUNT_POINT.value])

except Exception as err:
    print(f"Es gab einem Fehler beim Ausführen des Programms: {err}")

# Dieser Codeblock wird immer ausgeführt, ob das Programm vorher crasht oder nicht
finally:
    try:
        # löscht die lock Datei
        os.remove(Constants.LOCKFILE.value)
    except OSError as err:
        # Datei/ordner existiert nicht (enoent)
        if e.errno != errno.ENOENT:
            # raise bei einem anderen OSError
            raise
