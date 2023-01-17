import bitstring
import mido
from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.dump_memory import dump_memory
from dam_okd_utility.okd_midi import OkdMidiMessage
from dam_okd_utility.okd_p_track_midi_device import OkdPTrackMidiDevice
from dam_okd_utility.okd_p_track_midi import OkdPTrackMidi
from dam_okd_utility.okd_p_track_info_chunk import OkdPTrackInfoEntry
from dam_okd_utility.okd_extended_p_track_info_chunk import OkdExtendedPTrackInfoEntry
from dam_okd_utility.okd_p_track_midi_device import OkdPTrackMidiDevice


class OkdPTrackChunk(NamedTuple):
    """DAM OKD P-Track Chunk"""

    __logger = getLogger("OkdPTrackChunk")

    @staticmethod
    def read(stream: bitstring.BitStream):
        messages = OkdPTrackMidi.read(stream)
        return OkdPTrackChunk(messages)

    @staticmethod
    def to_midi(
        raw_tracks: list[tuple[int, list[OkdMidiMessage]]],
        track_info: list[OkdPTrackInfoEntry] | list[OkdExtendedPTrackInfoEntry],
    ):
        midi_devices: list[OkdPTrackMidiDevice] = []
        current_midi_device: OkdPTrackMidiDevice | None = None
        for track_number, raw_track in raw_tracks:
            midi_device = OkdPTrackMidiDevice.load_from_sysex_messages(raw_track)
            if midi_device is not None:
                current_midi_device = midi_device
            if current_midi_device is None:
                raise ValueError("P-Track MIDI device is not loaded.")

            if midi_device is not None:
                midi_devices.append(midi_device)
            else:
                midi_devices.append(current_midi_device)

        midi = mido.MidiFile()
        raw_track_count = len(raw_tracks)
        for port in range(raw_track_count):
            midi_device_status = midi_devices[port].get_state()
            for channel in range(OkdPTrackMidi.CHANNEL_COUNT_PER_PORT):
                midi_parameter_change = midi_device_status.midi_parameter_changes[
                    channel + 1
                ]

                midi_track = mido.MidiTrack()
                # Port
                midi_track.append(
                    mido.MetaMessage(
                        "midi_port",
                        port=port,
                    )
                )
                # Volume
                midi_track.append(
                    mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x07,
                        value=midi_parameter_change.volume,
                    )
                )
                # Program Change
                midi_track.append(
                    mido.Message(
                        "program_change",
                        channel=channel,
                        program=midi_parameter_change.program_number,
                    )
                )
                # Bend Pitch Control
                midi_track.append(
                    mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x65,
                        value=0x00,
                    )
                )
                midi_track.append(
                    mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x64,
                        value=0x00,
                    )
                )
                midi_track.append(
                    mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x06,
                        value=midi_parameter_change.bend_pitch_control,
                    )
                )

                midi.tracks.append(midi_track)

        # Tempo
        midi.tracks[0].append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(125)))

        absolute_messages = OkdPTrackMidi.to_absolute(raw_tracks, track_info)
        # for message in absolute_messages:
        #     print(
        #         f"time={message.time}, port={message.port}, track={message.track}, data={message.data.hex()}"
        #     )
        track_current_times = [0] * OkdPTrackMidi.TOTAL_CHANNEL_COUNT
        for absolute_message in absolute_messages:
            status_byte = absolute_message.data[0]
            try:
                mido.messages.specs.SPEC_BY_STATUS[status_byte]
            except KeyError:
                OkdPTrackChunk.__logger.warning(
                    f"Unknown message detected. status_byte={hex(status_byte)}"
                )

            delta_time = (
                absolute_message.time - track_current_times[absolute_message.track]
            )
            track_current_times[absolute_message.track] = absolute_message.time

            try:
                midi_message = mido.Message.from_bytes(
                    absolute_message.data, delta_time
                )
            except ValueError:
                OkdPTrackChunk.__logger.warning(
                    f"Invalid message data. status_byte={hex(status_byte)}"
                )
                continue
            midi.tracks[absolute_message.track].append(midi_message)

        # channel_current_times = [0] * OkdPTrackChunk.__TOTAL_CHANNEL_COUNT
        # for track_info_entry, absolute_track in absolute_tracks:
        #     channel_grouping_status = [False] * OkdPTrackChunk.__CHANNEL_COUNT_PER_PORT
        #     for absolute_time, message in absolute_track:
        #         if not isinstance(message, OkdMidiGenericMessage):
        #             continue

        #         status_byte = message.data[0]
        #         status_type = status_byte & 0xF0
        #         channel = status_byte & 0x0F
        #         channel_info_entry = track_info_entry.channel_info[channel]
        #         # delta_time = absolute_time - current_time
        #         # current_time = absolute_time

        #         midi_message: mido.Message
        #         # System messages
        #         if status_byte == 0xF0:
        #             midi_message = mido.Message.from_bytes(message.data)
        #         elif status_byte == 0xF8:
        #             # F8 to CC: 0x14(20) for research
        #             message_data_bytearray = bytearray(3)
        #             message_data_bytearray[0] = 0xB0 | channel
        #             message_data_bytearray[1] = 0x14
        #             message_data_bytearray[2] = message.data[1]
        #             midi_message = mido.Message.from_bytes(
        #                 bytes(message_data_bytearray),
        #             )
        #         elif status_byte == 0xF9:
        #             # F9 to CC: 0x15(21) for research
        #             message_data_bytearray = bytearray(3)
        #             message_data_bytearray[0] = 0xB0 | channel
        #             message_data_bytearray[1] = 0x15
        #             message_data_bytearray[2] = message.data[1]
        #             midi_message = mido.Message.from_bytes(
        #                 bytes(message_data_bytearray),
        #             )
        #         elif status_byte == 0xFA:
        #             # FD to CC: 0x16(22) for research
        #             message_data_bytearray = bytearray(3)
        #             message_data_bytearray[0] = 0xB0 | channel
        #             message_data_bytearray[1] = 0x16
        #             message_data_bytearray[2] = message.data[1]
        #             midi_message = mido.Message.from_bytes(
        #                 bytes(message_data_bytearray),
        #             )
        #         elif status_byte == 0xFD:
        #             # FD to CC: 0x17(23) for research
        #             message_data_bytearray = bytearray(3)
        #             message_data_bytearray[0] = 0xB0 | channel
        #             message_data_bytearray[1] = 0x17
        #             # message_data_bytearray[2] = message.data[1]
        #             midi_message = mido.Message.from_bytes(
        #                 bytes(message_data_bytearray),
        #             )

        #             channel_grouping_status[channel] = True
        #         elif status_byte == 0xFE:
        #             # FE to CC: 0x18(24) for research
        #             message_data_bytearray = bytearray(3)
        #             message_data_bytearray[0] = 0xB0 | channel
        #             message_data_bytearray[1] = 0x18
        #             message_data_bytearray[2] = message.data[1]
        #             midi_message = mido.Message.from_bytes(
        #                 bytes(message_data_bytearray),
        #             )
        #         # Channel voice messages
        #         elif status_type == 0xA0:
        #             # CC: channel_info_entry.control_change_ax
        #             message_data_bytearray = bytearray(3)
        #             message_data_bytearray[0] = 0xB0 | channel
        #             message_data_bytearray[1] = channel_info_entry.control_change_ax
        #             message_data_bytearray[2] = message.data[1]
        #             midi_message = mido.Message.from_bytes(
        #                 bytes(message_data_bytearray),
        #             )
        #         elif status_type == 0xC0:
        #             # CC: channel_info_entry.control_change_cx
        #             message_data_bytearray = bytearray(3)
        #             message_data_bytearray[0] = 0xB0 | channel
        #             message_data_bytearray[1] = channel_info_entry.control_change_cx
        #             message_data_bytearray[2] = message.data[1]
        #             midi_message = mido.Message.from_bytes(
        #                 bytes(message_data_bytearray),
        #             )
        #         else:
        #             try:
        #                 mido.messages.specs.SPEC_BY_STATUS[status_byte]
        #             except KeyError:
        #                 OkdPTrackChunk.__logger.warning(
        #                     f"Unknown message detected. status_byte={hex(status_byte)}"
        #                 )
        #             try:
        #                 midi_message = mido.Message.from_bytes(message.data)
        #             except ValueError:
        #                 OkdPTrackChunk.__logger.warning(
        #                     f"Invalid message data. status_byte={hex(status_byte)}"
        #                 )
        #                 continue

        #         single_channel_group = track_info_entry.single_channel_groups[channel]
        #         if single_channel_group == 0x0000:
        #             single_channel_group = 0x0001 << channel

        #         for port in range(OkdPTrackChunk.__PORT_COUNT):
        #             if (
        #                 track_info_entry.channel_info[channel].ports >> port
        #             ) & 0x0001 != 0x0001:
        #                 continue

        #             for grouped_channel in range(
        #                 OkdPTrackChunk.__CHANNEL_COUNT_PER_PORT
        #             ):
        #                 grouped_midi_track_number = (
        #                     port * OkdPTrackChunk.__CHANNEL_COUNT_PER_PORT
        #                 ) + grouped_channel

        #                 if (
        #                     (
        #                         channel_grouping_status[channel]
        #                         and track_info_entry.channel_groups[channel]
        #                         >> grouped_channel
        #                         & 0x0001
        #                         != 0x0001
        #                     )
        #                     or single_channel_group >> grouped_channel & 0x0001
        #                     != 0x0001
        #                 ):
        #                     cloned_midi_message = midi_message.copy()
        #                     if hasattr(cloned_midi_message, "channel"):
        #                         cloned_midi_message.channel = grouped_channel
        #                     midi_message.time = (
        #                         absolute_time
        #                         - channel_current_times[grouped_midi_track_number]
        #                     )
        #                     midi.tracks[grouped_midi_track_number].append(
        #                         cloned_midi_message
        #                     )

        #                 channel_current_times[grouped_midi_track_number] = absolute_time

        #             if channel_grouping_status[channel]:
        #                 channel_grouping_status[channel] = False
        # else:
        # midi_track_number = (
        #     port * OkdPTrackChunk.__CHANNEL_COUNT_PER_PORT
        # ) + channel
        # midi_message.time = (
        #     absolute_time - channel_current_times[midi_track_number]
        # )
        # midi.tracks[midi_track_number].append(midi_message)
        # channel_current_times[midi_track_number] = absolute_time

        return midi

    def to_json_serializable(self):
        json_track = []
        for message in self.messages:
            json_track.append(
                {
                    "delta_time": message.delta_time,
                    "data_hex": message.data.hex(),
                    "duration": message.duration,
                }
            )
        return {"track": json_track}

    # def to_midi(
    #     self,
    #     device: OkdPTrackMidiDevice,
    #     track_info_entry: OkdPTrackInfoEntry | OkdExtendedPTrackInfoEntry,
    #     part_number=0,
    #     total_part_number=0,
    # ):
    #     absolute_track = OkdPTrackMidi.to_absolute_track(self.track, track_info_entry)

    #     raw_track: list[tuple[int, mido.Message]] = []
    #     channel_grouping_status = [False] * 16
    #     for absolute_time, message in absolute_track:
    #         if not isinstance(message, OkdMidiGenericMessage):
    #             continue

    #         status_byte = message.data[0]
    #         status_type = status_byte & 0xF0
    #         source_channel = status_byte & 0x0F
    #         channel_info_entry = track_info_entry.channel_info[source_channel]

    #         if status_type == 0xF0:
    #             if status_byte == 0xF0:
    #                 midi_message = mido.Message.from_bytes(message.data)
    #                 raw_track.append((absolute_time, midi_message))
    #                 continue

    #             if status_byte == 0xF8:
    #                 # F8 to CC: 0x14(20) for research
    #                 message_data_bytearray = bytearray(3)
    #                 message_data_bytearray[0] = 0xB0
    #                 message_data_bytearray[1] = 0x14
    #                 message_data_bytearray[2] = message.data[1]
    #                 midi_message = mido.Message.from_bytes(
    #                     bytes(message_data_bytearray)
    #                 )
    #                 raw_track.append((absolute_time, midi_message))
    #                 continue

    #             if status_byte == 0xF9:
    #                 # F9 to CC: 0x15(21) for research
    #                 message_data_bytearray = bytearray(3)
    #                 message_data_bytearray[0] = 0xB0
    #                 message_data_bytearray[1] = 0x15
    #                 message_data_bytearray[2] = message.data[1]
    #                 midi_message = mido.Message.from_bytes(
    #                     bytes(message_data_bytearray)
    #                 )
    #                 raw_track.append((absolute_time, midi_message))
    #                 continue

    #             if status_byte == 0xFA:
    #                 # FD to CC: 0x16(22) for research
    #                 message_data_bytearray = bytearray(3)
    #                 message_data_bytearray[0] = 0xB0
    #                 message_data_bytearray[1] = 0x16
    #                 message_data_bytearray[2] = message.data[1]
    #                 midi_message = mido.Message.from_bytes(
    #                     bytes(message_data_bytearray)
    #                 )
    #                 raw_track.append((absolute_time, midi_message))
    #                 continue

    #             if status_byte == 0xFD:
    #                 # FD to CC: 0x17(23) for research
    #                 message_data_bytearray = bytearray(3)
    #                 message_data_bytearray[0] = 0xB0
    #                 message_data_bytearray[1] = 0x17
    #                 # message_data_bytearray[2] = message.data[1]
    #                 midi_message = mido.Message.from_bytes(
    #                     bytes(message_data_bytearray)
    #                 )
    #                 raw_track.append((absolute_time, midi_message))

    #                 channel_grouping_status[source_channel] = True
    #                 continue

    #             if status_byte == 0xFE:
    #                 # FE to CC: 0x18(24) for research
    #                 message_data_bytearray = bytearray(3)
    #                 message_data_bytearray[0] = 0xB0
    #                 message_data_bytearray[1] = 0x18
    #                 message_data_bytearray[2] = message.data[1]
    #                 midi_message = mido.Message.from_bytes(
    #                     bytes(message_data_bytearray)
    #                 )
    #                 raw_track.append((absolute_time, midi_message))
    #                 continue

    #             OkdPTrackChunk.__logger.warning(
    #                 f"Unknown message detected. status_byte={hex(status_byte)}"
    #             )

    #         grouped_channels = []
    #         if channel_grouping_status[source_channel]:
    #             for grouped_channel in range(16):
    #                 if not (
    #                     track_info_entry.channel_groups[source_channel]
    #                     >> grouped_channel
    #                     & 0x0001
    #                     == 0x0001
    #                 ):
    #                     continue
    #                 grouped_channels.append(grouped_channel)

    #             channel_grouping_status[source_channel] = False
    #         else:
    #             grouped_channels.append(source_channel)

    #         for channel in grouped_channels:
    #             if status_type == 0xA0:
    #                 # CC: channel_info_entry.control_change_ax
    #                 message_data_bytearray = bytearray(3)
    #                 message_data_bytearray[0] = 0xB0 | channel
    #                 message_data_bytearray[1] = channel_info_entry.control_change_ax
    #                 message_data_bytearray[2] = message.data[1]
    #                 midi_message = mido.Message.from_bytes(
    #                     bytes(message_data_bytearray)
    #                 )
    #                 midi_message.channel = channel
    #                 raw_track.append((absolute_time, midi_message))
    #                 continue

    #             if status_type == 0xC0:
    #                 # CC: channel_info_entry.control_change_cx
    #                 message_data_bytearray = bytearray(3)
    #                 message_data_bytearray[0] = 0xB0 | channel
    #                 message_data_bytearray[1] = channel_info_entry.control_change_cx
    #                 message_data_bytearray[2] = message.data[1]
    #                 midi_message = mido.Message.from_bytes(
    #                     bytes(message_data_bytearray)
    #                 )
    #                 midi_message.channel = channel
    #                 raw_track.append((absolute_time, midi_message))
    #                 continue

    #             try:
    #                 mido.messages.specs.SPEC_BY_STATUS[status_byte]
    #             except KeyError:
    #                 OkdPTrackChunk.__logger.warning(
    #                     f"Unknown message detected. status_byte={hex(status_byte)}"
    #                 )
    #                 continue

    #             midi_message: mido.Message
    #             try:
    #                 midi_message = mido.Message.from_bytes(message.data)
    #             except ValueError:
    #                 OkdPTrackChunk.__logger.warning(
    #                     f"Invalid message data. status_byte={hex(status_byte)}"
    #                 )
    #                 continue
    #             midi_message.channel = channel
    #             raw_track.append((absolute_time, midi_message))

    #     raw_track.sort(key=lambda message: message[0])

    #     midi = mido.MidiFile()

    #     setup_track = mido.MidiTrack()
    #     setup_track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(125)))
    #     current_time = 0
    #     for absolute_time, message in raw_track:
    #         if hasattr(message, "channel"):
    #             continue

    #         message.time = absolute_time - current_time
    #         setup_track.append(message)
    #         current_time = absolute_time

    #     midi.tracks.append(setup_track)

    #     device_state = device.get_state()

    #     for channel in range(16):
    #         track = mido.MidiTrack()

    #         track.append(
    #             mido.MetaMessage(
    #                 "midi_port",
    #                 port=total_part_number,
    #             )
    #         )

    #         midi_parameter_change_index = 16 * part_number + channel + 1
    #         midi_parameter_change = device_state.midi_parameter_changes[
    #             midi_parameter_change_index
    #         ]
    #         # Volume
    #         track.append(
    #             mido.Message(
    #                 "control_change",
    #                 channel=channel,
    #                 control=0x07,
    #                 value=midi_parameter_change.volume,
    #             )
    #         )
    #         # Program Change
    #         track.append(
    #             mido.Message(
    #                 "program_change",
    #                 channel=channel,
    #                 program=midi_parameter_change.program_number,
    #             )
    #         )
    #         # Bend Pitch Control
    #         track.append(
    #             mido.Message(
    #                 "control_change",
    #                 channel=channel,
    #                 control=0x65,
    #                 value=0x00,
    #             )
    #         )
    #         track.append(
    #             mido.Message(
    #                 "control_change",
    #                 channel=channel,
    #                 control=0x64,
    #                 value=0x00,
    #             )
    #         )
    #         track.append(
    #             mido.Message(
    #                 "control_change",
    #                 channel=channel,
    #                 control=0x06,
    #                 value=midi_parameter_change.bend_pitch_control,
    #             )
    #         )

    #         current_time = 0
    #         for absolute_time, message in raw_track:
    #             if not hasattr(message, "channel"):
    #                 continue
    #             if message.channel != channel:
    #                 continue
    #             message.time = absolute_time - current_time
    #             track.append(message)
    #             current_time = absolute_time

    #         midi.tracks.append(track)

    #     return midi

    messages: list[OkdMidiMessage]
