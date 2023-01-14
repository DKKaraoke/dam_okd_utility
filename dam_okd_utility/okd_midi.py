import bitstring
from typing import NamedTuple, Union

from dam_okd_utility.customized_logger import getLogger

__logger = getLogger('OkdMidi')


def read_status_byte(stream: bitstring.BitStream):
    byte: int = stream.read('uint:8')
    if byte & 0x80 != 0x80:
        raise ValueError('Invalid status byte.')
    return byte


def peek_status_byte(stream: bitstring.BitStream):
    byte: int = stream.peek('uint:8')
    if byte & 0x80 != 0x80:
        raise ValueError('Invalid status byte.')
    return byte


def read_data_byte(stream: bitstring.BitStream):
    byte: int = stream.read('uint:8')
    if byte & 0x80 == 0x80:
        raise ValueError('Invalid data byte.')
    return byte


def peek_data_byte(stream: bitstring.BitStream):
    byte: int = stream.peek('uint:8')
    if byte & 0x80 == 0x80:
        raise ValueError('Invalid data byte.')
    return byte


def read_variable_int(stream: bitstring.BitStream):
    value = 0
    for i in range(3):
        byte: int = read_data_byte(stream)
        value = (byte << (i * 6)) + value
        if byte & 0x40 != 0x40:
            return value

    raise ValueError('Invalid byte sequence.')


def read_extended_variable_int(stream: bitstring.BitStream):
    total_duration = 0
    while True:
        first_byte: int
        try:
            first_byte = peek_data_byte(stream)
        except ValueError:
            break
        # if first_byte == 0x00:
        #     break

        total_duration += read_variable_int(stream)

    return total_duration


# class OkdMidiGenericEvent(NamedTuple):
#     data: bytes
#     absolute_tick: int

# class OkdMidiDeltaTime(NamedTuple):
#     tick: int


class OkdMidiGenericMessage(NamedTuple):
    delta_time: int
    data: bytes
    duration: int


OkdMidiMessage = OkdMidiGenericMessage

# OkdMidiMessage = Union[OkdMidiDeltaTime, OkdMidiGenericMessage]
