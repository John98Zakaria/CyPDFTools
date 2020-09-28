from utills import ObjectIter
from PDFObjects import *
from typing import Iterable, List
import re

SEPERATORS = "\\/[]<>() \t\n"


def extract_name(stream: ObjectIter) -> str:
    """
    Extracts the next name from the iterator (7.3.5 PDF 32000-1:2008)
    :param stream:A stream whose forward slash / was just consumed
    :return: String containing the name
    """
    out_string = "/"
    for letter in stream:
        if (letter in SEPERATORS):
            stream.prev()  # Reverts a step back to where
            # the name ended in order for the typechecker to deduce the type
            break
        out_string += letter
    return out_string


def skip_space(stream: ObjectIter) -> str:
    """
    Moves stream to the next non whitespace char
    :param stream: Any iterable object
    :return: First letter after the whitespace
    """
    if(not stream.peek(1).isspace()):
        return ""
    for _ in stream:
        if (not stream.peek(1).isspace()):
            return ""


def parse_string_literal(stream: ObjectIter) -> str:
    """
    Parses string literals (7.3.4.2) PDF 32000-1:2008
    :param stream: A stream whose opening round bracket ( was just consumed
    :return: The string literal including the round brackets
    """
    out_string = "("
    countOpeningBraces = 1
    countClosingBraces = 0
    for letter in stream:
        if countClosingBraces == countOpeningBraces:
            break
        if letter == "(":
            countOpeningBraces += 1
        elif letter == ")":
            countClosingBraces += 1
        out_string += letter
    stream.prev()
    return out_string


def parse_numeric(init, stream: ObjectIter):
    number: str = init
    for char in stream:
        if (char in "\\/[]<>()\t\n"):
            stream.prev()
            break
        elif (char==" "):
            upcomingchars = stream.peek(3)
            isRef = upcomingchars=="0 R"
            if(isRef):
                stream.pointer+=3
                return IndirectObjectRef(number)
            else:
                return number
        elif (not char.isnumeric() and char!="."):
            number += stream.finishNumber()
            break
        number += char
    return number



def parse_stream(streamIter: ObjectIter, letter=None):
    if (letter is None):
        letter = next(streamIter)
    if letter == "/":
        value = extract_name(streamIter)

    elif letter == "[":
        value = extract_array(streamIter)

    elif letter.isnumeric() or letter == "-":
        value = parse_numeric(letter, streamIter)

    elif letter == "<":
        letter = next(streamIter)
        if letter == "<":
            value = parse_dictionary(streamIter)
        else:
            value = "<" + streamIter.moveto(">") + ">"
            next(streamIter)
    elif letter == "(":
        value = parse_string_literal(streamIter)
    elif letter in "tf": #handels true/false
        value = streamIter.moveto("e") + next(streamIter)
    elif letter== "n": #handels null values
        peek = streamIter.peek(3)
        if(peek=="ull"):
            value = "null"
            streamIter.pointer+=3

    skip_space(streamIter)

    return value


def parse_dictionary(pdf_stream):
    object_dict = dict()
    streamIter = ObjectIter(pdf_stream) if type(pdf_stream) != ObjectIter else pdf_stream
    streamIter.prepareDictParse()
    for letter in streamIter:
        # Parse Key

        if letter == ">":
            letter = next(streamIter)
            if (letter == ">"):
                return PDFDict(object_dict)

        elif letter != "/":
            raise AssertionError(f"Expected a forward slash / to build a dict key but got {letter}")
        key = extract_name(streamIter)
        skip_space(streamIter)
        letter = next(streamIter)
        # parse value
        value = parse_stream(streamIter, letter)


        object_dict[key] = value

    return PDFDict(object_dict)


def extract_array(stream: Iterable) -> List[str]:
    out_string = ""
    for letter in stream:
        if letter == "]":
            break
        out_string += letter

    return PDFArray(parse_arrayObjects(out_string))
    # return out_string.strip(" ").split(" ")


def parse_arrayObjects(array_str: str):
    stream_iter = ObjectIter(array_str)
    array = []
    for char in stream_iter:
        if(char.isspace()):
            continue
        item = parse_stream(stream_iter, char)
        array.append(item)

    return array


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
    # t1 = (
    #     rf"""/Type/Page/BleedBox[ 0 0 504 661.5]/Contents 5 0 R/CropBox[ 0 0 504 661.5]/MediaBox[ 0 0 504 661.5]/Parent 3493 0 R/Resources<</Font<</F3 2186 0 R>>/ProcSet[/Text/ImageC]>>/Rotate 0/Trans<<>>>>""")

    l1 = """/Type /Pages /Kids [
    4 0 R
    26 0 R
    40 0 R
    46 0 R
    52 0 R
    58 0 R
    64 0 R
    70 0 R
    76 0 R
    82 0 R
    88 0 R
    94 0 R
    100 0 R
    110 0 R
    117 0 R
    125 0 R
    132 0 R
    138 0 R
    144 0 R
    150 0 R
    156 0 R
    164 0 R
    170 0 R
    176 0 R
    182 0 R
    189 0 R
    195 0 R
    201 0 R
    211 0 R
    224 0 R
    ] /Count 30
    >>"""


    print(parse_dictionary(l1))

