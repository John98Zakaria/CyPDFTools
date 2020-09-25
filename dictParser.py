import re

address_match = re.compile(r"\d+ \d R")

test2 = """/Font 10 0 R
/ProcSet[/PDF/Text]
"""

test3 = """/Type /FontDescriptor
/FontName /RYPXUZ+CMR12
/Flags 4
/FontBBox [-34 -251 988 750]
/Ascent 694
/CapHeight 683
/Descent -194
/ItalicAngle 0
/StemV 65
/XHeight 431
/CharSet (/A/B/D/Delta/E/F/G/H/I/J/K/L/M/N/O/P/R/S/T/U/V/W/Z/a/at/b/c/colon/comma/d/dieresis/e/eight/equal/f/ff/fi/five/four/g/germandbls/h/hyphen/i/j/k/l/m/n/nine/numbersign/o/one/p/parenleft/parenright/percent/period/plus/q/question/r/s/seven/six/slash/t/three/two/u/v/w/x/y/z/zero)
/FontFile 53 0 R"""

test1 = """/Type /FontDescriptor
/FontName /PJZRLC+CMR6
/Flags 4
/FontBBox [-20 -250 1193 750]
/Ascent 694
/CapHeight 683
/Descent -194
/ItalicAngle 0
/StemV 83
/XHeight 431
/CharSet (/two)
/FontFile 55 0 R"""


test4 = """/Type /Group
/S /Transparency
/CS /DeviceRGB
>>
endobj
14 0 obj
<<
/Font << /F31 5 0 R /F32 4 0 R /F33 10 0 R >>
/XObject << /Im1 13 0 R >>
/ProcSet [ /PDF /Text ]"""

trailler = """<< /Size 65
/Root 63 0 R
/Info 64 0 R
/ID [<C3FA9E8A54723B66323582D170F24DFE> <C3FA9E8A54723B66323582D170F24DFE>] >>"""


tests = [test1, test2,test3,test4,trailler]


def cleanEnd(input:str):
    if input[-1] in "\n\t ":
        return input[:-1]
    return input

def parseDict(l):
    listIter = iter(l)
    out = dict()

    for i in listIter:
        spiltted = i.split(" ",1)
        if("") in spiltted:
            spiltted.remove("")
        itemLen = len(spiltted)
        if(i == ""):
            continue
        if(itemLen==2):
            if(spiltted[1]=="("):
                temp = list()
                for setItem in listIter:
                    if ")" in setItem:
                        break
                    temp.append(cleanEnd(setItem))
                out[spiltted[0]] =temp
                continue

            if "[" in spiltted[1]:
                temp = list()
                for setItem in listIter:
                    if "]" in setItem:
                        break
                    temp.append(cleanEnd(setItem))
                out[spiltted[0]] = temp
                continue


            out[spiltted[0]] = cleanEnd(spiltted[1])
        elif(itemLen==1):
            key = i
            i = next(listIter)
            value = cleanEnd(i)
            out[key] = value

    return out


def regexParser(input):
    parser = re.compile(r"\/(\w+) ?(.*)")
    res = parser.findall(input)
    return dict(res)

if __name__ == '__main__':
    for t in tests:
        print(regexParser(t))