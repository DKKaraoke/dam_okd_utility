import bitstring
from typing import NamedTuple, Union

from dam_okd_utility.customized_logger import getLogger

__logger = getLogger("OkdMidi")


def read_status_byte(stream: bitstring.BitStream):
    byte: int = stream.read("uint:8")
    if byte & 0x80 != 0x80:
        position = stream.bytepos
        raise ValueError(f"Invalid status byte. byte={byte} position={position}")
    return byte


def peek_status_byte(stream: bitstring.BitStream):
    byte: int = stream.peek("uint:8")
    if byte & 0x80 != 0x80:
        position = stream.bytepos
        raise ValueError(f"Invalid status byte. byte={byte} position={position}")
    return byte


def read_data_byte(stream: bitstring.BitStream):
    byte: int = stream.read("uint:8")
    if byte & 0x80 == 0x80:
        position = stream.bytepos
        raise ValueError(f"Invalid data byte. byte={byte} position={position}")
    return byte


def peek_data_byte(stream: bitstring.BitStream):
    byte: int = stream.peek("uint:8")
    if byte & 0x80 == 0x80:
        position = stream.bytepos
        raise ValueError(f"Invalid data byte. byte={byte} position={position}")
    return byte


def is_data_bytes(data: bytes):
    for byte in data:
        if byte & 0x80 == 0x80:
            return False
    return True


def read_variable_int(stream: bitstring.BitStream):
    value = 0
    for i in range(3):
        byte: int = read_data_byte(stream)
        value += byte << (i * 6)
        if byte & 0x40 != 0x40:
            return value

    position = stream.bytepos
    raise ValueError(f"Invalid byte sequence. position={position}")


def write_variable_int(stream: bitstring.BitStream, value: int):
    if 0x04103F < value:
        raise ValueError("Too big value. Use write_extended_variable_int.")

    if value == 0x000000:
        stream.append(b"\x00")
        return

    for i in range(3):
        masked_value = value & (0x3F << (i * 6))
        byte = masked_value >> (i * 6)
        next_value = value - masked_value
        if next_value != 0x000000:
            byte |= 0x40
            next_value -= 0x40 << (i * 6)
        value = next_value

        stream.append(bitstring.pack("uint:8", byte))

        if value == 0x000000:
            if byte & 0x40:
                stream.append(b"\x00")
            break


def read_extended_variable_int(stream: bitstring.BitStream):
    total_duration = 0
    while True:
        try:
            byte = peek_data_byte(stream)
            if byte == 0x00:
                stream.bytepos += 1
                break
        except ValueError:
            break

        total_duration += read_variable_int(stream)

    return total_duration


def write_extended_variable_int(stream: bitstring.BitStream, value: int):
    if value == 0x000000:
        return

    while 0x000000 < value:
        write_value = min(value, 0x04103F)
        write_variable_int(stream, write_value)
        value -= write_value


class OkdMidiGenericMessage(NamedTuple):
    delta_time: int
    data: bytes
    duration: int


# OkdMidiMessage = Union[OkdMidiGenericMessage]
OkdMidiMessage = OkdMidiGenericMessage
