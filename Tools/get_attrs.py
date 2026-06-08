from typing import Any
from .AnssiColors import AnssiColors as C
import sys


def get_attrs(object: Any, title: str | None = None,
              color: str = C.blue, skip_private: bool = True):

    if not title:
        title = f"{object.__class__}"

    padd = 0
    # finding the longest attr for paddin
    for attr in object.__dict__:
        if skip_private and attr.startswith("_"):
            continue
        attr_len = len(attr)
        if attr_len > padd:
            padd = attr_len

    # printin attrs
    sys.stdout.write(f"\n{color}{title}\033[0m\n")
    sys.stdout.write(f"{"-" * 40}\n")
    for attr, value in object.__dict__.items():
        if skip_private and attr.startswith("_"):
            continue
        if value is None:
            value = f"{C.red}None{C.reset}"
        sys.stdout.write(f"{attr.ljust(padd)} : {value}\n")
    sys.stdout.write(f"{"-" * 40}\n")
