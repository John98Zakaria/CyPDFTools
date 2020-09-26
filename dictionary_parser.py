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
    #TODO Parse the entries
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
        if (not number.isnumeric()):
            number+=stream.moveto("/")
            break

    number = re.match(r"(\d+) *(0 R){0,1}",number)
    return number.group(1) if number.lastindex<2 else IndirectObjectRef(number.group(1))


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
    ##Bad table
    t1 = """/Type/Annot/Border[ 0 0 0]/Dest[ 4863 0 R/XYZ 76.450073 383.27719 0]/F 4/Rect[ 167.25 565.5 447.75 582]/Subtype/Link>>"""
    # print(parseDict(t1))
    #
    # t2 = """/Subtype/Image
    # /ColorSpace/DeviceGray
    # /Width 360
    # /Height 135
    # /BitsPerComponent 8
    # /Filter/DCTDecode/Length 6899>>"""
    #
    # print(parseDict(t2))


    t3 = """/BaseFont/FWRCSR+CMMIB10/FontDescriptor 34 0 R/Type/Font
/FirstChar 78/LastChar 121/Widths[ 950 0
0 0 0 0 0 0 0 0 947 674 0 0 0 0 0 0
0 0 0 0 0 0 0 544 0 0 0 0 0 0 0 0
0 0 0 0 415 0 0 0 0 590]
/Encoding/WinAnsiEncoding/Subtype/Type1>>"""

    print(parseDict(t3))
