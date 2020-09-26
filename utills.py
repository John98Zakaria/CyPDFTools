class BidirectionalIterator:

    def __init__(self, iterable, pointer=-1):
        """
        :param iterable: Any object that supports __getitem__ ([index] operator)
        :param pointer: A pointer to the start index
        """
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

    def prev(self)->any:
        """
        Decrements the counter
        :return: Previous element
        """
        self.pointer -= 1
        if (self.pointer < 0):
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
                if(self.iterable[self.pointer-1]==">"): #Reached end of dict
                    return self.iterable[pointerStart:self.pointer ]
                else:
                    raise IndexError(f"{item} not found")
        self.pointer -= 1
        return self.iterable[pointerStart:self.pointer + 1]

    def peek(self):
        """
        :return: Current item without incrementing the pointer
        """
        return self.iterable[self.pointer]

