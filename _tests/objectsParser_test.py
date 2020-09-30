import pytest
from objectsParser import *


class TestArray:
    def test_simple(self):
        simple1 = b"[1 2 3 4 5]"
        simple2 = b"[1 2 0 R]"
        simple3 = b"[15 0 R]"
        simple4 = b"[ 484  9874 618 798]"
        simple5 = b"[/Train (KEY) (Len(Pi))]"
        simple6 = b"[null false true]"

        assert parse_stream(ObjectIter(simple1)) == PDFArray([b"1", b"2", b"3", b"4", b"5"])
        assert parse_stream(ObjectIter(simple2)) == PDFArray([b"1", IndirectObjectRef(2)])
        assert parse_stream(ObjectIter(simple3)) == PDFArray([IndirectObjectRef(15)])
        assert parse_stream(ObjectIter(simple4)) == PDFArray([b"484", b"9874", b"618", b"798"])
        assert parse_stream(ObjectIter(simple5)) == PDFArray([b"/Train", b"(KEY)", b"(Len(Pi))"])
        assert parse_stream(ObjectIter(simple6)) == PDFArray([b"null", b"false", b"true"])

    def test_nested(self):
        pytest.skip()
        nested1 = b"[1 2 3 [4 5 6]]"
        nested2 = b"[1 [4 5 6] 5 8]"
        nested3 = b"[1 [2 3] [4 5 6]]"
        nested4 = b"[1 2 3 [4 [5] 6]]"
        nested5 = b"[1 20 318 [4 [-5.497] 6]]"

        assert parse_stream(ObjectIter(nested1)) == PDFArray(
            [PDFArray([b"1", b"2", b"3", PDFArray([b"4", b"5", b"6"])])])
        assert parse_stream(ObjectIter(nested2)) == PDFArray([b"1", PDFArray([b"4", b"5", b"6"], b"5", b"8")])
        assert parse_stream(ObjectIter(nested3)) == PDFArray(
            [b"1", PDFArray([b"2", b"3"]), PDFArray([b"4", b"5", b"6"])])
        assert parse_stream(ObjectIter(nested4)) == PDFArray([b"484", b"9874", b"618", b"798"])
        assert parse_stream(ObjectIter(nested5)) == PDFArray([b"/Train", b"(KEY)", b"(Len(Pi))"])

    def test_empty(self):
        pytest.skip()
        empty1 = "[]"
        empty2 = "[[]]"
        empty3 = "[[[]]]"
        empty4 = "[[] [] [[]]]"


class TestNumeric:
    def test_simple(self):
        n1 = "5"
        n2 = "-5"
        n3 = "105"
        n4 = "10568"
        n5 = "-1051.86"
        n7 = "-2614816.984251"

    def test_ref(self):
        r1 = "4 0 R"
        r2 = "15 0 R"
        r3 = "190 0 R"
        r4 = "190 0 R"


def test_OnSameLine():
    t1 = (
        b"""/Type/Page/BleedBox[ 0 0 504 661.5]/Contents 5 0 R/CropBox[ 0 0 504 661.5]/MediaBox[ 0 0 504 661.5]/Parent 3493 0 R/Resources<</Font<</F3 2186 0 R>>/ProcSet[/Text/ImageC]>>/Rotate 0/Trans<<>>>>""")
    assert (parse_dictionary(t1).data == {'Type': 'Page', 'BleedBox': ['0', '0', '504', '661.5'],
                                          'Contents': IndirectObjectRef(5),
                                          'CropBox': ['0', '0', '504', '661.5'], 'MediaBox': ['0', '0', '504', '661.5'],
                                          'Parent': IndirectObjectRef(3493),
                                          'Resources': {'Font': {'F3': IndirectObjectRef(2186)},
                                                        'ProcSet': ['/Text/ImageC']},
                                          'Rotate': "0",
                                          'Trans': {}})


