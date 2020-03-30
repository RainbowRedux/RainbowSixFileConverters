"""Utility classes and functions for reading text files"""
import shlex

def read_tokenized_text_file(path):
    """Reads a text file and tokenizes.
    Keeps strings within quotes, and discards comments"""
    inFile = open(path, "r")
    lines = inFile.readlines()
    inFile.close()
    keywords = []
    for line in lines:
        # Strip comments out from this line of text
        commentStart = line.find("//")
        filteredLine = line
        if commentStart > -1:
            filteredLine = filteredLine[:commentStart]
        line_values = []
        try:
            line_values = shlex.split(filteredLine)
        except ValueError as ve:
            # Some files are incorrectly written, for instance M09 in Rainbow Six is missing a quotation close for an operator name
            # Unfortunately since the original files can't be patched this code needs to be forgiving around errors
            if ve.args == "No closing quotation":
                line_values = shlex.split(filteredLine + "\"")
        for value in line_values:
            keywords.append(value)
    return keywords

def read_text_dict(path):
    """Reads a tokenized text file and assumes that it's full of key/value pairs"""
    new_dict = {}
    tokens = read_tokenized_text_file(path)
    while len(tokens) > 1:
        new_key = tokens.pop(0)
        new_value = tokens.pop(0)
        new_dict[new_key] = new_value

    return new_dict

def read_keyword_list(keywords, list_length):
    """Reads a number of tokens froma keyword list and returns as separate list"""
    newlist = []
    #Uses a loop like this to ensure the original list is modified when removing keywords, rather than a just this reference to the list updating
    for _ in range(list_length):
        newlist.append(keywords.pop(0))
    return newlist
