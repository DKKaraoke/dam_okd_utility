import io
import os

from dam_okd_utility.okd_midi import OkdMidiDeltaTime, OkdMidiGenericEvent, OkdMidiMessage


class OkdPTrackMidi:
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

            duration = OkdPTrackMidi.__read_delta_time(stream)
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
                delta_time = OkdPTrackMidi.__read_cont_delta_time(stream)
                messages.append(OkdMidiDeltaTime(delta_time))

            status_buffer = stream.read(1)
            if len(status_buffer) != 1:
                break
            status_byte = status_buffer[0]
            status_type = status_byte & 0xf0

            if status_byte == 0xf0 or status_byte == 0xf9:
                event_data_buffer = status_buffer
                while True:
                    byte_buffer = stream.read(1)
                    if len(byte_buffer) != 1:
                        raise RuntimeError('Invalid byte_buffer length.')
                    if byte_buffer[0] & 0x80 == 0x80:
                        stream.seek(-1, os.SEEK_CUR)
                        # if byte_buffer[0] != 0xf7:
                        #     raise RuntimeError(
                        #         'Unterminated SysEx message detected.')
                        break
                    event_data_buffer += byte_buffer
                messages.append(OkdMidiGenericEvent(event_data_buffer))
                continue

            data_length: int
            if status_type == 0x80:
                data_length = 3
            elif status_type == 0x90:
                data_length = 2
            elif status_type == 0xa0:
                data_length = 1
            elif status_type == 0xb0:
                data_length = 2
            elif status_type == 0xc0:
                data_length = 1
            elif status_type == 0xd0:
                data_length = 1
            elif status_type == 0xe0:
                data_length = 2
            elif status_byte == 0xf7:
                data_length = 0
            elif status_byte == 0xf8:
                data_length = 3
            elif status_byte == 0xfa:
                data_length = 1
            elif status_byte == 0xfd:
                data_length = 0
            elif status_byte == 0xfe:
                byte_1_buffer = stream.read(1)
                if len(byte_1_buffer) != 1:
                    raise RuntimeError('Invalid byte_1_buffer length.')
                stream.seek(-1, os.SEEK_CUR)
                byte_1 = byte_1_buffer[0]
                if byte_1 & 0xf0 == 0xa0:
                    data_length = 4
                elif byte_1 & 0xf0 == 0xc0:
                    data_length = 3
                else:
                    data_length = 1
            else:
                stream.seek(-16, os.SEEK_CUR)
                raise RuntimeError(
                    f'Unknown message detected. status_byte={hex(status_byte)}')

            data_buffer = stream.read(data_length)
            if len(data_buffer) != data_length:
                raise RuntimeError('Invalid data_buffer length.')

            messages.append(OkdMidiGenericEvent(status_buffer + data_buffer))

        return messages
