#!/usr/bin/env python3
try:
    import re
    import struct
    import os
    import subprocess
    import sqlite3
    from sqlite3 import Error
    from setup import path
except ImportError as e:
    print(e)


class NotSudo(Exception):
    pass


if os.getuid() != 0:
    raise NotSudo("This program is not run as sudo or elevated this it will not work")


# clipboard
def get_selected_text():
    """
    Getting the text which is selected by mouse by piping the output of xsel
    """
    process = subprocess.Popen("xsel", stdout=subprocess.PIPE, universal_newlines=True)
    out = process.stdout.read()
    return out


def set_clipboard_text(data):
    """
    Setting the clipboards
    """
    process = subprocess.Popen(["xsel", "-b"], stdin=subprocess.PIPE)
    process.communicate(input=data)


class CrudDb:
    """
    Creating and retriving clipboard data in database
    """

    db = sqlite3.connect("/home/aluman/.nclip/db.sqlite3")

    cursor = db.cursor()

    def close_conn(self):
        self.db.close()

    def post(self, id, clip):
        self.cursor.execute(
            """INSERT OR REPLACE INTO clipboards(id,clip)
               VALUES (:id,:clip)   
               """,
            {"id": id, "clip": clip},
        )

    def query(self, id):
        self.cursor.execute(
            """
                SELECT clip from clipboards WHERE id=?
                """,
            (id,),
        )
        return self.cursor.fetchone()


def get_keyboard_event_file():
    """
    Getting the keyboard event file of keyboard
    """
    with open("/proc/bus/input/devices") as f:
        lines = f.readlines()
        pattern = re.compile("Handlers|EV=")
        handlers = list(
            filter(pattern.search, lines)
        )  # getting the list of line that contain Handlers or EV=
        pattern = re.compile("EV=120013")

        for index, value in enumerate(handlers):
            if pattern.search(value):
                line = handlers[
                    index - 1
                ]  # assigning line = The line which contain EV=12001113
        pattern = re.compile("event[0-9]")
        return "/dev/input/" + pattern.search(line).group(0)


qwerty_map = {
    2: "1",
    3: "2",
    4: "3",
    5: "4",
    6: "5",
    7: "6",
    8: "7",
    9: "8",
    10: "9",
    11: "0",
    12: "-",
    13: "=",
    14: "[BACKSPACE]",
    15: "[TAB]",
    16: "a",
    17: "z",
    18: "e",
    19: "r",
    20: "t",
    21: "y",
    22: "u",
    23: "i",
    24: "o",
    25: "p",
    26: "^",
    27: "$",
    28: "\n",
    29: "[CTRL]",
    30: "q",
    31: "s",
    32: "d",
    33: "f",
    34: "g",
    35: "h",
    36: "j",
    37: "k",
    38: "l",
    39: "m",
    40: "ù",
    41: "*",
    42: "[SHIFT]",
    43: "<",
    44: "w",
    45: "x",
    46: "c",
    47: "v",
    48: "b",
    49: "n",
    50: ",",
    51: ";",
    52: ":",
    53: "!",
    54: "[SHIFT]",
    55: "FN",
    56: "ALT",
    57: " ",
    58: "[CAPSLOCK]",
}

"""
FORMAT represents the format used by linux kernel input event struct
See https://github.com/torvalds/linux/blob/v5.5-rc5/include/uapi/linux/input.h#L28
Stands for: long int, long int, unsigned short, unsigned short, unsigned int
"""
FORMAT = "llHHI"
EVENT_SIZE = struct.calcsize(FORMAT)
in_file = open(get_keyboard_event_file(), "rb")

event = in_file.read(EVENT_SIZE)

typed = ""

combo = []
db_clip = CrudDb()
start = 0
while event:
    (_, _, type, code, value) = struct.unpack(FORMAT, event)
    if code != 0 and type == 1 and value == 1:
        if code in qwerty_map:
            typed = qwerty_map[code]
            if typed == "[CTRL]":
                start += 1
            if start > 0 and start < 2:
                combo.append(typed)
            if combo:
                if len(combo) == 3:
                    print("The combo is ", combo)
                    first_stoke, second_stoke, third_stoke = combo
                    try:
                        third_stoke = int(third_stoke)
                        print(third_stoke)
                    except ValueError as e:
                        third_stoke = 0
                    if (
                        (first_stoke == "[CTRL]")
                        and (second_stoke == "c")
                        and (third_stoke > 0)
                        and (third_stoke < 6)
                    ):
                        print(combo)
                        clip_selected = get_selected_text()
                        if third_stoke:
                            print("Into the third stoke")
                            db_clip.post(third_stoke, clip_selected)
                            print(f"Sucessfully copied {clip_selected}")
                    elif (
                        (first_stoke == "[CTRL]")
                        and (second_stoke == "g")
                        and (third_stoke > 0)
                        and (third_stoke < 6)
                    ):
                        print(combo)
                        print(f"Getted the text from clipboard {third_stoke}")
                        if third_stoke:
                            clip_from_db = db_clip.query(third_stoke)
                            if not clip_from_db:
                                clip_from_db = " "
                            if clip_from_db:
                                clip_from_db = clip_from_db[0]
                            print("Setted clipboard ", clip_from_db)
                            set_clipboard_text(bytes(clip_from_db, "utf-8"))
                    combo = []
                    start = 0
                else:
                    print("no")
        typed = ""
    event = in_file.read(EVENT_SIZE)
in_file.close()
