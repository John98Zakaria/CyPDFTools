from PDFObjectsParser import *
import pytest


class TestArray:
    def test_simple(self):
        simple1 = b"[1 2 3 4 5]"
        simple2 = b"[1 2 0 R]"
        simple3 = b"[15 0 R]"
        simple4 = b"[ 484  9874 618 798]"
        simple5 = b"[/Train (KEY) (Len(Pi))]"
        simple6 = b"[null false true]"
        simple7 = b"[11655 645 R]"

        assert classify_steam(ObjectIter(simple1)) == PDFArray([b"1", b"2", b"3", b"4", b"5"])
        assert classify_steam(ObjectIter(simple2)) == PDFArray([b"1", IndirectObjectRef(2, 0)])
        assert classify_steam(ObjectIter(simple3)) == PDFArray([IndirectObjectRef(15, 0)])
        assert classify_steam(ObjectIter(simple4)) == PDFArray([b"484", b"9874", b"618", b"798"])
        assert classify_steam(ObjectIter(simple5)) == PDFArray([b"/Train", b"(KEY)", b"(Len(Pi))"])
        assert classify_steam(ObjectIter(simple6)) == PDFArray([b"null", b"false", b"true"])
        assert classify_steam(ObjectIter(simple7)) == PDFArray([IndirectObjectRef(11655, 645)])

    def test_nested(self):
        nested1 = b"[1 2 3 [4 5 6]]"
        nested2 = b"[1 [4 5 6] 5 8]"
        nested3 = b"[1 [2 3] [4 5 6]]"
        nested4 = b"[1 2 3 [4 [5] 6]]"
        nested5 = b"[1 20 318 [4 [-5.497] 6]]"

        assert classify_steam(ObjectIter(nested1)) == PDFArray(
            [b'1', b'2', b'3', PDFArray([b'4', b'5', b'6'])])
        assert classify_steam(ObjectIter(nested2)) == PDFArray([b"1", PDFArray([b"4", b"5", b"6"]), b"5", b"8"])
        assert classify_steam(ObjectIter(nested3)) == PDFArray(
            [b"1", PDFArray([b"2", b"3"]), PDFArray([b"4", b"5", b"6"])])
        assert classify_steam(ObjectIter(nested4)) == PDFArray(
            [b"1", b"2", b"3", PDFArray([b"4", PDFArray([b"5"]), b"6"])])
        assert classify_steam(ObjectIter(nested5)) == PDFArray(
            [b'1', b'20', b'318', PDFArray([b'4', PDFArray([b'-5.497']), b'6'])])

    def test_empty(self):
        empty1 = b"[]"
        empty2 = b"[[]]"
        empty3 = b"[[[]]]"
        empty4 = b"[[] [] [[]]]"

        assert classify_steam(ObjectIter(empty1)) == PDFArray([])
        assert classify_steam(ObjectIter(empty2)) == PDFArray([PDFArray([])])
        assert classify_steam(ObjectIter(empty3)) == PDFArray([PDFArray([PDFArray([])])])
        assert classify_steam(ObjectIter(empty4)) == PDFArray([PDFArray([]), PDFArray([]), PDFArray([PDFArray([])])])


class TestNumeric:
    def test_simple(self):
        n1 = b"5"
        n2 = b"-5"
        n3 = b"105"
        n4 = b"10568"
        n5 = b"-1051.86"
        n6 = b"-2614816.984251"

        assert classify_steam(ObjectIter(n1)) == n1
        assert classify_steam(ObjectIter(n2)) == n2
        assert classify_steam(ObjectIter(n3)) == n3
        assert classify_steam(ObjectIter(n4)) == n4
        assert classify_steam(ObjectIter(n5)) == n5
        assert classify_steam(ObjectIter(n6)) == n6

    def test_ref(self):
        r1 = b"4 0 R"
        r2 = b"15 0 R"
        r3 = b"190 0 R"
        r4 = b"846 165 R"
        r5 = b"68 12 R"

        assert classify_steam(ObjectIter(r1)) == IndirectObjectRef(4, 0)
        assert classify_steam(ObjectIter(r2)) == IndirectObjectRef(15, 0)
        assert classify_steam(ObjectIter(r3)) == IndirectObjectRef(190, 0)
        print(ObjectIter(r4))
        assert classify_steam(ObjectIter(r4)) == IndirectObjectRef(846, 165)
        assert classify_steam(ObjectIter(r5)) == IndirectObjectRef(68, 12)


