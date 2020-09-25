from io import StringIO


class MyIterator:
    def __init__(self, iterable,pointer=-1):
        self.iterable = iterable
        self.pointer = pointer
        self.length = len(iterable)


    def __len__(self):
        return self.length

    def __iter__(self):
        return self

    def __next__(self):
        self.pointer += 1
        if (self.pointer >= self.length):
            raise StopIteration
        return self.iterable[self.pointer]

    def prev(self):
        self.pointer -= 1
        if (self.pointer < 0):
            raise StopIteration
        return self.iterable[self.pointer]

    def movetoDelemiter(self, delimiter):
        pointerStart = self.pointer
        while (self.iterable[self.pointer] != delimiter):
            self.pointer += 1
            if (self.pointer == self.length):
                raise IndexError("Delimiter not found")
        self.pointer -= 1
        return self.iterable[pointerStart:self.pointer + 1]

    def peek(self):
        return self.iterable[self.pointer]


def getString(stream:MyIterator):
    out_string = ""
    for letter in stream:
        if (not letter.isalnum()):
            stream.prev()
            break
        out_string += letter
    return out_string


def skipSpace(stream):
    for letter in stream:
        if (not letter.isspace()):
            return letter

def parseList(stream):
    out_string = ""
    for letter in stream:
        if letter == "]":
            break
        out_string += letter
    return out_string.strip().split(" ")



class IndirectObjectRef:
    def __init__(self,objectref):
        self.objectref = objectref

    def __str__(self):
        return f"{self.objectref} 0 R"

    def __repr__(self):
        return self.__str__()

    def addOffset(self,offset):
        self.objectref +=offset





def parseNumeric(init,stream:MyIterator):
    number:str = init
    for char in stream:
        number+=char
        if(not number.isnumeric() or char=="/"):
            stream.movetoDelemiter("/")
            return IndirectObjectRef(number[:-1])
    return number



def parseDict(pdf_stream):
    object_dict = dict()
    streamIter = MyIterator(pdf_stream) if type(pdf_stream) != MyIterator else pdf_stream
    for letter in streamIter:
        #Parse Key
        if (letter == ">"):
            letter = next(streamIter)
            if (letter == ">"):
                return object_dict

        elif (letter != "/"):
            raise AssertionError("Key must be a string")
        key = getString(streamIter)
        letter = skipSpace(streamIter)
        if(key=="ProcSet"):
            print("pro")
        #parse value



        if (letter == "/"):
            value = getString(streamIter)

        elif (letter=="["):
            value = parseList(streamIter)

        elif (letter.isnumeric()):
            value = parseNumeric(letter,streamIter)

        elif (letter == "<"):
            letter = next(streamIter)
            if(letter=="<"):
                value = parseDict(streamIter)
            else:
                value = letter+ streamIter.movetoDelemiter(">")

        elif(letter==">"):
            letter = next(streamIter)
            if(letter==">"):
                return object_dict

        object_dict[key] = value

    return object_dict

if __name__ == '__main__':
    t = r"""/Type/Page/BleedBox[ 0 0 504 661.5]/Contents 5 0 R/CropBox[ 0 0 504 661.5]/MediaBox[ 0 0 504 661.5]/Parent 3493 0 R/Resources<</Font<</F3 2186 0 R>>/ProcSet[/Text/ImageC]>>/Rotate 0/Trans<<>>>>"""

    print(parseDict(t))