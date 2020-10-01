from utillsCythonized cimport ObjectIter
from PDFObjects import *

cdef readonly bytes SEPERATORS = b"\\/[]<>() \t\n"


cdef bytes extract_name(ObjectIter stream):
    """
    Extracts the next name from the iterator (7.3.5 PDF 32000-1:2008)
    :param stream:A stream whose forward slash / was just consumed
    :return: String containing the name
    """
    cdef bytes out_bytes
    cdef bytes letter
    out_bytes = b"/"
    for letter in stream:
        if (letter in SEPERATORS):
            stream.prev()  # Reverts a step back to where
            # the name ended in order for the typechecker to deduce the type
            break
        out_bytes += letter
    return out_bytes


cdef void skip_space(ObjectIter stream):
    """
    Moves stream to the next non whitespace char
    :param stream: Any iterable object
    :return: First letter after the whitespace
    """
    cdef bytes peek
    peek = stream.peek(1)
    if (not peek.isspace() or peek == b""):
        return
    cdef bytes i
    for i in stream:

        if (not i.isspace()):
            stream.prev()
            return


cdef bytes parse_string_literal(ObjectIter stream) :
    """
    Parses string literals (7.3.4.2) PDF 32000-1:2008
    :param stream: A stream whose opening round bracket ( was just consumed
    :return: The string literal including the round brackets
    """

    cdef bytes out_string_literal
    cdef int countOpeningBraces
    cdef int countClosingBraces
    cdef bytes letter
    out_string_literal = b"("
    countOpeningBraces = 1
    countClosingBraces = 0
    for letter in stream:
        if countClosingBraces == countOpeningBraces:
            break
        if letter == b"(":
            countOpeningBraces +=  stream.reversePeek(1)!=b"\\"
        elif letter == b")":
            countClosingBraces += stream.reversePeek(1)!=b"\\"
        out_string_literal += letter
    stream.prev()
    return out_string_literal


cpdef parse_numeric(bytes init ,ObjectIter stream):
    cdef bytes number
    cdef bytes letter
    cdef bint isRef
    cdef bytes upcomingchars
    number = init
    for letter in stream:
        if (letter in b"\\/[]<>()\t\n"):
            stream.prev()
            break
        elif (letter == b" "):
            upcomingchars = stream.peek(3)
            isRef = upcomingchars == b"0 R"
            if isRef:
                stream.move_pointer(3)
                return IndirectObjectRef(number)
            else:
                return number
        elif not letter.isdigit() and letter != b".":
            number += stream.finish_number()
            break
        number += letter
    return number


def parse_stream(streamIter:ObjectIter, letter=None):
    if (letter is None):
        letter = next(streamIter)

    debug = letter.decode("utf-8")
    if letter == b"/":
        value = extract_name(streamIter)

    elif letter == b"[":
        value = extract_array(streamIter)

    elif letter.isdigit() or letter == b"-":
        value = parse_numeric(letter, streamIter)

    elif letter == b"<":
        letter = next(streamIter)
        if letter == b"<":
            value = parse_dictionary(streamIter)
        else:
            value = b"<" + letter + streamIter.move_to(b">") + b">"
            try:
                next(streamIter)
            except StopIteration:
                return value

    elif letter == b"(":
        value = parse_string_literal(streamIter)
    elif letter in b"tf":  # handels true/false
        value = letter + streamIter.move_to(b"e") + next(streamIter)
    elif letter == b"n":  # handels null values
        peek = streamIter.peek(3)
        if (peek == b"ull"):
            value = b"null"
            streamIter.move_pointer(3)

    skip_space(streamIter)

    return value


cpdef  parse_dictionary(ObjectIter streamIter):
    cdef dict object_dict
    cdef bytes letter
    cdef bytes key
    object_dict = dict()
    streamIter._prepare_dictparse()

    for letter in streamIter:
        # Parse Key

        if letter == b">":
            letter = next(streamIter)
            if (letter == b">"):
                return PDFDict(object_dict)

        elif letter != b"/":
            raise AssertionError(f"Expected a forward slash / to build a dict key but got {letter}")
        key = extract_name(streamIter)
        skip_space(streamIter)
        letter = next(streamIter)
        # parse value
        value = parse_stream(streamIter, letter)

        object_dict[key] = value

    return PDFDict(object_dict)


cpdef extract_array(ObjectIter stream):
    cdef bytes out_bytes
    cdef int count_closingBraces
    cdef int count_openingBraces
    cdef bytes letter
    out_bytes = b""
    count_closingBraces = 0
    count_openingBraces = 1

    for letter in stream:
        if letter == b"]":
            count_closingBraces += 1
        elif letter == b"[":
            count_openingBraces += 1
        if count_closingBraces==count_openingBraces:
            break
        out_bytes += letter

    return PDFArray(parse_arrayObjects(out_bytes))


cpdef list parse_arrayObjects(bytes array_bytes):
    cdef list array
    cdef bytes letter
    cdef ObjectIter stream_iter
    stream_iter = ObjectIter(array_bytes)
    array = []
    for letter in stream_iter:
        if (letter.isspace()):
            continue
        item = parse_stream(stream_iter, letter)
        array.append(item)

    return array


