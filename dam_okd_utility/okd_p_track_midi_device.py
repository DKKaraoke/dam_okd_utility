from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.okd_midi import OkdMidiMessage


class OkdPTrackMidiDeviceStatusMidiParameterChange(NamedTuple):
    bank_select_lsb: int
    bank_select_msb: int
    program_number: int
    volume: int
    pan: int


class OkdPTrackMidiDeviceState(NamedTuple):
    midi_parameter_changes: list[OkdPTrackMidiDeviceStatusMidiParameterChange]


class OkdPTrackMidiDevice(NamedTuple):
    """DAM OKD P-Track MIDI Device"""

    __logger = getLogger("OkdPTrackMidiDevice")

    @staticmethod
    def get_initial_memory():
        memory = [0x00] * 0x200000

        # Set default value
        for channel in range(0x40):
            # Volume
            memory[0x801b + (channel << 7)] = 0x40
            # Pan
            memory[0x801e + (channel << 7)] = 0x40

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

    def get_state(self):
        midi_parameter_changes = []
        for channel in range(0x40):
            bank_select_msb = self.memory[0x8001 + (channel << 7)]
            bank_select_lsb = self.memory[0x8002 + (channel << 7)]
            program_number = self.memory[0x8003 + (channel << 7)]
            volume = self.memory[0x801b + (channel << 7)]
            pan = self.memory[0x801e + (channel << 7)]

            midi_parameter_changes.append(
                OkdPTrackMidiDeviceStatusMidiParameterChange(
                    bank_select_msb,
                    bank_select_lsb,
                    program_number,
                    volume,
                    pan,
                )
            )

        return OkdPTrackMidiDeviceState(midi_parameter_changes)

    memory: list[int]
