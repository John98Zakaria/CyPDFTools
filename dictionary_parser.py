from utills import BidirectionalIterator
from pdfobjects import *
from typing import Iterable
import re

def extractNextName(stream: BidirectionalIterator) -> str:
    """
    Extracts the next name from the iterator (7.3.5 PDF 32000-1:2008)
    :param stream:A stream whose forward slash / was just consumed
    :return: String containing the name
    """
    out_string = ""
    for letter in stream:
        if (not letter.isalnum() and not letter == "."):
            stream.prev()  # Reverts a step back to where
            # the name ended in order for the typechecker to deduce the type
            break
        out_string += letter
    return out_string


def skipSpace(stream: Iterable) -> str:
    """
    Moves stream to the next non whitespace char
    :param stream: Any iterable object
    :return: First letter after the whitespace
    """
    for letter in stream:
        if (not letter.isspace()):
            return letter


def parseList(stream: Iterable) -> str:
    out_string = ""
    for letter in stream:
        if letter == "]":
            break
        out_string += letter
    return out_string.strip().split(" ")


def parseStringLiteral(stream: BidirectionalIterator) -> str:
    """
    Parses string literals (7.3.4.2) PDF 32000-1:2008
    :param stream: A stream whose opening round bracket ( was just consumed
    :return: The string literal including the round brackets
    """
    out_string = "("
    countOpeningBraces = 1
    countClosingBraces = 0
    for letter in stream:
        if (countClosingBraces == countOpeningBraces):
            break
        if (letter == "("):
            countOpeningBraces += 1
        elif (letter == ")"):
            countClosingBraces += 1
        out_string += letter
    stream.prev()
    return out_string


def parseNumeric(init, stream: BidirectionalIterator):
    number: str = init
    for char in stream:
        number += char
        if (not number.isnumeric() or char == "/"):
            stream.moveto("/")
            return IndirectObjectRef(number[:-1])
    return number


def parseDict(pdf_stream):
    object_dict = dict()
    streamIter = BidirectionalIterator(pdf_stream) if type(pdf_stream) != BidirectionalIterator else pdf_stream
    for letter in streamIter:
        # Parse Key
        if (letter == ">"):
            letter = next(streamIter)
            if (letter == ">"):
                return object_dict

        elif (letter != "/"):
            raise AssertionError(f"Expected a forward slash / to build a dict key but got {letter}")
        key = extractNextName(streamIter)
        letter = skipSpace(streamIter)

        # parse value

        if (letter == "/"):
            value = extractNextName(streamIter)

        elif (letter == "["):
            value = parseList(streamIter)

        elif (letter.isnumeric()):
            value = parseNumeric(letter, streamIter)

        elif (letter == "<"):
            letter = next(streamIter)
            if (letter == "<"):
                value = parseDict(streamIter)
            else:
                value = letter + streamIter.moveto(">")
        elif (letter == "("):
            value = parseStringLiteral(streamIter)


        skipSpace(streamIter)
        try:
            streamIter.prev()
        except IndexError:
            pass
        object_dict[key] = value

    return object_dict


if __name__ == '__main__':
    t1 = """/Type /ObjStm
    /N 68
    /First 522
    /Length 2786      
    /Filter /FlateDecode"""
    print(parseDict(t1))

