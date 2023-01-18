from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.okd_midi import OkdMidiMessage
from dam_okd_utility.okd_p_track_midi import OkdPTrackMidi


class OkdPTrackMidiDeviceStatusMidiParameterChange(NamedTuple):
    bank_select_lsb: int
    bank_select_msb: int
    program_number: int
    volume: int
    pan: int
    bend_pitch_control: int


class OkdPTrackMidiDevice(NamedTuple):
    """DAM OKD P-Track MIDI Device"""

    __logger = getLogger("OkdPTrackMidiDevice")

    MIDI_PARAMETER_CHANGE_ENTRY_INDEX_TABLE = [
        0x01,
        0x02,
        0x03,
        0x04,
        0x05,
        0x06,
        0x07,
        0x08,
        0x09,
        0x00,
        0x0A,
        0x0B,
        0x0C,
        0x0D,
        0x0E,
        0x0F,
        0x11,
        0x12,
        0x13,
        0x14,
        0x15,
        0x16,
        0x17,
        0x18,
        0x19,
        0x10,
        0x1A,
        0x1B,
        0x1C,
        0x1D,
        0x1E,
        0x1F,
    ]

    @staticmethod
    def get_initial_memory():
        memory = [0x00] * 0x200000

        # Set default value
        for entry_index in range(0x40):
            # Volume
            memory[0x801B + (entry_index << 7)] = 0x40
            # Pan
            memory[0x801E + (entry_index << 7)] = 0x40
            # Bend Pitch Control
            memory[0x8041 + (entry_index << 7)] = 0x40

        return memory

    @staticmethod
    def load_from_sysex_messages(track: list[OkdMidiMessage]):
        memory = OkdPTrackMidiDevice.get_initial_memory()

        valid_sysex_exists = False
        for message in track:
            status_byte = message.data[0]
            if status_byte != 0xF0:
                continue
            manufacture_id = message.data[1]
            if manufacture_id != 0x43:
                OkdPTrackMidiDevice.__logger.warning(
                    f"Unknown manufacture ID detected. manufacture_id={manufacture_id}"
                )
                continue
            if message.data[2] & 0x10 != 0x10:
                OkdPTrackMidiDevice.__logger.warning(
                    "Invalid Parameter Change detected."
                )
                continue
            device_number = message.data[2] & 0x0F
            model_id = message.data[3]
            address = message.data[4] << 14 | message.data[5] << 7 | message.data[6]
            data_length = len(message.data) - 9
            data = message.data[7 : 7 + data_length]
            end_mark = message.data[-1]
            if end_mark != 0xF7:
                OkdPTrackMidiDevice.__logger.warning("Invalid SysEx end mark detected.")
                continue

            memory[address : address + data_length] = data

            valid_sysex_exists = True

        return OkdPTrackMidiDevice(memory) if valid_sysex_exists else None

    def get_midi_parameter_change(self, track_part_number: int, channel: int):
        entry_index = (
            OkdPTrackMidi.CHANNEL_COUNT_PER_PORT * track_part_number
            + OkdPTrackMidiDevice.MIDI_PARAMETER_CHANGE_ENTRY_INDEX_TABLE[channel]
        )
        bank_select_msb = self.memory[0x8001 + (entry_index << 7)]
        bank_select_lsb = self.memory[0x8002 + (entry_index << 7)]
        program_number = self.memory[0x8003 + (entry_index << 7)]
        volume = self.memory[0x801B + (entry_index << 7)]
        pan = self.memory[0x801E + (entry_index << 7)]
        bend_pitch_control = self.memory[0x8041 + (entry_index << 7)]
        return OkdPTrackMidiDeviceStatusMidiParameterChange(
            bank_select_msb,
            bank_select_lsb,
            program_number,
            volume,
            pan,
            bend_pitch_control,
        )

    memory: list[int]
