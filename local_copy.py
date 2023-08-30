
import argparse
import os
import shutil
import subprocess
from enum import Enum
import sys
from time import sleep

class FaultyCopyProcess(Exception):
    """Exception raised for errors of a faulty copy process.

    Attributes:
        pof -- point of failure where error was caused
        message -- explanation where error was thrown
    """
    def __init__(self, pof, message="Error thrown in ") -> None:
        self.salary = pof
        self.message = f"{message} {pof}"
        print(self.message)
        super().__init__(self.message)

class Constants(Enum):
    """
    Enum for local paths.
    """
    SRC_FOLDER = '/media/pi/'
    DEST_FOLDER = '/home/pi/Desktop/temp'
    SD_CARD_PATH = "/dev/sda1"
    TEMP_FOLDER = f"{SRC_FOLDER}TEMP"

class LcdScreen():
    """
    A class representing an LCD screen.

    Attributes:
        mylcd: An instance of the I2C_LCD_driver.lcd class.
    """
    def __init__(self, i2c_lcd_driver) -> None:
        """
        Initializes a new instance of the LcdScreen class.
        """
        if i2c_lcd_driver is not None:
            self.mylcd = i2c_lcd_driver.lcd()

    def clear(self) -> None:
        """
        Clears the contents of the LCD screen.
        """
        self.mylcd.lcd_clear()

    def wait(self, amount: int) -> None:
        """
        Waits a specific amount of time.
        """
        sleep(amount)

    def print_rows(self, *extra_args: str, row1: str = None, row2: str = None) -> None:
        """
        Prints text to the first and second rows of the LCD screen and to the console.

        Args:
            row1 (str):
                The text to be printed on the first row of the LCD screen. Defaults to None.
            row2 (str):
                The text to be printed on the second row of the LCD screen. Defaults to None.
            *extra_args (str):
                Additional text to be printed to the console.

        Returns:
            None
        """
        if row1 or row2:
            self.clear()
        if row1:
            self.mylcd.lcd_display_string(row1, 1)
        if row2:
            self.mylcd.lcd_display_string(row2, 2)
        console_print = " ".join(filter(None, [row1, row2, *extra_args]))
        if console_print:
            print(console_print)

class PrintScreen(LcdScreen):
    """
    A class representing a PrintScreen that inherits from LcdScreen.

    Attributes:
        None
    """
    def __init__(self) -> None:
        """
        Initializes a new instance of the PrintScreen class.
        """
        super().__init__(i2c_lcd_driver=None)

    def clear(self) -> None:
        """
        Clears the contents of the LCD screen.
        """
        print("clearing the lcd screen")

    def print_rows(self, *extra_args: str, row1: str = None, row2: str = None) -> None:
        """
        Prints text to the console.

        Args:
            row1 (str):
                The text to be printed on the first row of the console. Defaults to None.
            row2 (str):
                The text to be printed on the second row of the console. Defaults to None.
            *extra_args (str):
                Additional text to be printed to the console.

        Returns:
            None
        """
        if row1 or row2:
            self.clear()
        console_print = " ".join(filter(None, [row1, row2]))
        if extra_args:
            console_print += "\n"
            console_print += "\n".join(filter(None, [*extra_args]))
        if console_print:
            print(console_print)

def _format_sd_card(device_path: str, src_path: str, lcd_screen: LcdScreen) -> None:
    """
    Formats an SD card and mounts it to a specified folder.

    Args:
        device_path (str):
            The device path of the SD card to be formatted.
        src_folder (str):
            The path of the folder where the SD card will be mounted.

    Returns:
        bool:
            True if the SD card was successfully formatted and mounted, False otherwise.

    Raises:
        subprocess.CalledProcessError:
            If an error occurs while running a subprocess command.
    """
    try:
        subprocess.run(["sudo", "umount", device_path], check=True)
        subprocess.run(["sudo", "mkfs.vfat", "-F", "32", device_path], check=True)
        os.makedirs(src_path, exist_ok=True)
        subprocess.run(["sudo", "mount", device_path, src_path], check=True)
    except subprocess.CalledProcessError as err:
        lcd_screen.print_rows(row1="Formatieren", row2="fehlgeschlagen", *(err.args[0]))
        lcd_screen.wait(amount=2)
        lcd_screen.print_rows(
            row1="SD-Karte",
            row2="neu einstecken",
            *("Vorhandener Ordner wird gelöscht", "SD Karte muss erneut eingesteckt werden"))
        raise FaultyCopyProcess(pof="SD formatting") from err

def format_sd_card(device_path: str, src_path: str, lcd_screen: LcdScreen, dry_run: bool = False) -> bool:
    """
    Formats an SD card and displays status messages on an LCD screen.

    Args:
        device_path (str):
            The device path of the SD card to be formatted.
        src_path (str):
            The path of the source folder where it gets re-mounted after formatting.
        lcd_screen (LcdScreen):
            An instance of the LcdScreen class used to display status messages.

    Returns:
        bool:
            True if the SD card was successfully formatted, False otherwise.

    Raises:
        FaultyCopyProcess:
            If an error occurs while copying files or formatting the SD card.
    """
    if dry_run:
        print(f"device path {device_path}")
        print(f"source path {src_path}")
        lcd_screen.print_rows(row1="Dateien kopiert", row2="Formatiere...")
        lcd_screen.print_rows(row1="Karte formatiert")
        return True
    try:
        lcd_screen.print_rows(row1="Dateien kopiert", row2="Formatiere...")
        _format_sd_card(
            device_path=device_path,
            src_path=src_path,
            lcd_screen=lcd_screen)
        lcd_screen.print_rows(row1="Karte formatiert")
        lcd_screen.wait(amount=2)
        return True
    except FaultyCopyProcess as err:
        raise FaultyCopyProcess(pof=err.message) from err

