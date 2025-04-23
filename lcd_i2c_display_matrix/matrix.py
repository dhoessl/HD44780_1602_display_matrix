from .display import Display, LCDIdentifierDoesNotExist

# Example Dict
# display_data = [
#     {"location": (0, 0), "identifier": 0x20},
#     {"location": (1, 0), "identifier": 0x26}
# ]


class DisplayIndexError(Exception):
    def __init__(self, *args) -> None:
        if args:
            self.index = args[0]
            self.len_displays = args[1]
        else:
            self.index = None

    def __str__(self) -> str:
        if self.index:
            return f"{self.index} is not 0 - {self.len_displays}"
        else:
            return "Index is not in the list of Displays"


class DisplayDataIdError(Exception):
    def __init__(self, *args) -> None:
        if args:
            self.id = args[0]
        else:
            self.id = None

    def __str__(self) -> str:
        return f"Display ID {self.id if self.id else ''} was not " \
                "found in active displays"


class Matrix:
    def __init__(self, identifiers: list = None) -> None:
        self.displays = []
        self.create_displays(identifiers)
        self.last_used = -1

    def create_displays(self, identifiers: list) -> None:
        """ Creates all displays provided in the identifiers list. """
        for identifier in identifiers:
            try:
                self.displays.append(Display(identifier))
            except LCDIdentifierDoesNotExist:
                print(
                    f"Identifier {identifier} is not a valid identifier!"
                    "Skipping this display"
                )

    def exit(self) -> None:
        """ Turns of Backlight for every display. """
        for display in self.displays:
            if display.is_on():
                display.toggle_display()

    def self_test(self) -> None:
        """ Displays Identifier and position in list for every display. """
        for display in self.displays:
            if not display.is_on():
                continue
            display.set_text(
                f"ID:    {hex(display.identifier)}",
                f"Index: {self.displays.index(display)}"
            )

    def find_data_id_display(self, id) -> Display:
        """ search self.displays for a display with the set id as data_id. """
        for display in self.displays:
            if display.data_id == id:
                return display
        return None

    def display_on_id(self, lines: list, data_id: str) -> bool:
        """ Displays some text on a display using the data_id and the provided
            lines list [line1, line2]
        """
        id_display = self.find_data_id_display(data_id)
        if id_display:
            id_display.set_text(lines[0], lines[1])
            return True
        return False

    def find_next_free_display(self) -> Display:
        """ Search self.display for the next unlocked display """
        displays_to_check = list(range(self.last_used + 1, len(self.displays)))
        displays_to_check += list(range(0, self.last_used + 1))
        for index in displays_to_check:
            if self.displays[index].locked:
                continue
            return self.displays[index]
        return None

    def display_on_next(self, lines: list, data_id: str) -> None:
        """ Displays some text provided by lines [line1, line2]. """
        next_display = self.find_next_free_display()
        if not next_display:
            # No unlocked active display found
            # Return without displaying the data
            return
        if not next_display.is_on():
            next_display.toggle_display()
        next_display.set_text(lines[0], lines[1])
        next_display.data_id = data_id
        self.last_used = self.displays.index(next_display)

    def display_on_next_or_id(self, lines: list, data_id) -> None:
        """ Tries to write data on a display with the provided data_id.
            If the display does not exist, then the next unlocked display is
            searched and written on
        """
        if self.display_on_id(lines, data_id):
            return
        self.display_on_next(lines, data_id)

    def lock_display(self, index: int = None, id: str = None) -> None:
        """ Locks a display specified by data_id or the index in the list.
            This class might just write on the locked displays if providing
            the exact data_id
        """
        display = None
        if id:
            display = self.find_data_id_display(id)
        elif index and index in range(len(self.displays)):
            display = self.displays[index]
        if not display or display.locked:
            return
        display.locked = True

    def unlock_display(self, index: int = None, id: str = None) -> None:
        """ Unlocks previously locked display.
            Can be unlocked using data_id or the index of the display
            in the self.displays list
        """
        display = None
        if id:
            display = self.find_data_id_display(id)
        elif index and index in range(len(self.displays)):
            display = self.displays[index]
        if not display or not display.locked:
            return
        display.locked = False

    def display_and_shift(self, lines: list, id: str = None) -> None:
        """ Add new text to the first display which is not a maintainance
            or locked display.
            All displays will be shifted by one.
        """
        for display in self.displays:
            if display.data_id == "maintainance" or display.locked:
                continue
            old_lines = display.current_lines
            if not display.is_on():
                display.toggle_display()
            old_id = display.data_id
            display.set_text(lines[0], lines[1])
            display.data_id = id
            lines = old_lines
            id = old_id
        # next_display.set_text(lines[0], lines[1])

# NOTE: Display switching is work in progess and currently not needed that much
#
#     def switch_position_by_index(self, src: int, dest: int) -> None:
#         if src not in range(len(self.displays)):
#             raise DisplayIndexError(src)
#         if dest not in range(len(self.displays)):
#             raise DisplayIndexError(dest)
#         self.switch_position(self.displays[src], self.displays[dest])
#
#     def switch_position_by_id(self, src: str, dest: str) -> None:
#         if not self.find_data_id_display(src):
#             raise DisplayDataIdError(src)
#         if not self.find_data_id_display(dest):
#             raise DisplayDataIdError(dest)
#         self.switch_position(
#             self.find_data_id_display(src),
#             self.find_data_id_display(dest)
#         )
#
#     def switch_position(self, src: Display, dest: Display) -> None:
#         pass
