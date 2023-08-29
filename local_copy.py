from enum import Enum
import os
import shutil
import I2C_LCD_driver
from time import sleep
import subprocess

class Constants(Enum):
    SRC_FOLDER = '/media/pi/'
    DEST_FOLDER = '/home/pi/Desktop/temp'
    SD_CARD_PATH = "/dev/sda1"
    TEMP_FOLDER = f"{SRC_FOLDER}TEMP"

def format_sd_card(device_path, src_folder):
    try:
        subprocess.run(["sudo", "umount", device_path], check=True)
        subprocess.run(["sudo", "mkfs.vfat", "-F", "32", device_path], check=True)
        os.makedirs(src_folder, exist_ok=True)
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
        return False, err.args[0]

class LcdScreen():
    def __init__(self) -> None:
        self.mylcd = I2C_LCD_driver.lcd()

    def clear(self):
        self.mylcd.lcd_clear()

    def print_rows(self, row1: str = None, row2: str = None, *extra_args: str):
        if row1 or row2:
            self.clear()
        if row1:
            self.mylcd.lcd_display_string(row1, 1)
        if row2:
            self.mylcd.lcd_display_string(row2, 2)
        console_print = " ".join(filter(None, [row1, row2, *extra_args]))
        if console_print:
            print(console_print)

def main():
    lcd_screen = LcdScreen()
    while True:
        if os.listdir(Constants.SRC_FOLDER.value):
            try:
                lcd_screen.print_rows(row1="SD-Karte wird", row2="kopiert...")

                existing_folders = [f for f in os.listdir(Constants.DEST_FOLDER.value) if os.path.isdir(os.path.join(Constants.DEST_FOLDER.value, f)) and f.startswith('SD_Karte_')]
                if existing_folders:
                    counter = max([int(f.split('_')[-1]) for f in existing_folders]) + 1
                else:
                    counter = 1
                folder_name = f"SD_Karte_{counter}"
                dest_path = os.path.join(Constants.DEST_FOLDER.value, folder_name)
                os.makedirs(dest_path, exist_ok=True)

                process_success = False
                copy_success = recursive_copy(Constants.SRC_FOLDER.value, dest_path)

                if copy_success[0]:
                    lcd_screen.print_rows(row1="Dateien kopiert", row2="Formatiere...")

                    try:

                        if format_sd_card(Constants.SD_CARD_PATH.value, Constants.TEMP_FOLDER.value):
                            lcd_screen.print_rows(row1="Karte formatiert")
                            process_success = True
                            sleep(2)
                            while os.path.exists(Constants.TEMP_FOLDER.value):
                                lcd_screen.print_rows(row1="Vorgang", row2="erfolgreich")
                                sleep(3)
                                lcd_screen.print_rows(row1="SD-Karte", row2="entnehmen")
                                sleep(3)
                            lcd_screen.clear()
                        else:
                            raise Exception

                    except Exception as err:
                        lcd_screen.print_rows(row1="Formatieren", row2="fehlgeschlagen", *(err.args[0]))
                        sleep(2)
                        lcd_screen.print_rows(row1="SD-Karte", row2="neu einstecken", *("Vorhandener Ordner wird gelöscht", "SD Karte muss erneut eingesteckt werden"))

                else:
                    while os.path.exists(Constants.SRC_FOLDER.value):
                        lcd_screen.print_rows(row1="Kopieren", row2="fehlgeschlagen")
                        sleep(2)
                        lcd_screen.print_rows(row1="Karte entfernen", row2="neu einstecken", *(copy_success[1]))

            except Exception as err:
                while os.path.exists(Constants.SRC_FOLDER.value):
                    lcd_screen.print_rows(row1="Fehler", row2="neu einstecken", *(copy_success[1]))

            finally:
                if not process_success:
                    if os.path.exists(dest_path):
                        shutil.rmtree(dest_path)
        else:
            lcd_screen.print_rows(row1="Bereit")
            sleep(1)

if __name__ == "__main__":
    main()
