import pytest
from dictionary_parser import *


def test_OnSameLine():
    t1 = (rf"""/Type/Page/BleedBox[ 0 0 504 661.5]/Contents 5 0 R/CropBox[ 0 0 504 661.5]/MediaBox[ 0 0 504 661.5]/Parent 3493 0 R/Resources<</Font<</F3 2186 0 R>>/ProcSet[/Text/ImageC]>>/Rotate 0/Trans<<>>>>""")
    assert (parseDict(t1) == {'Type': 'Page', 'BleedBox': ['0', '0', '504', '661.5'], 'Contents': IndirectObjectRef(5),
                              'CropBox': ['0', '0', '504', '661.5'], 'MediaBox': ['0', '0', '504', '661.5'],
                              'Parent': IndirectObjectRef(3493), 'Resources': {'Font': {'F3': IndirectObjectRef(2186),
                                                                                        'ProcSet': ['/Text/ImageC']},
                                                                               'Rotate': IndirectObjectRef(0),
                                                                               'Trans': {}}})


def test_StringLiterals():
    l1 = """/Producer (MiKTeX pdfTeX-1.40.21)
           /Creator (TeX)
           /CreationDate (D:20200504155420+02'00')
           /ModDate (D:20200504155420+02'00')
           /Trapped /False
           /PTEX.Fullbanner (This is MiKTeX-pdfTeX 2.9.7338 (1.40.21))"""
    assert (parseDict(l1) == {'Producer': '(MiKTeX pdfTeX-1.40.21)', 'Creator': '(TeX)', 'CreationDate': "(D:20200504155420+02'00')",
                              'ModDate': "(D:20200504155420+02'00')",
                              'Trapped': 'False',
                              'PTEX.Fullbanner': '(This is MiKTeX-pdfTeX 2.9.7338 (1.40.21))'})

    l2 = """/Author()/Title()/Subject()/Creator(\376\377\000L\000a\000T\000e\000X\000\040\000v\000i\000a\000\040\000p\000a\000n\000d\000o\000c)/Producer(pdfTeX-1.40.20)/Keywords()
    /CreationDate (D:20200419154240+02'00')
    /ModDate (D:20200419154240+02'00')
    /Trapped /False
    /PTEX.Fullbanner (This is pdfTeX, Version 3.14159265-2.6-1.40.20 (TeX Live 2019) kpathsea version 6.3.1)"""

    assert (parseDict(l2) =={'Author': '()', 'Title': '()', 'Subject': '()',
                             'Creator': '(þÿ\x00L\x00a\x00T\x00e\x00X\x00 \x00v\x00i\x00a\x00 \x00p\x00a\x00n\x00d\x00o\x00c)',
                             'Producer': '(pdfTeX-1.40.20)',
                             'Keywords': '()', 'CreationDate': "(D:20200419154240+02'00')",
                             'ModDate': "(D:20200419154240+02'00')",
                             'Trapped': 'False',
                             'PTEX.Fullbanner': '(This is pdfTeX, Version 3.14159265-2.6-1.40.20 (TeX Live 2019) kpathsea version 6.3.1)'}
)


def test_multiline():
    t1 = """/Type /ObjStm
/N 68
/First 522
/Length 2786      
/Filter /FlateDecode"""
    assert parseDict(t1) == {'Type': 'ObjStm', 'N': "68",
                             'First': "522",
                             'Length': "2786", 'Filter': 'FlateDecode'}


