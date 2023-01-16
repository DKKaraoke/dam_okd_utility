import bitstring
import math


def dump_memory(data: list[int], chunk_size=16, bytes_per_sep=" "):
    output = ""

    data_length = len(data)
    chunk_count = math.floor(data_length / chunk_size)
    fraction_length = data_length % chunk_size

    stream = bitstring.BitStream(bytearray(data))
    for i in range(chunk_count - 1):
        address = chunk_size * i
        chunk: bytes = stream.read(8 * chunk_size).bytes
        output += format(address, "06X") + "    " + chunk.hex(bytes_per_sep) + "\n"

    if fraction_length == 0:
        return output

    address = chunk_size * chunk_count
    fraction: bytes = stream.read(8 * chunk_size).bytes
    output += format(address, "06X") + "    " + fraction.hex(bytes_per_sep) + "\n"

    return output