def test_ListParsing():
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

    assert parse_dictionary(l1).data == {'/Count': '30',
                                         '/Kids': PDFArray(
                                             [IndirectObjectRef(4), IndirectObjectRef(26), IndirectObjectRef(40),
                                              IndirectObjectRef(46),
                                              IndirectObjectRef(52), IndirectObjectRef(58),
                                              IndirectObjectRef(64), IndirectObjectRef(70),
                                              IndirectObjectRef(76), IndirectObjectRef(82), IndirectObjectRef(88),
                                              IndirectObjectRef(94), IndirectObjectRef(100), IndirectObjectRef(110),
                                              IndirectObjectRef(117), IndirectObjectRef(125), IndirectObjectRef(132),
                                              IndirectObjectRef(138), IndirectObjectRef(144), IndirectObjectRef(150),
                                              IndirectObjectRef(156), IndirectObjectRef(164), IndirectObjectRef(170),
                                              IndirectObjectRef(176), IndirectObjectRef(182), IndirectObjectRef(189),
                                              IndirectObjectRef(195), IndirectObjectRef(201), IndirectObjectRef(211),
                                              IndirectObjectRef(224)]),
                                         '/Type': '/Pages'}

    t2 = """/BaseFont/FWRCSR+CMMIB10/FontDescriptor 34 0 R/Type/Font
/FirstChar 78/LastChar 121/Widths[ 950 0
0 0 0 0 0 0 0 0 947 674 0 0 0 0 0 0
0 0 0 0 0 0 0 544 0 0 0 0 0 0 0 0
0 0 0 0 415 0 0 0 0 590]
/Encoding/WinAnsiEncoding/Subtype/Type1>>"""

    assert parse_dictionary(t2).data == {'/BaseFont': '/FWRCSR+CMMIB10',
                                         '/FontDescriptor': IndirectObjectRef(34),
                                         '/Type': '/Font', '/FirstChar': '78',
                                         '/LastChar': '121',
                                         '/Widths': PDFArray(["950", "0", "0", "0", "0", "0", "0", "0", "0", "0", "947",
                                                              "674", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0",
                                                              "0",
                                                              "0", "0", "544", "0", "0", "0", "0", "0", "0", "0", "0",
                                                              "0",
                                                              "0", "0", "0", "415", "0", "0", "0", "0", "590"]),
                                         '/Encoding': '/WinAnsiEncoding', '/Subtype': '/Type1'}


def test_StringLiterals():
    l1 = """/Producer (MiKTeX pdfTeX-1.40.21)
           /Creator (TeX)
           /CreationDate (D:20200504155420+02'00')
           /ModDate (D:20200504155420+02'00')
           /Trapped /False
           /PTEX.Fullbanner (This is MiKTeX-pdfTeX 2.9.7338 (1.40.21))"""
    assert parse_dictionary(l1).data == {'/CreationDate': "(D:20200504155420+02'00')",
                                         '/Creator': '(TeX)',
                                         '/ModDate': "(D:20200504155420+02'00')",
                                         '/PTEX.Fullbanner': '(This is MiKTeX-pdfTeX 2.9.7338 (1.40.21))',
                                         '/Producer': '(MiKTeX pdfTeX-1.40.21)',
                                         '/Trapped': '/False'}

    l2 = """/Author()/Title()/Subject()/Creator(\376\377\000L\000a\000T\000e\000X\000\040\000v\000i\000a\000\040\000p\000a\000n\000d\000o\000c)/Producer(pdfTeX-1.40.20)/Keywords()
    /CreationDate (D:20200419154240+02'00')
    /ModDate (D:20200419154240+02'00')
    /Trapped /False
    /PTEX.Fullbanner (This is pdfTeX, Version 3.14159265-2.6-1.40.20 (TeX Live 2019) kpathsea version 6.3.1)"""

    assert parse_dictionary(l2).data == {'/Author': '()',
                                         '/CreationDate': "(D:20200419154240+02'00')",
                                         '/Creator': '(þÿ\x00L\x00a\x00T\x00e\x00X\x00 \x00v\x00i\x00a\x00 '
                                                     '\x00p\x00a\x00n\x00d\x00o\x00c)',
                                         '/Keywords': '()',
                                         '/ModDate': "(D:20200419154240+02'00')",
                                         '/PTEX.Fullbanner': '(This is pdfTeX, Version 3.14159265-2.6-1.40.20 (TeX '
                                                             'Live 2019) kpathsea version 6.3.1)',
                                         '/Producer': '(pdfTeX-1.40.20)',
                                         '/Subject': '()',
                                         '/Title': '()',
                                         '/Trapped': '/False'}


def test_multiline():
    t1 = b"""/Type /ObjStm
/N 68
/First 522
/Length 2786      
/Filter /FlateDecode"""
    assert parse_dictionary(t1).data == {'/Type': '/ObjStm', '/N': "68",
                                         '/First': "522",
                                         '/Length': "2786", '/Filter': '/FlateDecode'}

    t2 = """/R19
    19 0 R/R11
    11 0 R/R9
    9 0 R/R33
    33 0 R/R35
    35 0 R/R31
    31 0 R/R29
    29 0 R/R13
    13 0 R/R15
    15 0 R/R21
    21 0 R/R17
    17 0 R>>"""

    assert (parse_dictionary(t2) ==
            {'/R19': IndirectObjectRef(19), '/R11': IndirectObjectRef(11), '/R9': IndirectObjectRef(9),
             '/R33': IndirectObjectRef(33), '/R35': IndirectObjectRef(35), '/R31': IndirectObjectRef(31),
             '/R29': IndirectObjectRef(29), '/R13': IndirectObjectRef(13),
             '/R15': IndirectObjectRef(15), '/R21': IndirectObjectRef(21), '/R17': IndirectObjectRef(17)})
