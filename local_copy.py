import os
import shutil
import I2C_LCD_driver
from time import *
import subprocess

def recursive_copy(src_folder, dest_path):
    try:
        for item in os.listdir(src_folder):
            dest_path_temp = dest_path
            s = os.path.join(src_folder, item)
            if os.path.isdir(s):
                recursive_copy(src_folder=s, dest_path=dest_path)
            else:
                dest_path_temp = os.path.join(dest_path, item)
                if not os.path.exists(dest_path_temp) or os.stat(s).st_mtime - os.stat(dest_path_temp).st_mtime > 1:
                    shutil.copy2(s, dest_path_temp)
        return True, None
    except Exception as err:
        return False, err

def main():
    mylcd = I2C_LCD_driver.lcd()

    # Durchsuche den Ordner "SD_Karten_Backup" nach vorhandenen Ordnern und ermittle den höchsten Counter
    dest_folder = '/home/pi/temp'
    existing_folders = [f for f in os.listdir(dest_folder) if os.path.isdir(os.path.join(dest_folder, f)) and f.startswith('SD_Karte_')]
    if existing_folders:
        counter = max([int(f.split('_')[-1]) for f in existing_folders])
    else:
        counter = 0

    while True:
        # Überprüfen, ob eine SD-Karte eingesteckt ist und Dateien enthält
            if os.listdir('/media/pi'):
                try:
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

                    process_success = False

                    # Kopieren aller Dateien von der SD-Karte in den Ordner für diese SD-Karte
                    copy_success = recursive_copy(src_folder, dest_path)

                    if copy_success[0]:
                        print("Alle Dateien erfolgreich kopiert, formatiere SD-Karte...")
                        mylcd.lcd_clear()
                        mylcd.lcd_display_string("Dateien okay,", 1)
                        mylcd.lcd_display_string("formatiere Karte...", 2)

                        try:
                            for item in os.listdir(src_folder):
                                item_path = os.path.join(src_folder, item)
                                try:
                                    os.remove(item_path)
                                except OSError:
                                    shutil.rmtree(item_path)

                            print("SD-Karte erfolgreich formatiert.")
                            mylcd.lcd_clear()
                            mylcd.lcd_display_string("Karte formatiert!", 1)
                            mylcd.lcd_display_string("Bereit", 2)
                            process_success = True
                        except Exception as err:
                            print(err)
                            mylcd.lcd_clear()
                            mylcd.lcd_display_string("Formatieren fehlgeschlagen!", 1)
                            mylcd.lcd_display_string("Bereit", 2)

                    else:
                        print("Kopieren nicht erfolgreich, bitte Karte erneut einführen...")
                        print(copy_success[1])
                        mylcd.lcd_clear()
                        mylcd.lcd_display_string("Kopieren fehlgeschlagen,", 1)
                        mylcd.lcd_display_string("Karte erneut einführen...", 2)
                except Exception as err:
                    print("Etwas ist schiefgelaufen")

                finally:
                    if not process_success:
                        # Wiederherstellen der ursprünglichen Ordnung (falls benötigt)
                        if os.path.exists(dest_path):
                            shutil.rmtree(dest_path)
            else:
                print("Bereit")
                mylcd.lcd_display_string("Bereit", 1)
                sleep(1)
                mylcd.lcd_clear()

if __name__ == "__main__":
    main()