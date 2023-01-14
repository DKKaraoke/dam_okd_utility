import bitstring
from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger

__logger = getLogger('OkdMidi')

def read_delta_time(stream: bitstring.BitStream):
    byte_1: int = stream.read('uint:8')
    if byte_1 < 0x40:
        return byte_1
    byte_2: int = stream.read('uint:8')
    if byte_2 < 0x40:
        return byte_2 * 0x40 + byte_1
    byte_3: int = stream.read('uint:8')
    if byte_3 < 0x40:
        return byte_3 * 0x1000 + byte_2 * 0x40 + byte_1

    __logger.warning('Failed to read delta time.')

def read_extended_delta_time(stream: bitstring.BitStream):
    total_duration = 0
    while True:
        first_byte: int = stream.peek('uint:8')
        if first_byte & 0x80 == 0x80 or first_byte == 0x00:
            break

        delta_time = read_delta_time(stream)
        if delta_time is None:
            break
        total_duration += delta_time

    return total_duration

class OkdMidiGenericEvent(NamedTuple):
    data: bytes
    absolute_tick: int
