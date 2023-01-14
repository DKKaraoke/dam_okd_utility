import bitstring

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.okd_midi import read_status_byte, read_variable_int, read_extended_variable_int, OkdMidiGenericMessage, OkdMidiMessage


class OkdPTrackMidi:
    __logger = getLogger('OkdPTrackMidi')

    @staticmethod
    def to_absolute_track(track: list[OkdMidiMessage]):
        absolute_track: list[tuple[int, OkdMidiMessage]] = []
        absolute_time = 0
        for message in track:
            if isinstance(message, OkdMidiGenericMessage):
                absolute_time += message.delta_time

                status_byte = message.data[0]
                status_type = status_byte & 0xf0

                if status_type == 0x80:
                    channel = status_byte & 0x0f
                    note_number = message.data[1]
                    note_on_velocity = message.data[2]
                    note_off_velocity = message.data[3]

                    note_on_bytearray = bytearray(3)
                    note_on_bytearray[0] = 0x90 | channel
                    note_on_bytearray[1] = note_number
                    note_on_bytearray[2] = note_on_velocity
                    absolute_track.append(
                        (absolute_time, OkdMidiGenericMessage(0, bytes(note_on_bytearray), 0)))

                    note_off_bytearray = bytearray(3)
                    note_off_bytearray[0] = 0x80 | channel
                    note_off_bytearray[1] = note_number
                    note_off_bytearray[2] = note_off_velocity
                    absolute_track.append(
                        (absolute_time + message.duration, OkdMidiGenericMessage(0, bytes(note_off_bytearray), 0)))
                    continue

                if status_type == 0x90:
                    channel = status_byte & 0x0f
                    note_number = message.data[1]
                    note_on_velocity = message.data[2]

                    absolute_track.append(
                        (absolute_time, OkdMidiGenericMessage(0, bytes(message.data), 0)))

                    note_off_bytearray = bytearray(3)
                    note_off_bytearray[0] = 0x80 | channel
                    note_off_bytearray[1] = note_number
                    note_off_bytearray[2] = 0x40
                    absolute_track.append(
                        (absolute_time + message.duration, OkdMidiGenericMessage(0, bytes(note_off_bytearray), 0)))
                    continue

                absolute_track.append(
                    (absolute_time, OkdMidiGenericMessage(0, message.data, 0)))

        return absolute_track

    @ staticmethod
    def read(stream: bitstring.BitStream):
        track: list[OkdMidiMessage] = []

        try:
            while True:
                delta_time: int
                try:
                    delta_time = read_extended_variable_int(stream)
                except bitstring.ReadError:
                    break

                status_byte = read_status_byte(stream)
                status_type = status_byte & 0xf0

                data_length = 0
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
                elif status_byte == 0xf0 or status_byte == 0xf9:
                    start_position = stream.bytepos
                    unterminated_sysex_detected = False
                    while True:
                        byte = stream.read('uint:8')
                        if byte & 0x80 == 0x80:
                            if byte != 0xf7:
                                OkdPTrackMidi.__logger.warning(
                                    f'Unterminated SysEx message detected. stop_byte={hex(byte)}')
                                unterminated_sysex_detected = True
                            data_length = stream.bytepos - start_position
                            stream.bytepos = start_position
                            break
                    if unterminated_sysex_detected:
                        continue
                    stream.bytepos = start_position
                elif status_byte == 0xf8:
                    data_length = 3
                elif status_byte == 0xf9:
                    data_length = 1
                elif status_byte == 0xfa:
                    data_length = 1
                elif status_byte == 0xfd:
                    data_length = 0
                elif status_byte == 0xfe:
                    byte = stream.peek('uint:8')
                    if byte & 0xf0 == 0xa0:
                        data_length = 4
                    elif byte & 0xf0 == 0xc0:
                        data_length = 3
                    else:
                        data_length = 1
                else:
                    OkdPTrackMidi.__logger.warning(
                        f'Unknown message detected. status_byte={hex(status_byte)}')

                status_buffer = status_byte.to_bytes(1, byteorder='big')
                data_buffer = stream.read(8 * data_length).bytes

                duration = 0
                if status_type == 0x80 or status_type == 0x90:
                    duration = read_variable_int(stream) << 2

                track.append(OkdMidiGenericMessage(
                    delta_time, status_buffer + data_buffer, duration))
        except bitstring.ReadError:
            OkdPTrackMidi.__logger.warning(f'Reached to end of stream.')
            # Ignore irregular
            pass

        return track
