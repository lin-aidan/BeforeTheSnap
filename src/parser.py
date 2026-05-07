import re

def parse_input(text):
    text = text.lower()

    text = text.replace("first", "1")
    text = text.replace("second", "2")
    text = text.replace("third", "3")
    text = text.replace("fourth", "4")

    # allow messy input like "and and"
    match = re.search(r'(\d+)[^\d]+(\d+)', text)

    if match:
        down = int(match.group(1))
        distance = int(match.group(2))
        return down, distance

    raise ValueError("Could not parse input")