def recursive_copy(src_folder: str, dest_path: str, dry_run: bool = False) -> None:
    """
    Recursively copies the contents of a source folder to a destination path.

    Args:
        src_folder (str):
            The path of the source folder whose contents are to be copied.
        dest_path (str):
            The path of the destination where the contents will be copied.

    Returns:
        tuple:
            A tuple containing a boolean value indicating whether the copy
            operation was successful, and an error message if an error occurred.

    Raises:
        FileNotFoundError:
            If the source folder or destination path do not exist.
        PermissionError:
            If the user does not have permission to access the
            source folder or destination path.
    """
    if dry_run:
        print(f"list dir of {src_folder}")
        print(f"copy files to {dest_path}")
        return
    try:
        for item in os.listdir(src_folder):
            dest_path_temp = dest_path
            source_path = os.path.join(src_folder, item)
            if os.path.isdir(source_path):
                recursive_copy(src_folder=source_path, dest_path=dest_path)
            else:
                dest_path_temp = os.path.join(dest_path, item)
                shutil.copy2(source_path, dest_path_temp)
    except (FileNotFoundError, PermissionError) as err:
        raise FaultyCopyProcess(pof=f'copy success verification. Error: {err.args[0]}') from err

def get_current_counter(folder: str, dry_run: bool = False) -> int:
    """
    Returns the current counter value based on the existing folders in the specified folder.
    Returns 1 if no folder exists matching the pattern.

    Args:
        folder (str):
        The path of the folder to search for existing folders.

    Returns:
        int: The current counter value.
    """
    if dry_run:
        return 1
    existing_folders = []
    for file in os.listdir(folder):
        if os.path.isdir(os.path.join(folder, file)) and file.startswith('SD_Karte_'):
            existing_folders.append(file)
    if existing_folders:
        return max((int(f.split('_')[-1]) for f in existing_folders)) + 1
    return 1

def main(dry_run: bool = False) -> None:
    """
    Main function.
    """
    if not dry_run:
        import I2C_LCD_driver
        lcd_screen = LcdScreen(i2c_lcd_driver=I2C_LCD_driver)
    else:
        lcd_screen = PrintScreen()
        lcd_screen.print_rows(row1="Bereit")
        lcd_screen.print_rows(row1="SD-Karte wird", row2="kopiert...")
        lcd_screen.print_rows(
            row1="SD-Karte",
            row2="neu einstecken",
            *("Vorhandener Ordner wird gelöscht", "SD Karte muss erneut eingesteckt werden"))
        lcd_screen.wait(amount=1)
        folder_name = f"SD_Karte_{(get_current_counter(folder=Constants.DEST_FOLDER.value, dry_run=dry_run))}"
        print(folder_name)
        dest_path = os.path.join(Constants.DEST_FOLDER.value, folder_name)
        print(dest_path)
        recursive_copy(src_folder=Constants.SRC_FOLDER.value, dest_path=dest_path, dry_run=dry_run)
        process_success = format_sd_card(
                device_path=Constants.SD_CARD_PATH.value,
                src_path=Constants.TEMP_FOLDER.value,
                lcd_screen=lcd_screen,
                dry_run=dry_run)
        print(process_success)
        lcd_screen.print_rows(row1="Vorgang", row2="erfolgreich")
        lcd_screen.print_rows(row1="SD-Karte", row2="entnehmen")

        sys.exit(0)

    while True:
        while not os.listdir(Constants.SRC_FOLDER.value):
            lcd_screen.print_rows(row1="Bereit")
            lcd_screen.wait(amount=1)

        process_success = False
        lcd_screen.print_rows(row1="SD-Karte wird", row2="kopiert...")
        folder_name = f"SD_Karte_{(get_current_counter(folder=Constants.DEST_FOLDER.value))}"
        dest_path = os.path.join(Constants.DEST_FOLDER.value, folder_name)
        try:
            os.makedirs(dest_path, exist_ok=True)
            recursive_copy(Constants.SRC_FOLDER.value, dest_path)

            process_success = format_sd_card(
                device_path=Constants.SD_CARD_PATH.value,
                src_path=Constants.TEMP_FOLDER.value,
                lcd_screen=lcd_screen)

            while os.path.exists(Constants.TEMP_FOLDER.value):
                lcd_screen.print_rows(row1="Vorgang", row2="erfolgreich")
                lcd_screen.wait(amount=3)
                lcd_screen.print_rows(row1="SD-Karte", row2="entnehmen")
                lcd_screen.wait(amount=3)
            lcd_screen.clear()

        except FaultyCopyProcess:
            while os.path.exists(Constants.SRC_FOLDER.value):
                lcd_screen.print_rows(row1="Kopieren", row2="fehlgeschlagen")
                lcd_screen.wait(amount=2)
                lcd_screen.print_rows(row1="Karte entfernen", row2="neu einstecken")
        finally:
            if not process_success:
                if os.path.exists(dest_path):
                    shutil.rmtree(dest_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry_run", type=bool, default=False)
    args = parser.parse_args()
    main(args.dry_run)
