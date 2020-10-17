from collections import defaultdict
import numpy as np
import io
from PDFStructureObjects import XrefEntry, XRefTable


# https://www.w3.org/TR/PNG/#9Filters

def png_algorithmPipeline(decoded_stream: bytes, number_of_columns: int, algorithm_id: int) -> bytes:
    """
    Takes a png image to decompress its contents

    :param decoded_stream: png as bytes
    :param number_of_columns: number of columns in the image
    :param algorithm_id: algorithm to be applied
    :return: png decoded as bytes
    """
    if algorithm_id == 10:  # png was decoded with the none filter nothing to be done
        return decoded_stream

    # convert pdf png algorithm number to standard
    algorithm_id = algorithm_id - 10 if algorithm_id > 10 else algorithm_id
    filter_algorithms = {1: reverse_subFilter,
                         2: reverse_upFilter,
                         3: reverse_averageFilter,
                         4: reverse_paethFilter}

    reshaped_stream = reshape_toMatrix(decoded_stream, number_of_columns)
    applied_alg_steam = filter_algorithms[algorithm_id](reshaped_stream)

    return matrix_toBytes(applied_alg_steam)


def reshape_toMatrix(data: bytes, number_of_columns) -> np.array:
    """
    Reshapes bytes to a matrix

    :param data: bytes to be reshaped
    :param number_of_columns:
    :return: A matrix representing the image
    """
    big_endian = np.dtype(np.ubyte).newbyteorder(">")
    value = np.frombuffer(data, big_endian)
    value = np.reshape(value, (len(value) // (number_of_columns + 1), number_of_columns + 1))

    return value


def reverse_subFilter(png_array: np.array) -> np.array:
    raise NotImplemented("reverse sub filter yet to be implemented")


def reverse_averageFilter(png_array: np.array) -> np.array:
    raise NotImplemented("reverse average filter yet to be implemented")


def reverse_paethFilter(png_array: np.array) -> np.array:
    raise NotImplemented("reverse paeth filter yet to be implemented")


def reverse_upFilter(png_array: np.array) -> np.array:
    """
    Reverses the png upFilter

    :param png_array: A matrix representing the png image
    """

    png_array = np.delete(png_array, 0, 1)  # Remove the column that specifies the algorithm number

    for i in range(1, len(png_array)):
        png_array[i] = png_array[i] + png_array[i - 1]
        png_array[i] = png_array[i] & 0xff

    return png_array


def decode_XRef(png_matrix: np.array, W):
    # png_matrix = png_matrix.tobytes()
    decompressed_trailer = io.BytesIO(png_matrix)
    size = decompressed_trailer.getbuffer().nbytes
    compressed_objects = defaultdict(list)
    ExtractedXRef = XRefTable([], True)

    while decompressed_trailer.tell() != size:
        field_1 = int.from_bytes(decompressed_trailer.read(W[0]), "big")
        field_2 = int.from_bytes(decompressed_trailer.read(W[1]), "big")
        field_3 = int.from_bytes(decompressed_trailer.read(W[2]), "big")
        if field_1 == 0:
            ExtractedXRef.table.append(XrefEntry(field_2, field_3, "f"))
        elif field_1 == 1:
            ExtractedXRef.table.append(XrefEntry(field_2, field_3, "n"))
        elif field_1 == 2:
            compressed_objects[field_2].append(field_3)
        else:
            raise AssertionError()

    print(ExtractedXRef)
    print(compressed_objects)


def matrix_toBytes(matrix: np.array) -> bytes:
    """
    Converts a matrix to variable sized bytes

    :param matrix: png matrix
    :return: variable sized bytes representation of the numbers in the matrix
    """
    encoded_matrix = matrix.tobytes()
    return encoded_matrix


if __name__ == '__main__':
    xref = b'\x02\x01\x00\x10\x00\x02\x00\x03\xd6\x00\x02\x00\x01\xad\x00\x02\x00\x01Y\x00\x02\x00\x05^\x00\x02\x00\x06\xe7\x00\x02\x00\x03\xf7\x00\x02\x00\x01$\x00\x02\x00\n[\x00\x02\x00\x03\xa2\x00\x02\x00\x01/\x00\x02\x00}\xa1\x00\x02\x00a[\x00\x02\x01%\t\x00\x02\x00\x00\x00\x01\x02\x00\x00\x00\x01\x02\x00\x00\x00\x01\x02\x00\x00\x00\x01\x02\x00\x00\x00\x01\x02\x00\x00\x00\x01\x02\x00\x00\x00\x01\x02\x00\x00\x00\x01\x02\x00\x00\x00\x01\x02\x00\x00\x00\x01\x02\xff\xdci\xf6'
    xref_encoded = reshape_toMatrix(xref, 4)

    encoding_free = reverse_upFilter(xref_encoded)

    print(encoding_free)
    bts = matrix_toBytes(encoding_free)

    print(decode_XRef(bts, [1, 2, 1]))
    print()
