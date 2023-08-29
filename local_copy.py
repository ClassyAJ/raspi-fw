import os
import shutil
import I2C_LCD_driver
from time import *
import subprocess

def format_sd_card(device_path, src_folder):
    try:
        subprocess.run(["sudo", "umount", device_path], check=True)
        subprocess.run(["sudo", "mkfs.vfat", "-F", "32", device_path], check=True)
        subprocess.run(["sudo", "mkdir", src_folder, ], check=True)
        subprocess.run(["sudo", "mount", device_path, src_folder], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def recursive_copy(src_folder, dest_path):
    try:
        for item in os.listdir(src_folder):
            dest_path_temp = dest_path
            s = os.path.join(src_folder, item)
            if os.path.isdir(s):
                recursive_copy(src_folder=s, dest_path=dest_path)
            else:
                dest_path_temp = os.path.join(dest_path, item)
                shutil.copy2(s, dest_path_temp)
        return True, None
    except Exception as err:
        return False, err

def main():
    mylcd = I2C_LCD_driver.lcd()
    dest_folder = '/home/pi/Desktop/temp'
    sd_card_path = "/dev/sda1"

    while True:
            if os.listdir('/media/pi'):
                try:
                    print("SD-Karte wird kopiert...")
                    mylcd.lcd_clear()
                    mylcd.lcd_display_string("SD-Karte wird", 1)
                    mylcd.lcd_display_string("kopiert...", 2)

                    src_folder = '/media/pi/'

                    existing_folders = [f for f in os.listdir(dest_folder) if os.path.isdir(os.path.join(dest_folder, f)) and f.startswith('SD_Karte_')]
                    if existing_folders:
                        counter = max([int(f.split('_')[-1]) for f in existing_folders]) + 1
                    else:
                        counter = 1
                    folder_name = f"SD_Karte_{counter}"
                    dest_path = os.path.join(dest_folder, folder_name)
                    os.makedirs(dest_path, exist_ok=True)

                    process_success = False
                    copy_success = recursive_copy(src_folder, dest_path)

                    if copy_success[0]:
                        print("Alle Dateien erfolgreich kopiert, formatiere SD-Karte...")
                        mylcd.lcd_clear()
                        mylcd.lcd_display_string("Dateien okay,", 1)
                        mylcd.lcd_display_string("formatiere Karte...", 2)
                        temp_folder = f"{src_folder}TEMP"

                        try:
                            if format_sd_card(sd_card_path, temp_folder):
                                print("SD-Karte erfolgreich formatiert.")
                                mylcd.lcd_clear()
                                mylcd.lcd_display_string("Karte formatiert!", 1)
                                mylcd.lcd_display_string("Bereit", 2)
                                process_success = True

                                while os.path.exists(temp_folder):
                                    mylcd.lcd_clear()
                                    mylcd.lcd_display_string("Vorgang", 1)
                                    mylcd.lcd_display_string("erfolgreich", 2)
                                    sleep(4)
                                    mylcd.lcd_clear()
                                    mylcd.lcd_display_string("SD-Karte", 1)
                                    mylcd.lcd_display_string("entnehmen", 2)
                                    sleep(4)
                                mylcd.lcd_clear()

                            else:
                                mylcd.lcd_clear()
                                mylcd.lcd_display_string("Formatieren fehlgeschlagen!", 1)
                                mylcd.lcd_display_string("neu einstecken", 2)
                                print("Vorhandener Ordner wird gelöscht")
                                print("SD Karte muss erneut eingesteckt werden")
                        except Exception as err:
                            print(err)
                            mylcd.lcd_clear()
                            mylcd.lcd_display_string("Formatieren fehlgeschlagen!", 1)
                            mylcd.lcd_display_string("neu einstecken", 2)

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
                        if os.path.exists(dest_path):
                            shutil.rmtree(dest_path)
            else:
                print("Bereit")
                mylcd.lcd_display_string("Bereit", 1)
                sleep(1)
                mylcd.lcd_clear()

if __name__ == "__main__":
    main()