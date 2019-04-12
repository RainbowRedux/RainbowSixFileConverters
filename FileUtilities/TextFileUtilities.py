"""Utility classes and functions for reading text files"""
import shlex

def read_tokenized_text_file(path):
    """Reads a text file and tokenizes.
    Keeps strings within quotes, and discards comments"""
    inFile = open(path, "r")
    lines = inFile.readlines()
    keywords = []
    for line in lines:
        # Strip comments out from this line of text
        commentStart = line.find("//")
        filteredLine = line
        if commentStart > -1:
            filteredLine = filteredLine[:commentStart]
        line_values = shlex.split(filteredLine)
        for value in line_values:
            keywords.append(value)
    return keywords

def read_text_dict(path):
    new_dict = {}
    tokens = read_tokenized_text_file(path)
    while len(tokens) > 1:
        new_key = tokens.pop(0)
        new_value = tokens.pop(0)
        new_dict[new_key] = new_value

    return new_dict