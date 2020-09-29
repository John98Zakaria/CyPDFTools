SEPERATORS = "\\/[]<> ()\t\n"


class ObjectIter:

    def __init__(self, iterable, pointer=-1):
        """
        :param iterable: Any object that supports __getitem__ ([index] operator)
        :param pointer: A pointer to the start index
        """
        self.iterable = iterable
        self.pointer = pointer
        self.length = len(iterable)
        self._clean()

    def _clean(self):
        """
        Removes endobj/stream from iterator
        :return:
        """
        trailler = self.iterable[-6:]
        if (trailler in ["endobj", "stream"]):
            self.length -= 6

    def prepareDictParse(self) -> None:
        """
        Moves the Pointer to the item preceding a forward slash /
        """
        self.moveto("/")

    def __len__(self):
        return self.length

    def __iter__(self):
        return self

    def __next__(self):
        self.pointer += 1
        if (self.pointer >= self.length):
            raise StopIteration
        return self.iterable[self.pointer]

    def prev(self) -> any:
        """
        Decrements the counter
        :return: Previous element
        """
        self.pointer -= 1
        if (self.pointer < -1):
            raise StopIteration
        return self.iterable[self.pointer]

    def moveto(self, item):
        """
        Moves the iterator to given item
        :param item: item to move to
        :return: Items since the beginning of iteration till end
        """
        pointerStart = self.pointer
        while (self.iterable[self.pointer] != item):
            self.pointer += 1
            if (self.pointer == self.length):
                countClosingBraces = 0
                self.pointer -= 1
                while (countClosingBraces != 2):
                    countClosingBraces += self.iterable[self.pointer] == ">"
                    self.pointer -= 1
                return self.iterable[pointerStart:self.pointer + 1]
            elif (self.pointer <= self.length):
                continue
            else:
                raise IndexError(f"{item} not found")
        self.pointer -= 1

        return self.iterable[pointerStart:self.pointer + 1]


    def finishNumber(self):
        rest = ""
        for char in iter(self):
            if char in "<>\\/\n\t":
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
        try:
            self.iterable[self.pointer+n+1]
            out_string = self.iterable[self.pointer+1:self.pointer+n+1]
        except IndexError:
            #todo investigate bug
            return self.iterable[self.pointer+1:self.pointer+n+1]

        return out_string
