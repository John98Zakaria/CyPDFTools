from utills import ObjectIter
from pdfobjects import *
from typing import Iterable
import re

SEPERATORS = "\\/[]<>() \t\n"


def extractNextName(stream: ObjectIter) -> str:
    """
    Extracts the next name from the iterator (7.3.5 PDF 32000-1:2008)
    :param stream:A stream whose forward slash / was just consumed
    :return: String containing the name
    """
    out_string = ""
    for letter in stream:
        if (letter in SEPERATORS):
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
    # TODO Parse the entries
    out_string = ""
    for letter in stream:
        if letter == "]":
            break
        out_string += letter
    return out_string.strip().split(" ")


def parseStringLiteral(stream: ObjectIter) -> str:
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


def parseNumeric(init, stream: ObjectIter):
    #TODO Test negative number
    number: str = init
    for char in stream:
        number += char
        if (not number.lstrip("-").isnumeric() ):
            number += stream.moveto("/")
            break

    number = re.match(r"-?(\d+) *(0 R){0,1}", number)
    return number.group(1) if number.lastindex < 2 else IndirectObjectRef(number.group(1))


def objectIdentifier(streamIter: Iterable, letter=None):
    if(letter is None):
        letter = next(streamIter)
    if (letter == "/"):
        value = extractNextName(streamIter)

    elif (letter == "["):
        value = parseList(streamIter)

    elif (letter.isnumeric() or letter=="-"):
        value = parseNumeric(letter, streamIter)

    elif (letter == "<"):
        letter = next(streamIter)
        if (letter == "<"):
            value = parseDict(streamIter)
        else:
            value = "<" + streamIter.moveto(">")+">"
            next(streamIter)
    elif (letter == "("):
        value = parseStringLiteral(streamIter)

    skipSpace(streamIter)

    return value


def parseDict(pdf_stream):
    object_dict = dict()
    streamIter = ObjectIter(pdf_stream) if type(pdf_stream) != ObjectIter else pdf_stream
    streamIter.prepareDictParse()
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
        value = objectIdentifier(streamIter, letter)

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

    t4 = """/Type/Encoding/BaseEncoding/WinAnsiEncoding/Differences[
0/parenleftbig/parenrightbig
16/parenleftBig/parenrightBig/parenleftbigg/parenrightbigg
26/braceleftbigg
34/bracketleftBigg/bracketrightBigg
40/braceleftBigg/bracerightBigg
56/bracelefttp/bracerighttp/braceleftbt/bracerightbt/braceleftmid/bracerightmid/braceex
80/summationtext
88/summationdisplay
90/integraldisplay
104/bracketleftBig/bracketrightBig
110/braceleftBig/bracerightBig/radicalbig
122/bracehtipdownleft/bracehtipdownright/bracehtipupleft/bracehtipupright]>>"""

    # print(parseDict(t4))

    r3 ="""<<
/Font << /F32 4 0 R /F31 5 0 R /F50 6 0 R /F51 7 0 R /F35 8 0 R /F38 9 0 R /F33 10 0 R /F34 11 0 R >>
/ProcSet [ /PDF /Text ]
>>
endobj"""

    # print(objectIdentifier(ObjectIter(r3)))

    r5 = """<<
/Title <feff0050006f0077006500720050006f0069006e0074002d0050007200e400730065006e0074006100740069006f006e>
/Author (Schumacher, Hendrik-Lukas)
/CreationDate (D:20200430160325+02'00')
/ModDate (D:20200430160325+02'00')
/Producer <feff004d006900630072006f0073006f0066007400ae00200050006f0077006500720050006f0069006e007400ae0020006600fc00720020004f006600660069006300650020003300360035>
/Creator <feff004d006900630072006f0073006f0066007400ae00200050006f0077006500720050006f0069006e007400ae0020006600fc00720020004f006600660069006300650020003300360035>
>>
endobj"""
    o = ObjectIter(r5)
    print(objectIdentifier(o))

    t6 = """<<
/Type /FontDescriptor
/FontName /BCDEEE+Calibri
/Flags 32
/ItalicAngle 0
/Ascent 750
/Descent -250
/CapHeight 750
/AvgWidth 521
/MaxWidth 1743
/FontWeight 400
/XHeight 250
/StemV 52
/FontBBox [ -503 -250 1240 750]
/FontFile2 27 0 R
>>
endobj"""

    o = ObjectIter(t6)

    print(objectIdentifier(o))