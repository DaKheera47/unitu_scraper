import re

def get_nums_from_str(string):
    if string is None:
        return None

    # regex pattern to find all sequences of digits in the string
    pattern = r'\d+'
    # find all matches of the pattern in the string
    matches = re.findall(pattern, string)
    # convert matches to integers
    numbers = [int(match) for match in matches]
    return numbers
