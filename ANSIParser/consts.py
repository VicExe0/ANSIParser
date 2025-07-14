import re

TAG_PATTERN = re.compile(r"(?<!\\)<\/?\#?[:\w]+>|\<|[^<]+", re.DOTALL)
HEX_PATTERN = re.compile(r"^(?:\#[0-9a-fA-F]{6}(:bg)?)$")
ANSI_PATTERN = re.compile(r'\x1b\[[0-9;]+m')
ANSI_RESET = "\x1b[0m"
THEME_FOREGROUND = 38
THEME_BACKGROUND = 48
TAGS = {
    "": "", # Container
    "bold": "\x1b[1m",
    "dim": "\x1b[2m",
    "italic": "\x1b[3m",
    "underline": "\x1b[4m",
    "blink": "\x1b[5m",
    "reverse": "\x1b[7m",
    "hide": "\x1b[8m",
    "strikethrough": "\x1b[9m"
}