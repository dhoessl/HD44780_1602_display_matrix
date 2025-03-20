from .LCD import LCD
from threading import Thread, Event
from queue import Queue
from time import sleep

# Example Dict
# display_data = [
#     {"location": (0, 0), "identifier": 0x20},
#     {"location": (1, 0), "identifier": 0x26}
# ]


class LCDMatrix:
    def __init__(self, display_data: list) -> None:
        """
            Create the Matrix.
            location must be a tuple with containing x, y of the display in
            the matrix. The identifier is the LCDs controll board identifier
        """
        self.displays = []
        self.get_displays(display_data)
        self.last_used = self.displays[0][0]

    def display_on_next(self, lines: list, data_id: str) -> None:
        """
            Display text on the next available display.
            If there is an display already got the same id then use it
            otherwise use the next unlocked display after the last used one
        """
        data_id_display = None
        next_display = None
        next_use = False
        for row in self.displays:
            for display in row:
                if not display:
                    # If on this spot there is no display set
                    # then check the next one display instead
                    continue
                if display.data_id == data_id:
                    data_id_display = display
                if next_use and not display.locked_display:
                    next_display = display
                    next_use = False
                if display == self.last_used:
                    next_use = True
        if not next_display and not data_id_display:
            # No active display to display data on
            # Just return and do not display the data
            return
        if data_id_display:
            # Display the text on the already used display
            data_id_display.set_text(line1=lines[0], line2=lines[1])
            return
        if next_display:
            # Display the text on the next available Display
            # set the correct data_id so it can be found again
            # set it as the last used one
            if not next_display.is_on():
                next_display.toggle_display()
            next_display.set_text(line1=lines[0], line2=lines[1])
            next_display.data_id = data_id
            self.last_used = next_display
            return

    def self_test(self) -> None:
        """ Selftesting
            Display Identifier on first line
            Display location on second lin
        """
        for row in self.displays:
            for display in row:
                if not display.is_on():
                    display.toggle_display()
                display.set_text(
                    line1=f"ID : {hex(display.identifier)}",
                    line2=f"Loc: {display.location}"
                )

    def get_displays(self, setup_data: list) -> None:
        """
            Init all displays. If there are spots without a display on the
            grid its value will be set to `None`.
        """
        for display in setup_data:
            if "identifier" not in display or "location" not in display:
                # NOTE: if identifier or location is missing just continue
                continue
            x, y = display["location"]
            while len(self.displays) < x + 1:
                self.displays.append([])
            while len(self.displays[x]) < y + 1:
                self.displays[x].append(None)
            self.displays[x][y] = Display(
                display["identifier"],
                display["location"],
            )

    def exit(self) -> None:
        for row in self.displays:
            for display in row:
                if display.is_on():
                    display.toggle_display()


class Display:
    def __init__(self, identifier: hex, location: tuple) -> None:
        """
            Creates the display.
            location and identifier is given by the matrix via user input.
            locked_display and data_id is used by the matrix to decide if it
            is the correct display to display text on.
            A msg queue and thread is created to deliver message in realtime to
            the board.
        """
        self.identifier = identifier
        self.location = location
        self.lcd = LCD(2, self.identifier, True)
        self.locked_display = False
        self.data_id = None
        self.msg_queue = Queue()
        self.thread = Thread(
            target=self.display_thread,
            args=()
        )
        self.thread_exit = Event()
        self.thread.start()

    def create_display(self) -> LCD:
        """ NOTE: currently not used"""
        if self.identifier not in list(range(0x20, 0x28)):
            return None
        return LCD(2, self.identifier, False)

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
        self.lcd = LCD(2, self.identifier, False)
        if self.is_on():
            self.thread_exit.set()

    def turn_on(self) -> None:
        """ Toggle display on by setting the Backlight to on and removing
            the Event Flag. Creating a thread to handle displaying data
        """
        if not self.is_on():
            self.lcd = LCD(2, self.identifier, True)
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

    def set_text(self, line1: str = None, line2: str = None) -> None:
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
            current_lines = ["", ""]
            if self.msg_queue.qsize() > 0:
                new_lines = self.msg_queue.get()
                if (new_lines[0] is not None
                        and current_lines[0] != new_lines[0]):
                    self.lcd.message(f"{new_lines[0]}", 1)
                    current_lines[0] = new_lines[0]
                if (new_lines[1] is not None
                        and current_lines[1] != new_lines[1]):
                    self.lcd.message(f"{new_lines[1]}", 2)
                    current_lines[1] = new_lines[1]
            else:
                sleep(.1)
