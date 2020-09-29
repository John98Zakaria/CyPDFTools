SEPERATORS = "\\/[]<> ()\t\n"

from io import BytesIO,SEEK_CUR,SEEK_SET,SEEK_END

class ObjectIter:

    def __init__(self, iterable:bytes, pointer=0):
        """
        :param iterable: Any object that supports __getitem__ ([index] operator)
        :param pointer: A pointer to the start index
        """
        self.iterable = BytesIO(iterable)
        self.iterable.seek(pointer)
        self.length = self.iterable.seek(0,SEEK_END)
        self.deb = iterable
        self.iterable.seek(0)
        self._clean()

    def _clean(self):
        """
        Removes endobj/stream from iterator
        :return:
        """
        while self.peek(1).isspace():
            self.iterable.seek(1,SEEK_CUR)

    def prepareDictParse(self) -> None:
        """
        Moves the Pointer to the item preceding a forward slash /
        """
        self.moveto(b"/")

    def __len__(self):
        return self.length

    def __iter__(self):
        return self

    def __next__(self):

        po = self.iterable.tell()
        byte = self.iterable.read(1)
        if(byte==b""):
            raise StopIteration
        return byte

    def prev(self) -> any:
        """
        Decrements the counter
        :return: Previous element
        """
        self.iterable.seek(-2,SEEK_CUR)
        return self.iterable.read(1)

    def move_poiter(self,n):
        self.iterable.seek(n,SEEK_CUR)

    def moveto(self, item):
        """
        Moves the iterator to given item
        :param item: item to move to
        :return: Items since the beginning of iteration till end
        """
        pointerStart = self.iterable.tell()
        nextbyte = self.peek(1)
        while (nextbyte != item):
            if (self.iterable.tell() == self.length):
                countClosingBraces = 0
                while (countClosingBraces != 2):
                    countClosingBraces += self.iterable.read(1) == b">"
                poiterEnd = self.iterable.tell()
                self.iterable.seek(pointerStart - poiterEnd, SEEK_CUR)
                return self.iterable.read(poiterEnd-pointerStart)
            elif (self.iterable.tell() <= self.length):
                self.iterable.read(1)
                nextbyte = self.peek(1)
                continue
            else:
                raise IndexError(f"{item} not found")

        poiterEnd = self.iterable.tell()
        self.iterable.seek(pointerStart-poiterEnd,SEEK_CUR)
        value = self.iterable.read(poiterEnd-pointerStart)
        return  value


    def finishNumber(self):
        rest = b""
        for char in iter(self):
            if char in b"<>\\/\n\t":
                break
            rest+=char
        self.prev()
        return rest


    def peek(self,n=1):
        """
        Returns the next n chars without incrementing the counter
        :param n: number of characters
        :return: Returns the next n chars without incrementing the counter
        """
        out_string = self.iterable.read(n)
        if(self.iterable.tell()==self.length):
            return out_string
        self.iterable.seek(-n,SEEK_CUR)
        return out_string