#     arr = "5 0 9 7"
#     print(parse_arrayObjects(arr))
#
#     t2 = """/R17
#        17 0 R>>"""
#
#     print(parse_dictionary(t2))
#     print(parse_numeric("",ObjectIter("587.78")))
#     t3 = """/BaseFont/FWRCSR+CMMIB10/FontDescriptor 34 0 R/Type/Font
# /FirstChar 78/LastChar 121/Widths[ 950 0
# 0 0 0 0 0 0 0 0 947 674 0 0 0 0 0 0
# 0 0 0 0 0 0 0 544 0 0 0 0 0 0 0 0
# 0 0 0 0 415 0 0 0 0 590]
# /Encoding/WinAnsiEncoding/Subtype/Type1>>"""
#     # print(parse_dictionary(t3))
#
#     t4 = """/Type/Encoding/BaseEncoding/WinAnsiEncoding/Differences[
# 0/parenleftbig/parenrightbig
# 16/parenleftBig/parenrightBig/parenleftbigg/parenrightbigg
# 26/braceleftbigg
# 34/bracketleftBigg/bracketrightBigg
# 40/braceleftBigg/bracerightBigg
# 56/bracelefttp/bracerighttp/braceleftbt/bracerightbt/braceleftmid/bracerightmid/braceex
# 80/summationtext
# 88/summationdisplay
# 90/integraldisplay
# 104/bracketleftBig/bracketrightBig
# 110/braceleftBig/bracerightBig/radicalbig
# 122/bracehtipdownleft/bracehtipdownright/bracehtipupleft/bracehtipupright]>>"""
#
#     print(parse_dictionary(t4))
#
#     r3 = """<<
# /Font << /F32 4 0 R /F31 5 0 R /F50 6 0 R /F51 7 0 R /F35 8 0 R /F38 9 0 R /F33 10 0 R /F34 11 0 R >>
# /ProcSet [ /PDF /Text ]
# >>
# endobj"""
#
#     print(parse_stream(ObjectIter(r3)))
#
#     r5 = """<<
# /Title <feff0050006f0077006500720050006f0069006e0074002d0050007200e400730065006e0074006100740069006f006e>
# /Author (Schumacher, Hendrik-Lukas)
# /CreationDate (D:20200430160325+02'00')
# /ModDate (D:20200430160325+02'00')
# /Producer <feff004d006900630072006f0073006f0066007400ae00200050006f0077006500720050006f0069006e007400ae0020006600fc00720020004f006600660069006300650020003300360035>
# /Creator <feff004d006900630072006f0073006f0066007400ae00200050006f0077006500720050006f0069006e007400ae0020006600fc00720020004f006600660069006300650020003300360035>
# >>
# endobj"""
#     o = ObjectIter(r5)
#     # print(objectIdentifier(o))
#
#     t6 = """<<
# /Type /FontDescriptor
# /FontName /BCDEEE+Calibri
# /Flags 32
# /ItalicAngle 0
# /Ascent 750
# /Descent -250
# /CapHeight 750
# /AvgWidth 521
# /MaxWidth 1743
# /FontWeight 400
# /XHeight 250
# /StemV 52
# /FontBBox [ -503 -250 1240 750]
# /FontFile2 27 0 R
# >>
# endobj"""
#
#     o = ObjectIter(t6)
#
#     # print(objectIdentifier(o))
#
#     l1 = """/Type /Pages /Kids [
#     4 0 R
#     26 0 R
#     40 0 R
#     46 0 R
#     52 0 R
#     58 0 R
#     64 0 R
#     70 0 R
#     76 0 R
#     82 0 R
#     88 0 R
#     94 0 R
#     100 0 R
#     110 0 R
#     117 0 R
#     125 0 R
#     132 0 R
#     138 0 R
#     144 0 R
#     150 0 R
#     156 0 R
#     164 0 R
#     170 0 R
#     176 0 R
#     182 0 R
#     189 0 R
#     195 0 R
#     201 0 R
#     211 0 R
#     224 0 R
#     ] /Count 30
#     >>"""
#
#     # print(parse_dictionary(l1))
