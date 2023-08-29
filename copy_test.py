import os
import shutil
import I2C_LCD_driver
from time import *
import subprocess

def format_sd_card(device_path):
    try:
        subprocess.run(["sudo", "umount", device_path], check=True)
        subprocess.run(["sudo", "mkfs.vfat", "-F", "32", device_path], check=True)
        print("SD-Karte wurde erfolgreich formatiert.")
        return True
    except subprocess.CalledProcessError:
        return False

def recursive_copy(src_folder, dest_path):
    try:
        for item in os.listdir(src_folder):
            dest_path_temp = dest_path
            s = os.path.join(src_folder, item)
            print("source path")
            print(s)
            if os.path.isdir(s):
                print("sub-folder")
                recursive_copy(src_folder=s, dest_path=dest_path)
            else:
                dest_path_temp = os.path.join(dest_path, item)
                print("dest path to file")
                print(dest_path_temp)
                print("exists")
                print(os.path.exists(dest_path_temp))
                print("time")
                print(os.stat(s).st_mtime - os.stat(dest_path_temp).st_mtime > 1)
                if not os.path.exists(dest_path_temp) or os.stat(s).st_mtime - os.stat(dest_path_temp).st_mtime > 1:
                    print("copy")
                    shutil.copy2(s, dest_path_temp)
        return True, None
    except Exception as err:
        return False, err

def main():
    mylcd = I2C_LCD_driver.lcd()

    dest_folder = '/home/pi/temp'
    counter = 0
    if os.listdir('/media/pi'):
        print("SD-Karte wird kopiert...")
        mylcd.lcd_clear()
        mylcd.lcd_display_string("SD-Karte wird", 1)
        mylcd.lcd_display_string("kopiert...", 2)

        # Erstellen eines Ordners für die SD-Karte auf dem Desktop
        src_folder = '/media/pi/'
        dest_folder = '/home/pi/Desktop/temp/'

        # Erhöhe den Zähler um 1
        counter += 1
        folder_name = f"SD_Karte_{counter}"
        dest_path = os.path.join(dest_folder, folder_name)
        os.makedirs(dest_path, exist_ok=True)

        # Kopieren aller Dateien von der SD-Karte in den Ordner für diese SD-Karte
        copy_success = recursive_copy(src_folder, dest_path)

        if copy_success[0]:
            print("Alle Dateien erfolgreich kopiert, formatiere SD-Karte...")
            mylcd.lcd_clear()
            mylcd.lcd_display_string("Dateien okay,", 1)
            mylcd.lcd_display_string("formatiere Karte...", 2)
        else:
            print("Kopieren nicht erfolgreich, bitte Karte erneut einführen...")
            print(copy_success[1])
            mylcd.lcd_clear()
            mylcd.lcd_display_string("Kopieren fehlgeschlagen,", 1)
            mylcd.lcd_display_string("Karte erneut einführen...", 2)

if __name__ == "__main__":
    main()