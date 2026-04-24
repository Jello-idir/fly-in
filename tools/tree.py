from sys import stdout
from typing import Any
from functools import singledispatch


def tree(data: Any):
    bold   = "\033[1m"
    red = "\033[31m"
    green  = "\033[32m"
    yellow = "\033[33m"
    blue  = "\033[34m"
    magenta = "\033[35m"
    cyan = "\033[36m"

    nrml = "\033[22m"
    rst  = "\033[0m"

    c_title = "\033[48;2;255;255;255m\033[38;2;0;0;0m"
    c_dict = green
    c_list =  blue
    c_tuple = yellow
    c_set = magenta

    cb_title = bold + c_title
    cb_dict = bold + c_dict
    cb_list = bold + c_list
    cb_tuple = bold + c_tuple
    cb_set = bold + c_set

    PADD = 4

    @singledispatch
    def render(val: Any, padd):
        stdout.write(f"{"-" * padd}{val}\n")

    @render.register(dict)
    def _(val: dict, padd: int = 0):
        """ displays dict in a tree like structure """
        stdout.write("\n")
        parent_padd = padd - PADD
        for key, value in val.items():
            # dict case
            if isinstance(value, dict):
                stdout.write(f"╰{cb_dict}─{"─" * padd} {"{}"} {key}:{rst}")
                render(value, padd + PADD)

            # list case
            elif isinstance(value, list):
                stdout.write(f"╰{cb_list}─{"─" * padd} {"[]"} {key}:{rst}")
                render(value, padd + PADD)

            elif isinstance(value, tuple):
                stdout.write(f"│{cb_tuple} {" " * padd} {"()"} {key}: ")
                render(value, padd + PADD)

            elif isinstance(value, set):
                stdout.write(f"│{cb_set} {" " * padd} {"}{"} {key}: {nrml}{value}{rst}\n")

            # normal value
            else:
                stdout.write(f"│{" " * padd}  {"──"} {key}: {nrml}{value}\n")

    @render.register(list)
    def _(val: list, padd: int = 0):
        """ displays list in a tree like structure """

        stdout.write("\n")
        for item in val:
            if isinstance(item, list):
                stdout.write(f"│{" " * padd}")
                render(item, padd + PADD)
            elif isinstance(item, dict):
                stdout.write(f"╰{red}─{"─" * padd} {"{}"} {"--"}: {rst}")
                render(item, padd + PADD)
            elif isinstance(item, tuple):
                stdout.write(f"│{cb_tuple} {" " * padd} {"()"} {""}: {rst}")
                render(item, padd + PADD)
            else:
                stdout.write(f"│{" " * padd} ╰[ {item}\n")

    @render.register(tuple)
    def _(val: tuple, padd: int = 0):
        # remove the ['] from strings
        val = str(val).replace("'", "") # type: ignore
        stdout.write(f"{nrml}{c_tuple}{val}{rst}\n")


    stdout.write(f"{cb_title} Map Data: {rst}\n│")
    render(data)

# U+250x 	─ 	━ 	│ 	┃ 	┄ 	┅ 	┆ 	┇ 	┈ 	┉ 	┊ 	┋ 	┌ 	┍ 	┎ 	┏
# U+251x 	┐ 	┑ 	┒ 	┓ 	└ 	┕ 	┖ 	┗ 	┘ 	┙ 	┚ 	┛ 	├ 	┝ 	┞ 	┟
# U+252x 	┠ 	┡ 	┢ 	┣ 	┤ 	┥ 	┦ 	┧ 	┨ 	┩ 	┪ 	┫ 	┬ 	┭ 	┮ 	┯
# U+253x 	┰ 	┱ 	┲ 	┳ 	┴ 	┵ 	┶ 	┷ 	┸ 	┹ 	┺ 	┻ 	┼ 	┽ 	┾ 	┿
# U+254x 	╀ 	╁ 	╂ 	╃ 	╄ 	╅ 	╆ 	╇ 	╈ 	╉ 	╊ 	╋ 	╌ 	╍ 	╎ 	╏
# U+255x 	═ 	║ 	╒ 	╓ 	╔ 	╕ 	╖ 	╗ 	╘ 	╙ 	╚ 	╛ 	╜ 	╝ 	╞ 	╟
# U+256x 	╠ 	╡ 	╢ 	╣ 	╤ 	╥ 	╦ 	╧ 	╨ 	╩ 	╪ 	╫ 	╬ 	╭ 	╮ 	╯
# U+257x 	╰ 	╱ 	╲ 	╳ 	╴ 	╵ 	╶ 	╷ 	╸ 	╹ 	╺ 	╻ 	╼ 	╽ 	╾ 	╿
