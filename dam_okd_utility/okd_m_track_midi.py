import io
import os

from dam_okd_utility.okd_midi import OkdMidiDeltaTime, OkdMidiGenericEvent, OkdMidiMessage


class OkdMTrackMidi:
    @staticmethod
    def __read_delta_time(stream: io.BufferedReader):
        byte_1_buffer = stream.read(1)
        if len(byte_1_buffer) != 1:
            raise RuntimeError('Invalid byte_1_buffer length.')
        byte_1 = byte_1_buffer[0]
        if byte_1 & 0x40 == 0x00:
            return byte_1

        byte_2_buffer = stream.read(1)
        if len(byte_2_buffer) != 1:
            raise RuntimeError('Invalid byte_2_buffer length.')
        byte_2 = byte_2_buffer[0]
        if byte_2 & 0x40 == 0x00:
            return byte_2 * 0x40 + byte_1

        byte_3_buffer = stream.read(1)
        if len(byte_3_buffer) != 1:
            raise RuntimeError('Invalid byte_3_buffer length.')
        byte_3 = byte_3_buffer[0]
        if byte_3 & 0x40 == 0x00:
            return byte_3 * 0x1000 + byte_2 * 0x40 + byte_1

        raise RuntimeError('Failed to read duration.')

    @staticmethod
    def __read_cont_delta_time(stream: io.BufferedReader):
        total_duration = 0
        while True:
            first_byte_buffer = stream.read(1)
            if len(first_byte_buffer) != 1:
                raise RuntimeError('Invalid first_byte_buffer length..')
            stream.seek(-1, os.SEEK_CUR)
            first_byte = first_byte_buffer[0]
            if first_byte & 0x80 == 0x80 or first_byte == 0x00:
                break

            duration = OkdMTrackMidi.__read_delta_time(stream)
            if duration is None:
                break
            total_duration += duration
        return total_duration

    @staticmethod
    def read(stream: io.BufferedReader):
        messages: list[OkdMidiMessage] = []
        while True:
            first_byte_buffer = stream.read(1)
            if len(first_byte_buffer) != 1:
                return messages
            stream.seek(-1, os.SEEK_CUR)

            end_of_track_buffer = stream.read(4)
            if end_of_track_buffer == b'\x00\x00\x00\x00':
                break
            stream.seek(-4, os.SEEK_CUR)

            if first_byte_buffer[0] & 0x80 != 0x80:
                delta_time = OkdMTrackMidi.__read_cont_delta_time(stream)
                messages.append(OkdMidiDeltaTime(delta_time << 2))

            status_buffer = stream.read(1)
            if len(status_buffer) != 1:
                break
            status_byte = status_buffer[0]

            if status_byte == 0xff:
                event_data_buffer = status_buffer
                while True:
                    byte_buffer = stream.read(1)
                    if len(byte_buffer) != 1:
                        raise RuntimeError('Invalid byte_buffer length.')
                    if byte_buffer[0] & 0x80 == 0x80:
                        stream.seek(-1, os.SEEK_CUR)
                        if byte_buffer[0] != 0xfe:
                            raise RuntimeError(
                                'Unterminated SysEx message detected.')
                        break
                    event_data_buffer += byte_buffer
                messages.append(OkdMidiGenericEvent(event_data_buffer))
                continue

            data_length: int
            if status_byte == 0xf1:
                data_length = 0
            elif status_byte == 0xf2:
                data_length = 0
            elif status_byte == 0xf3:
                data_length = 1
            elif status_byte == 0xf4:
                data_length = 1
            elif status_byte == 0xf5:
                data_length = 0
            elif status_byte == 0xf6:
                data_length = 1
            elif status_byte == 0xf8:
                data_length = 1
            elif status_byte == 0xfe:
                data_length = 0
            else:
                while True:
                    byte_buffer = stream.read(1)
                    if len(byte_buffer) != 1:
                        break
                    if 0xf1 <= byte_buffer[0]:
                        stream.seek(-1, os.SEEK_CUR)
                        break
                    data_buffer += byte_buffer
                messages.append(OkdMidiGenericEvent(status_buffer + data_buffer))
                continue

            data_buffer = stream.read(data_length)
            if len(data_buffer) != data_length:
                raise RuntimeError('Invalid data_buffer length.')

            messages.append(OkdMidiGenericEvent(status_buffer + data_buffer))

        return messages
