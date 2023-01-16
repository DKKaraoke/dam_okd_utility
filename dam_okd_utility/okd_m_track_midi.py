import bitstring

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.okd_midi import (
    read_status_byte,
    is_data_bytes,
    read_extended_variable_int,
    OkdMidiGenericMessage,
    OkdMidiMessage,
)


class OkdMTrackMidi:
    __logger = getLogger("OkdMTrackMidi")

    @staticmethod
    def to_absolute_track(track: list[OkdMidiMessage]):
        absolute_track: list[tuple[int, OkdMidiMessage]] = []
        absolute_time = 0
        for message in track:
            if isinstance(message, OkdMidiGenericMessage):
                absolute_time += message.delta_time

                absolute_track.append(
                    (absolute_time, OkdMidiGenericMessage(0, message.data, 0))
                )

        return absolute_track

    @staticmethod
    def read(stream: bitstring.BitStream):
        track: list[OkdMidiMessage] = []

        while True:
            try:
                end_of_track: bytes = stream.peek("bytes:4")
                if end_of_track == b"\x00\x00\x00\x00":
                    break

                delta_time = read_extended_variable_int(stream)

                status_byte = read_status_byte(stream)

                data_length = 0
                # System messages
                if status_byte == 0xFF:
                    start_position = stream.bytepos
                    unterminated_sysex_detected = False
                    while True:
                        byte = stream.read("uint:8")
                        if byte & 0x80 == 0x80:
                            if byte != 0xFE:
                                OkdMTrackMidi.__logger.warning(
                                    f"Unterminated SysEx message detected. stop_byte={hex(byte)}"
                                )
                                unterminated_sysex_detected = True
                            data_length = stream.bytepos - start_position
                            stream.bytepos = start_position
                            break
                    if unterminated_sysex_detected:
                        continue
                    stream.bytepos = start_position
                elif status_byte == 0xF1:
                    data_length = 0
                elif status_byte == 0xF2:
                    data_length = 0
                elif status_byte == 0xF3:
                    data_length = 1
                elif status_byte == 0xF4:
                    data_length = 1
                elif status_byte == 0xF5:
                    data_length = 0
                elif status_byte == 0xF6:
                    data_length = 1
                elif status_byte == 0xF8:
                    data_length = 0
                else:
                    OkdMTrackMidi.__logger.warning(
                        f"Unknown message detected. status_byte={hex(status_byte)}"
                    )

                status_buffer = status_byte.to_bytes(1, byteorder="big")
                data_buffer = stream.read(8 * data_length).bytes
                message_buffer = status_buffer + data_buffer
                if status_byte != 0xFF and not is_data_bytes(data_buffer):
                    OkdMTrackMidi.__logger.warning(
                        f"Invalid data bytes detected. message_buffer={message_buffer.hex()}"
                    )
                    continue

                track.append(
                    OkdMidiGenericMessage(delta_time, message_buffer, 0)
                )

            except bitstring.ReadError:
                OkdMTrackMidi.__logger.warning(f"Reached to end of stream.")
                # Ignore irregular
                break

            except ValueError as e:
                OkdMTrackMidi.__logger.warning(f'Invalid value detected. error="{e}"')
                # Ignore irregular
                pass

        return track
