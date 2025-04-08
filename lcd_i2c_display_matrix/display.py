from .LCD import LCD
from threading import Thread, Event
from queue import Queue
from time import sleep


class LCDIdentifierDoesNotExist(Exception):
    def __init__(self, *args) -> None:
        if args:
            self.identifier = args[0]
        else:
            self.identifier = None

    def __str__(self) -> str:
        if self.identifier:
            return f"LCD Display with Identifier {self.identifier} " \
                    "was not found!"
        else:
            return "LCD Display Identifier Error"


class LCDUnkownError(Exception):
    def __init__(self, *args) -> None:
        if args:
            self.msg = args[0]
            self.execption = args[1]
        else:
            self.msg = None

    def __str__(self) -> str:
        if self.msg:
            return f"Unkown Exeception: {self.msg}\n{self.exception}"
        else:
            return "Unkown Exception"


class Display:
    def __init__(self, identifier: hex) -> None:
        """
            Creates the display.
            location and identifier is given by the matrix via user input.
            locked_display and data_id is used by the matrix to decide if it
            is the correct display to display text on.
            A msg queue and thread is created to deliver message in realtime to
            the board.
        """
        self.identifier = identifier
        self.lcd = self.create_lcd()
        self.locked = False
        self.data_id = None
        self.current_lines = ["", ""]
        self.msg_queue = Queue()
        self.thread = Thread(
            target=self.display_thread,
            args=()
        )
        self.thread_exit = Event()
        self.thread.start()

    def create_lcd(self) -> LCD:
        try:
            lcd = LCD(2, self.identifier, True)
            return lcd
        except OSError as e:
            if e.errno == 5:
                raise LCDIdentifierDoesNotExist(self.identifier)
            else:
                raise LCDUnkownError("Display Create", e)

    def is_on(self) -> bool:
        """ Check if the Event flag is set"""
        if self.thread_exit.is_set():
            return False
        return True

    def toggle_display(self) -> None:
        """Toggle display on/off depending on the current state"""
        if self.is_on():
            self.turn_off()
        else:
            self.turn_on()

    def turn_off(self) -> None:
        """ Toggle display off by setting Backlight off and setting the
            Event flag """
        self.lcd = self.create_lcd()
        if self.is_on():
            self.thread_exit.set()

    def turn_on(self) -> None:
        """ Toggle display on by setting the Backlight to on and removing
            the Event Flag. Creating a thread to handle displaying data
        """
        if not self.is_on():
            self.lcd = self.create_lcd()
            self.thread_exit.clear()
            self.thread = Thread(
                target=self.display_thread,
                args=()
            )
            self.thread.start()

    def set_long_line(self, text) -> None:
        """ Split a long line into 2 parts containing 16 chars.
            All chars beyond 32 will be removed
        """
        self.set_text(line1=text[:16], line2=text[16:32])

    def set_text(self, line1: str, line2: str) -> None:
        """ Remove all current data from the message queue.
            Adding the new data to the queue.
        """
        while self.msg_queue.qsize() > 0:
            self.msg_queue.get()
        self.msg_queue.put([
            f"{line1}",
            f"{line2}"
        ])

    def set_line(self, text: str, line: int = 1) -> None:
        """ If there is the need to just modify one line of a display
            this function will deliver the correct line to the set_text
            function.
        """
        if line not in [1, 2]:
            return
        if line == 1:
            self.set_text(line1=text, line2=None)
        else:
            self.set_text(line1=None, line2=text)

    def display_thread(self) -> None:
        """ Thread to set the text of a display.
            It takes some time to display the text to the display.
            So while the data is printed new text may be added to the queue.
            The thread picks it up and displays it after finishing displaying
            the previous text.
        """
        while not self.thread_exit.is_set():
            if self.msg_queue.qsize() > 0:
                new_lines = self.msg_queue.get()
                if (new_lines[0] is not None
                        and self.current_lines[0] != new_lines[0]):
                    self.lcd.message(f"{new_lines[0]}", 1)
                    self.current_lines[0] = new_lines[0]
                if (new_lines[1] is not None
                        and self.current_lines[1] != new_lines[1]):
                    self.lcd.message(f"{new_lines[1]}", 2)
                    self.current_lines[1] = new_lines[1]
            else:
                sleep(.1)