class TestDict:
    def test_simple(self):
        t1 = b"<</Type /Test/Length 2>>"
        t2 = b"<<>>"
        t3 = b"<< >>"
        assert classify_steam(ObjectIter(t1)) == PDFDict({b"/Type": b"/Test", b"/Length": b"2"})
        assert classify_steam(ObjectIter(t2)) == PDFDict({})
        assert classify_steam(ObjectIter(t3)) == PDFDict({})



    def test_random(self):
        t1 = (
            b"""/Type/Page/BleedBox[ 0 0 504 661.5]/Contents 5 0 R/CropBox[ 0 0 504 661.5]/MediaBox[ 0 0 504 661.5]/Parent 3493 0 R/Resources<</Font<</F3 2186 0 R>>/ProcSet[/Text/ImageC]>>/Rotate 0/Trans<<>>>>""")
        assert parse_dictionary(t1).data == {b'/Type': b'/Page',
                                             b'/BleedBox': PDFArray([b'0', b'0', b'504', b'661.5']),
                                             b'/Contents': IndirectObjectRef(5, 0), b'/CropBox':
                                                 PDFArray([b'0', b'0', b'504', b'661.5']),
                                             b'/MediaBox': PDFArray([b'0', b'0', b'504', b'661.5']),
                                             b'/Parent': IndirectObjectRef(3493, 0),
                                             b'/Resources': PDFDict(
                                                 {b'/Font': PDFDict({b'/F3': IndirectObjectRef(2186, 0)}),
                                                  b'/ProcSet': PDFArray([b'/Text', b'/ImageC'])}),
                                             b'/Rotate': b'0', b'/Trans': PDFDict({})}

    def test_dictWithStringLiterals(self):
        l1 = b"""/Producer (MiKTeX pdfTeX-1.40.21)
               /Creator (TeX)
               /CreationDate (D:20200504155420+02'00')
               /ModDate (D:20200504155420+02'00')
               /Trapped /False
               /PTEX.Fullbanner (This is MiKTeX-pdfTeX 2.9.7338 (1.40.21))"""
        assert parse_dictionary(l1).data == {b'/CreationDate': b"(D:20200504155420+02'00')",
                                             b'/Creator': b'(TeX)',
                                             b'/ModDate': b"(D:20200504155420+02'00')",
                                             b'/PTEX.Fullbanner': b'(This is MiKTeX-pdfTeX 2.9.7338 (1.40.21))',
                                             b'/Producer': b'(MiKTeX pdfTeX-1.40.21)',
                                             b'/Trapped': b'/False'}

        l2 = b"""/Author()/Title()/Subject()/Creator(\376\377\000L\000a\000T\000e\000X\000\040\000v\000i\000a\000\040\000p\000a\000n\000d\000o\000c)/Producer(pdfTeX-1.40.20)/Keywords()
        /CreationDate (D:20200419154240+02'00')
        /ModDate (D:20200419154240+02'00')
        /Trapped /False
        /PTEX.Fullbanner (This is pdfTeX, Version 3.14159265-2.6-1.40.20 (TeX Live 2019) kpathsea version 6.3.1)"""

        assert parse_dictionary(l2).data == {b'/Author': b'()',
                                             b'/CreationDate': b"(D:20200419154240+02'00')",
                                             b'/Creator': b'(\xfe\xff\x00L\x00a\x00T\x00e\x00X\x00 \x00v\x00i\x00a\x00 \x00'
                                                          b'p\x00a\x00n\x00d\x00o\x00c)',
                                             b'/Keywords': b'()',
                                             b'/ModDate': b"(D:20200419154240+02'00')",
                                             b'/PTEX.Fullbanner': b'(This is pdfTeX, Version 3.14159265-2.6-1.40.20 (TeX'
                                                                  b' Live 2019) kpathsea version 6.3.1)',
                                             b'/Producer': b'(pdfTeX-1.40.20)',
                                             b'/Subject': b'()',
                                             b'/Title': b'()',
                                             b'/Trapped': b'/False'}

    def test_multiline_parsing(self):
        t1 = b"""/Type /ObjStm
    /N 68
    /First 522
    /Length 2786      
    /Filter /FlateDecode"""
        assert parse_dictionary(t1).data == {b'/Filter': b'/FlateDecode',
                                             b'/First': b'522',
                                             b'/Length': b'2786',
                                             b'/N': b'68',
                                             b'/Type': b'/ObjStm'}

        t2 = b"""/R19
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

        assert parse_dictionary(t2).data == {b'/R11': IndirectObjectRef(11, 0),
                                             b'/R13': IndirectObjectRef(13, 0),
                                             b'/R15': IndirectObjectRef(15, 0),
                                             b'/R17': IndirectObjectRef(17, 0),
                                             b'/R19': IndirectObjectRef(19, 0),
                                             b'/R21': IndirectObjectRef(21, 0),
                                             b'/R29': IndirectObjectRef(29, 0),
                                             b'/R31': IndirectObjectRef(31, 0),
                                             b'/R33': IndirectObjectRef(33, 0),
                                             b'/R35': IndirectObjectRef(35, 0),
                                             b'/R9': IndirectObjectRef(9, 0)}

    def test_ListParsing(self):
        l1 = b"""/Type /Pages /Kids [
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

        assert parse_dictionary(l1).data == {b'/Count': b'30',
                                             b'/Kids': PDFArray(
                                                 [IndirectObjectRef(4, 0), IndirectObjectRef(26, 0),
                                                  IndirectObjectRef(40, 0),
                                                  IndirectObjectRef(46, 0),
                                                  IndirectObjectRef(52, 0), IndirectObjectRef(58, 0),
                                                  IndirectObjectRef(64, 0), IndirectObjectRef(70, 0),
                                                  IndirectObjectRef(76, 0), IndirectObjectRef(82, 0),
                                                  IndirectObjectRef(88, 0),
                                                  IndirectObjectRef(94, 0), IndirectObjectRef(100, 0),
                                                  IndirectObjectRef(110, 0),
                                                  IndirectObjectRef(117, 0), IndirectObjectRef(125, 0),
                                                  IndirectObjectRef(132, 0),
                                                  IndirectObjectRef(138, 0), IndirectObjectRef(144, 0),
                                                  IndirectObjectRef(150, 0),
                                                  IndirectObjectRef(156, 0), IndirectObjectRef(164, 0),
                                                  IndirectObjectRef(170, 0),
                                                  IndirectObjectRef(176, 0), IndirectObjectRef(182, 0),
                                                  IndirectObjectRef(189, 0),
                                                  IndirectObjectRef(195, 0), IndirectObjectRef(201, 0),
                                                  IndirectObjectRef(211, 0),
                                                  IndirectObjectRef(224, 0)]),
                                             b'/Type': b'/Pages'}

        t2 = b"""/BaseFont/FWRCSR+CMMIB10/FontDescriptor 34 0 R/Type/Font
    /FirstChar 78/LastChar 121/Widths[ 950 0
    0 0 0 0 0 0 0 0 947 674 0 0 0 0 0 0
    0 0 0 0 0 0 0 544 0 0 0 0 0 0 0 0
    0 0 0 0 415 0 0 0 0 590]
    /Encoding/WinAnsiEncoding/Subtype/Type1>>"""

        assert parse_dictionary(t2).data == {b'/BaseFont': b'/FWRCSR+CMMIB10',
                                             b'/FontDescriptor': IndirectObjectRef(34, 0),
                                             b'/Type': b'/Font', b'/FirstChar': b'78',
                                             b'/LastChar': b'121',
                                             b'/Widths': PDFArray(
                                                 [b"950", b"0", b"0", b"0", b"0", b"0", b"0", b"0", b"0", b"0", b"947",
                                                  b"674", b"0", b"0", b"0", b"0", b"0", b"0", b"0", b"0", b"0", b"0",
                                                  b"0",
                                                  b"0", b"0", b"544", b"0", b"0", b"0", b"0", b"0", b"0", b"0", b"0",
                                                  b"0",
                                                  b"0", b"0", b"0", b"415", b"0", b"0", b"0", b"0", b"590"]),
                                             b'/Encoding': b'/WinAnsiEncoding', b'/Subtype': b'/Type1'}


