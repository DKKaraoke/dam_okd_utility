import io
import os
from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger


class OkdMTrackMessage(NamedTuple):
    """DAM OKD M-Track Message
    """

    time: int
    data: bytes


class OkdMTrackChunk(NamedTuple):
    """DAM OKD M-TrackChunk
    """

    __logger = getLogger('OkdMTrackChunk')

    @staticmethod
    def __read_duration(stream: io.BufferedReader):
        byte_1_buffer = stream.read(1)
        if len(byte_1_buffer) != 1:
            return
        byte_1 = byte_1_buffer[0]
        if byte_1 < 0x40:
            return byte_1
        byte_2_buffer = stream.read(1)
        if len(byte_2_buffer) != 1:
            raise RuntimeError('Invalid byte_2_buffer length.')
        byte_2 = byte_2_buffer[0]
        if byte_2 < 0x40:
            return byte_1 * 0x40 + byte_1
        byte_3_buffer = stream.read(1)
        if len(byte_1_buffer) != 1:
            raise RuntimeError('Invalid byte_3_buffer length.')
        byte_3 = byte_3_buffer[0]
        if byte_3 < 0x40:
            return byte_3 * 0x1000 + byte_2 * 0x40 + byte_1
        raise RuntimeError('Failed to read duration.')

    @staticmethod
    def read(stream: io.BufferedReader):
        messages: list[OkdMTrackMessage] = []

        time = 0
        while True:
            message_id_buffer = stream.read(1)
            if len(message_id_buffer) != 1:
                break
            message_id = message_id_buffer[0]
            if message_id & 0x80 == 0x80:
                data_buffer = message_id_buffer
                if message_id == 0xf1:
                    data_buffer += stream.read(2)
                    if len(data_buffer) != 3:
                        raise RuntimeError('Invalid data_buffer length.')
                elif message_id == 0xf2:
                    data_buffer += stream.read(1)
                    if len(data_buffer) != 2:
                        raise RuntimeError('Invalid data_buffer length.')
                elif message_id == 0xf3:
                    data_buffer += stream.read(1)
                    if len(data_buffer) != 2:
                        raise RuntimeError('Invalid data_buffer length.')
                elif message_id == 0xf4:
                    data_buffer += stream.read(1)
                    if len(data_buffer) != 2:
                        raise RuntimeError('Invalid data_buffer length.')
                elif message_id == 0xf5:
                    pass
                elif message_id == 0xf6:
                    data_buffer += stream.read(1)
                    if len(data_buffer) != 2:
                        raise RuntimeError('Invalid data_buffer length.')
                elif message_id == 0xf8:
                    data_buffer += stream.read(1)
                    if len(data_buffer) != 2:
                        raise RuntimeError('Invalid data_buffer length.')
                elif message_id == 0xff:
                    while True:
                        current_byte_buffer = stream.read(1)
                        if len(current_byte_buffer) != 1:
                            raise RuntimeError(
                                'Invalid current_byte_buffer length.')
                        if current_byte_buffer[0] == 0xfe:
                            stream.seek(-1, os.SEEK_CUR)
                            break
                        data_buffer += current_byte_buffer
                else:
                    while True:
                        current_byte_buffer = stream.read(1)
                        if len(current_byte_buffer) != 1:
                            raise RuntimeError(
                                'Invalid current_byte_buffer length.')
                        if 0xf1 <= current_byte_buffer[0]:
                            stream.seek(-1, os.SEEK_CUR)
                            break
                        data_buffer += current_byte_buffer
                messages.append(OkdMTrackMessage(time, data_buffer))
            else:
                duration = OkdMTrackChunk.__read_duration(stream)
                if duration is None:
                    break
                time += duration

        return OkdMTrackChunk(messages)

    messages: list[OkdMTrackMessage]
