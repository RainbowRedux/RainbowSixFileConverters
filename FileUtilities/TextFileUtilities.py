"""Utility classes and functions for reading text files"""
import shlex

def read_tokenized_text_file(path):
    """Reads a text file and tokenizes.
    Keeps strings within quotes, and discards comments"""
    inFile = open(path, "r")
    lines = inFile.readlines()
    cxp_keywords = []
    for line in lines:
        # Strip comments out from this line of text
        commentStart = line.find("//")
        filteredLine = line
        if commentStart > -1:
            filteredLine = filteredLine[:commentStart]
        line_values = shlex.split(filteredLine)
        for value in line_values:
            cxp_keywords.append(value)
    return cxp_keywords
