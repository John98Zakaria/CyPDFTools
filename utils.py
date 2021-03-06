from io import BytesIO, SEEK_CUR, SEEK_END
SEPERATORS = b"\\/[]<>()\t\n\r"


class ObjectIter:
    """
    Used to iterate over objects
    """

    def __init__(self, stream: bytes, pointer=0):
        """
        :param stream: Any object that `BytesIO <https://docs.python.org/3/library/io.html#io.BytesIO>` supports
        :param pointer: A pointer to the start index
        """
        self.stream = BytesIO(stream)
        self.length = self.stream.getbuffer().nbytes
        self.deb = stream
        self._clean()

    def _clean(self):
        """
        Increments the iterable to the next non space character
        """
        while self.peek(1).isspace():
            self.stream.seek(1, SEEK_CUR)

    def __len__(self):
        return self.length

    def __iter__(self):
        return self

    def __next__(self):
        byte = self.stream.read(1)
        if byte == b"":
            raise StopIteration
        return byte

    def prev(self) -> bytes:
        """
        Decrements the counter

        :return: Previous element

        """
        self.stream.seek(-2, SEEK_CUR)
        return self.stream.read(1)

    def move_pointer(self, n: int) -> None:
        """
        Moves the pointer n characters

        :param n: Number of characters
        """
        self.stream.seek(n, SEEK_CUR)

    def move_to(self, item: bytes):
        """
        Moves the iterator to given item

        :param item: item to move to
        :return: Items since the beginning of iteration till end
        """
        pointerStart = self.stream.tell()
        nextbyte = self.peek(1)
        while nextbyte != item:
            if self.stream.tell() == self.length:
                pointer = self.stream.tell()
                self.stream.seek(-1, SEEK_CUR)
                pointer = self.stream.tell()
                countClosingBraces = 0
                curr = self.stream.read(1)
                pointer = self.stream.tell()
                while countClosingBraces != 2:
                    pointer = self.stream.tell()
                    countClosingBraces += curr == b">"
                    self.stream.seek(-2, SEEK_CUR)
                    curr = self.stream.read(1)

                poiterEnd = self.stream.tell()
                self.stream.seek(pointerStart - poiterEnd, SEEK_CUR)
                return self.stream.read(poiterEnd - pointerStart)
            if self.stream.tell() <= self.length:
                self.stream.read(1)
                nextbyte = self.peek(1)
            else:
                raise IndexError(f"{item} not found")

        poiterEnd = self.stream.tell()
        self.stream.seek(pointerStart - poiterEnd, SEEK_CUR)
        value = self.stream.read(poiterEnd - pointerStart)
        return value

    def skip_space(self) -> None:
        """
        Moves stream to the next non whitespace char

        :param stream: Any iterable object
        """
        peek = self.peek(1)
        if not peek.isspace() or peek == b"":
            return

        for i in self:
            if not i.isspace():
                self.prev()
                return

    def finish_number(self) -> bytes:
        """
        Move stream until a separating character is found

        :return: Resulting int
        """
        rest = b""
        for char in iter(self):
            if char in SEPERATORS:
                break
            rest += char
        self.prev()  # Move back in order to preserve type token for next item
        return rest

    def peek(self, n: int = 1):
        """
        Returns the next n chars without incrementing the counter

        :param n: number of characters
        :return: Returns the next n chars without incrementing the counter
        """
        prepeak = self.stream.tell()
        out_string = self.stream.read(n)
        self.stream.seek(prepeak)
        if (self.stream.tell() == self.length):
            return out_string
        return out_string

    def reversePeek(self, n: int = 1) -> bytes:
        """
        Returns the previous n chars without incrementing the counter

        :param n: number of characters
        :return: Returns the next n chars without incrementing the counter
        """
        prepeak = self.stream.tell()
        self.stream.seek(-n - 1, SEEK_CUR)
        out_string = self.stream.read(n)
        self.stream.seek(prepeak)
        return out_string


class Ibytable:


    def __bytes__(self):
        raise NotImplementedError("__bytes__ was not implemented")

    def __eq__(self, other):
        raise NotImplementedError("__eq__ was not implemented")

    def offset_references(self, offset: int):
        raise NotImplementedError("offset_references was not implemented")

    def __repr__(self):
        return self.__str__()
