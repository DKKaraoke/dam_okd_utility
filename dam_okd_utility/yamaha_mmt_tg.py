import mido

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.okd_p_track_midi_data import OkdPTrackAbsoluteTimeMessage
from dam_okd_utility.yamaha_mmt_tg_data import (
    YamahaMmtTgMidiParameterChangeTableSystem,
    YamahaMmtTgMidiParameterChangeTableMultiPartEntry,
)


class YamahaMmtTg:
    """YAMAHA MMT TG MIDI Device"""

    __logger = getLogger("YamahaMmtTg")

    CHANNEL_COUNT_PER_PORT = 16
    MIDI_PARAMETER_CHANGE_PART_NUMBER_TO_ENTRY_INDEX_TABLE = [
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

    MIDI_PARAMETER_CHANGE_ENTRY_INDEX_TO_PART_NUMBER_TABLE = [
        0x09,
        0x00,
        0x01,
        0x02,
        0x03,
        0x04,
        0x05,
        0x06,
        0x07,
        0x08,
        0x0A,
        0x0B,
        0x0C,
        0x0D,
        0x0E,
        0x0F,
        0x19,
        0x10,
        0x11,
        0x12,
        0x13,
        0x14,
        0x15,
        0x16,
        0x17,
        0x18,
        0x1A,
        0x1B,
        0x1C,
        0x1D,
        0x1E,
        0x1F,
    ]

    def __init__(self):
        self.initialize_state()

    def initialize_state(self):
        self.sound_module_mode = 0x00
        self.native_parameter_memory = [0x00] * 0x200000

        # Set default value
        for entry_index in range(0x20):
            entry_address = 0x008000 + (entry_index << 7)

            self.native_parameter_memory[entry_address + 0x01] = 0x00
            self.native_parameter_memory[entry_address + 0x02] = 0x00
            self.native_parameter_memory[entry_address + 0x03] = 0x00
            self.native_parameter_memory[entry_address + 0x04] = entry_index
            self.native_parameter_memory[entry_address + 0x05] = 0x01
            self.native_parameter_memory[entry_address + 0x06] = 0x01
            self.native_parameter_memory[entry_address + 0x07] = 0x01
            self.native_parameter_memory[entry_address + 0x08] = 0x01
            self.native_parameter_memory[entry_address + 0x09] = 0x01
            self.native_parameter_memory[entry_address + 0x0A] = 0x01
            self.native_parameter_memory[entry_address + 0x0B] = 0x01
            self.native_parameter_memory[entry_address + 0x0C] = 0x01
            self.native_parameter_memory[entry_address + 0x0D] = 0x01
            self.native_parameter_memory[entry_address + 0x0E] = 0x01
            self.native_parameter_memory[entry_address + 0x0F] = 0x01
            self.native_parameter_memory[entry_address + 0x10] = 0x01
            self.native_parameter_memory[entry_address + 0x11] = 0x01
            self.native_parameter_memory[entry_address + 0x12] = 0x01
            self.native_parameter_memory[entry_address + 0x13] = 0x01
            self.native_parameter_memory[entry_address + 0x14] = 0x01

            self.native_parameter_memory[entry_address + 0x15] = 0x01
            self.native_parameter_memory[entry_address + 0x16] = 0x01
            self.native_parameter_memory[entry_address + 0x17] = 0x01
            self.native_parameter_memory[entry_address + 0x18] = 0x01
            self.native_parameter_memory[entry_address + 0x19] = 0x08
            self.native_parameter_memory[entry_address + 0x1A] = 0x00
            self.native_parameter_memory[entry_address + 0x1B] = 0x64
            self.native_parameter_memory[entry_address + 0x1C] = 0x40
            self.native_parameter_memory[entry_address + 0x1D] = 0x40
            self.native_parameter_memory[entry_address + 0x1E] = 0x40
            self.native_parameter_memory[entry_address + 0x1F] = 0x00
            self.native_parameter_memory[entry_address + 0x20] = 0x7F
            self.native_parameter_memory[entry_address + 0x21] = 0x10
            self.native_parameter_memory[entry_address + 0x22] = 0x11
            self.native_parameter_memory[entry_address + 0x23] = 0x7F
            self.native_parameter_memory[entry_address + 0x24] = 0x00
            self.native_parameter_memory[entry_address + 0x25] = 0x40
            self.native_parameter_memory[entry_address + 0x26] = 0x00

            self.native_parameter_memory[entry_address + 0x27] = 0x40
            self.native_parameter_memory[entry_address + 0x28] = 0x40
            self.native_parameter_memory[entry_address + 0x29] = 0x40
            self.native_parameter_memory[entry_address + 0x2A] = 0x40
            self.native_parameter_memory[entry_address + 0x2B] = 0x40
            self.native_parameter_memory[entry_address + 0x2C] = 0x40
            self.native_parameter_memory[entry_address + 0x2D] = 0x40
            self.native_parameter_memory[entry_address + 0x2E] = 0x40

            self.native_parameter_memory[entry_address + 0x2F] = 0x40
            self.native_parameter_memory[entry_address + 0x30] = 0x40
            self.native_parameter_memory[entry_address + 0x31] = 0x40
            self.native_parameter_memory[entry_address + 0x32] = 0x40
            self.native_parameter_memory[entry_address + 0x33] = 0x40
            self.native_parameter_memory[entry_address + 0x34] = 0x40
            self.native_parameter_memory[entry_address + 0x35] = 0x40
            self.native_parameter_memory[entry_address + 0x36] = 0x40
            self.native_parameter_memory[entry_address + 0x37] = 0x40
            self.native_parameter_memory[entry_address + 0x38] = 0x40
            self.native_parameter_memory[entry_address + 0x39] = 0x40
            self.native_parameter_memory[entry_address + 0x3A] = 0x40

            self.native_parameter_memory[entry_address + 0x3B] = 0x40
            self.native_parameter_memory[entry_address + 0x3C] = 0x40
            self.native_parameter_memory[entry_address + 0x3D] = 0x40
            self.native_parameter_memory[entry_address + 0x3E] = 0x0A
            self.native_parameter_memory[entry_address + 0x3F] = 0x00

            self.native_parameter_memory[entry_address + 0x41] = 0x42
            self.native_parameter_memory[entry_address + 0x42] = 0x40
            self.native_parameter_memory[entry_address + 0x43] = 0x40
            self.native_parameter_memory[entry_address + 0x44] = 0x00
            self.native_parameter_memory[entry_address + 0x45] = 0x00

            self.native_parameter_memory[entry_address + 0x47] = 0x40
            self.native_parameter_memory[entry_address + 0x48] = 0x40
            self.native_parameter_memory[entry_address + 0x49] = 0x40
            self.native_parameter_memory[entry_address + 0x4A] = 0x00
            self.native_parameter_memory[entry_address + 0x4B] = 0x00

            self.native_parameter_memory[entry_address + 0x4D] = 0x40
            self.native_parameter_memory[entry_address + 0x4E] = 0x40
            self.native_parameter_memory[entry_address + 0x4F] = 0x40
            self.native_parameter_memory[entry_address + 0x50] = 0x00
            self.native_parameter_memory[entry_address + 0x51] = 0x00

            self.native_parameter_memory[entry_address + 0x53] = 0x40
            self.native_parameter_memory[entry_address + 0x54] = 0x40
            self.native_parameter_memory[entry_address + 0x55] = 0x40
            self.native_parameter_memory[entry_address + 0x56] = 0x00
            self.native_parameter_memory[entry_address + 0x57] = 0x00

            self.native_parameter_memory[entry_address + 0x59] = 0x40
            self.native_parameter_memory[entry_address + 0x5A] = 0x40
            self.native_parameter_memory[entry_address + 0x5B] = 0x40
            self.native_parameter_memory[entry_address + 0x5C] = 0x00
            self.native_parameter_memory[entry_address + 0x5D] = 0x00

            self.native_parameter_memory[entry_address + 0x5F] = 0x00
            self.native_parameter_memory[entry_address + 0x60] = 0x00

    @staticmethod
    def __is_sysex_message(message: OkdPTrackAbsoluteTimeMessage):
        if len(message.data) < 3:
            return False
        status_byte = message.data[0]
        if status_byte != 0xF0:
            return False
        end_mark = message.data[-1]
        if end_mark != 0xF7:
            return False
        return True

    @staticmethod
    def __is_universal_realtime_message(message: OkdPTrackAbsoluteTimeMessage):
        if not YamahaMmtTg.__is_sysex_message(message):
            return False
        if len(message.data) < 8:
            return False
        manufacture_id = message.data[1]
        if manufacture_id != 0x7F:
            return False
        return True

    @staticmethod
    def __is_universal_non_realtime_message(message: OkdPTrackAbsoluteTimeMessage):
        if not YamahaMmtTg.__is_sysex_message(message):
            return False
        if len(message.data) < 6:
            return False
        manufacture_id = message.data[1]
        if manufacture_id != 0x7E:
            return False
        return True

    @staticmethod
    def __is_native_parameter_change_message(message: OkdPTrackAbsoluteTimeMessage):
        if not YamahaMmtTg.__is_sysex_message(message):
            return False
        if len(message.data) < 10:
            return False
        manufacture_id = message.data[1]
        if manufacture_id != 0x43:
            return False
        device_number_byte = message.data[2]
        if device_number_byte & 0xF0 != 0x10:
            return False
        return True

    def __receive_universal_realtime_message(
        self, message: OkdPTrackAbsoluteTimeMessage
    ):
        status_byte = message.data[0]
        if status_byte != 0xF0:
            raise ValueError(f"Invalid status_byte. status_byte={hex(status_byte)}")
        manufacture_id = message.data[1]
        if manufacture_id != 0x7F:
            raise ValueError(
                f"Invalid manufacture_id. manufacture_id={hex(manufacture_id)}"
            )
        target_device_id = message.data[2]
        sub_id_1 = message.data[3]
        if sub_id_1 != 0x04:
            YamahaMmtTg.__logger.warning(
                f"Unknown sub_id_1 detected. sub_id_1={hex(sub_id_1)}"
            )

        sub_id_2 = message.data[3]
        if sub_id_2 == 0x01:
            # Master Volume
            volume_lsb = message.data[4]
            volume_msb = message.data[5]
            # MASTER VOLUME
            self.native_parameter_memory[0x000004] = volume_msb
        elif sub_id_2 == 0x02:
            # Master Balance
            balance_lsb = message.data[4]
            balance_msb = message.data[5]
            # MASTER PAN
            self.native_parameter_memory[0x000006] = balance_msb
        else:
            YamahaMmtTg.__logger.warning(
                f"Unknown sub_id_2 detected. sub_id_2={hex(sub_id_2)}"
            )

    def __receive_universal_non_realtime_message(
        self, message: OkdPTrackAbsoluteTimeMessage
    ):
        status_byte = message.data[0]
        if status_byte != 0xF0:
            raise ValueError(f"Invalid status_byte. status_byte={hex(status_byte)}")
        manufacture_id = message.data[1]
        if manufacture_id != 0x7E:
            raise ValueError(
                f"Invalid manufacture_id. manufacture_id={hex(manufacture_id)}"
            )
        target_device_id = message.data[2]
        sub_id_1 = message.data[3]
        if sub_id_1 != 0x09:
            YamahaMmtTg.__logger.warning(
                f"Unknown sub_id_1 detected. sub_id_1={hex(sub_id_1)}"
            )

        sub_id_2 = message.data[3]
        if sub_id_2 == 0x01:
            self.sound_module_mode = message.data[4]
        else:
            YamahaMmtTg.__logger.warning(
                f"Unknown sub_id_2 detected. sub_id_2={hex(sub_id_2)}"
            )

    def __receive_native_parameter_change_message(
        self, message: OkdPTrackAbsoluteTimeMessage
    ):
        status_byte = message.data[0]
        if status_byte != 0xF0:
            raise ValueError(f"Invalid status_byte. status_byte={hex(status_byte)}")
        manufacture_id = message.data[1]
        if manufacture_id != 0x43:
            raise ValueError(
                f"Invalid manufacture_id. manufacture_id={hex(manufacture_id)}"
            )
        device_number_byte = message.data[2]
        if device_number_byte & 0xF0 != 0x10:
            raise ValueError(
                f"Invalid device_number_byte detected. device_number_byte={hex(device_number_byte)}"
            )
        device_number = device_number_byte & 0x0F
        model_id = message.data[3]

        address = message.data[4] << 14 | message.data[5] << 7 | message.data[6]
        data_length = len(message.data) - 9
        data = message.data[7 : 7 + data_length]
        check_sum = message.data[-2]

        if address == 0x00007F:
            # All Parameters Reset
            self.initialize_state()
            return
        self.native_parameter_memory[address : address + data_length] = data

    def receive_sysex_message(self, message: OkdPTrackAbsoluteTimeMessage):
        if len(message.data) < 1:
            raise ValueError("Invalid message.data legnth.")

        status_byte = message.data[0]
        if status_byte != 0xF0:
            raise ValueError(f"Invalid status_byte. status_byte={hex(status_byte)}")
        end_mark = message.data[-1]
        if end_mark != 0xF7:
            raise ValueError(f"Invalid end_mark. end_mark={hex(end_mark)}")

        manufacture_id = message.data[1]
        if manufacture_id == 0x7F:
            self.__receive_universal_realtime_message(message)
        elif manufacture_id == 0x7E:
            self.__receive_universal_non_realtime_message(message)
        elif manufacture_id == 0x43:
            device_number_byte = message.data[2]
            if device_number_byte & 0xF0 != 0x10:
                YamahaMmtTg.__logger.warning(
                    f"Unknown native SysEx message detected. device_number_byte={hex(device_number_byte)}"
                )
                return
            self.__receive_native_parameter_change_message(message)
        else:
            YamahaMmtTg.__logger.warning(
                f"Unknown manufacture_id detected. manufacture_id={hex(manufacture_id)}"
            )

    def get_midi_parameter_change_table_system(self):
        master_tune = (
            ((self.native_parameter_memory[0x000000] & 0x0F) << 12)
            | ((self.native_parameter_memory[0x000001] & 0x0F) << 8)
            | ((self.native_parameter_memory[0x000002] & 0x0F) << 4)
            | (self.native_parameter_memory[0x000003] & 0x0F)
        )
        master_volume = self.native_parameter_memory[0x000004]
        transpose = self.native_parameter_memory[0x000005]
        master_pan = self.native_parameter_memory[0x000006]
        master_cutoff = self.native_parameter_memory[0x000007]
        master_pitch_modulation_depth = self.native_parameter_memory[0x000008]
        variation_effect_send_control_change_number = self.native_parameter_memory[
            0x000009
        ]

        return YamahaMmtTgMidiParameterChangeTableSystem(
            master_tune,
            master_volume,
            transpose,
            master_pan,
            master_cutoff,
            master_pitch_modulation_depth,
            variation_effect_send_control_change_number,
        )

    def get_midi_parameter_change_table_multi_part_entry(self, part_number: int):
        entry_index = (
            YamahaMmtTg.MIDI_PARAMETER_CHANGE_PART_NUMBER_TO_ENTRY_INDEX_TABLE[
                part_number
            ]
        )
        entry_address = 0x008000 + (entry_index << 7)

        bank_select_msb = self.native_parameter_memory[entry_address + 0x01]
        bank_select_lsb = self.native_parameter_memory[entry_address + 0x02]
        program_number = self.native_parameter_memory[entry_address + 0x03]
        rcv_channel = self.native_parameter_memory[entry_address + 0x04]
        rcv_pitch_bend = self.native_parameter_memory[entry_address + 0x05]
        rcv_ch_after_touch = self.native_parameter_memory[entry_address + 0x06]
        rcv_program_change = self.native_parameter_memory[entry_address + 0x07]
        rcv_control_change = self.native_parameter_memory[entry_address + 0x08]
        rcv_poly_after_touch = self.native_parameter_memory[entry_address + 0x09]
        rcv_note_message = self.native_parameter_memory[entry_address + 0x0A]
        rcv_rpn = self.native_parameter_memory[entry_address + 0x0B]
        rcv_nrpn = self.native_parameter_memory[entry_address + 0x0C]
        rcv_modulation = self.native_parameter_memory[entry_address + 0x0D]
        rcv_volume = self.native_parameter_memory[entry_address + 0x0E]
        rcv_pan = self.native_parameter_memory[entry_address + 0x0F]
        rcv_expression = self.native_parameter_memory[entry_address + 0x10]
        rcv_hold_1 = self.native_parameter_memory[entry_address + 0x11]
        rcv_portamento = self.native_parameter_memory[entry_address + 0x12]
        rcv_sostenuto = self.native_parameter_memory[entry_address + 0x13]
        rcv_soft_pedal = self.native_parameter_memory[entry_address + 0x14]

        mono_poly_mode = self.native_parameter_memory[entry_address + 0x15]
        same_note_number_key_on_assign = self.native_parameter_memory[
            entry_address + 0x16
        ]
        part_mode = self.native_parameter_memory[entry_address + 0x17]
        note_shift = self.native_parameter_memory[entry_address + 0x18]
        detune = ((self.native_parameter_memory[entry_address + 0x19] & 0x0F) << 4) | (
            self.native_parameter_memory[entry_address + 0x1A] & 0x0F
        )
        volume = self.native_parameter_memory[entry_address + 0x1B]
        velocity_sense_depth = self.native_parameter_memory[entry_address + 0x1C]
        velocity_sense_offset = self.native_parameter_memory[entry_address + 0x1D]
        pan = self.native_parameter_memory[entry_address + 0x1E]
        note_limit_low = self.native_parameter_memory[entry_address + 0x1F]
        note_limit_high = self.native_parameter_memory[entry_address + 0x20]
        ac_1_controller_number = self.native_parameter_memory[entry_address + 0x21]
        ac_2_controller_number = self.native_parameter_memory[entry_address + 0x22]
        dry_level = self.native_parameter_memory[entry_address + 0x23]
        chorus_send = self.native_parameter_memory[entry_address + 0x24]
        reverb_send = self.native_parameter_memory[entry_address + 0x25]
        variation_send = self.native_parameter_memory[entry_address + 0x26]

        vibrato_rate = self.native_parameter_memory[entry_address + 0x27]
        vibrato_depth = self.native_parameter_memory[entry_address + 0x28]
        filter_cutoff_frequency = self.native_parameter_memory[entry_address + 0x29]
        filter_resonance = self.native_parameter_memory[entry_address + 0x2A]
        eg_attack_time = self.native_parameter_memory[entry_address + 0x2B]
        eg_decay_time = self.native_parameter_memory[entry_address + 0x2C]
        eg_release_time = self.native_parameter_memory[entry_address + 0x2D]
        vibrato_delay = self.native_parameter_memory[entry_address + 0x2E]

        scale_tuning_c = self.native_parameter_memory[entry_address + 0x2F]
        scale_tuning_c_sharp = self.native_parameter_memory[entry_address + 0x30]
        scale_tuning_d = self.native_parameter_memory[entry_address + 0x31]
        scale_tuning_d_sharp = self.native_parameter_memory[entry_address + 0x32]
        scale_tuning_e = self.native_parameter_memory[entry_address + 0x33]
        scale_tuning_f = self.native_parameter_memory[entry_address + 0x34]
        scale_tuning_f_sharp = self.native_parameter_memory[entry_address + 0x35]
        scale_tuning_g = self.native_parameter_memory[entry_address + 0x36]
        scale_tuning_g_sharp = self.native_parameter_memory[entry_address + 0x37]
        scale_tuning_a = self.native_parameter_memory[entry_address + 0x38]
        scale_tuning_a_sharp = self.native_parameter_memory[entry_address + 0x39]
        scale_tuning_b = self.native_parameter_memory[entry_address + 0x3A]

        mw_pitch_control = self.native_parameter_memory[entry_address + 0x3B]
        mw_filter_control = self.native_parameter_memory[entry_address + 0x3C]
        mw_amplitude_control = self.native_parameter_memory[entry_address + 0x3D]
        mw_lfo_pmod_depth = self.native_parameter_memory[entry_address + 0x3E]
        mw_lfo_fmod_depth = self.native_parameter_memory[entry_address + 0x3F]

        bend_pitch_control = self.native_parameter_memory[entry_address + 0x41]
        bend_filter_control = self.native_parameter_memory[entry_address + 0x42]
        bend_amplitude_control = self.native_parameter_memory[entry_address + 0x43]
        bend_lfo_pmod_depth = self.native_parameter_memory[entry_address + 0x44]
        bend_lfo_fmod_depth = self.native_parameter_memory[entry_address + 0x45]

        cat_pitch_control = self.native_parameter_memory[entry_address + 0x47]
        cat_filter_control = self.native_parameter_memory[entry_address + 0x48]
        cat_amplitude_control = self.native_parameter_memory[entry_address + 0x49]
        cat_lfo_pmod_depth = self.native_parameter_memory[entry_address + 0x4A]
        cat_lfo_fmod_depth = self.native_parameter_memory[entry_address + 0x4B]

        pat_pitch_control = self.native_parameter_memory[entry_address + 0x4D]
        pat_filter_control = self.native_parameter_memory[entry_address + 0x4E]
        pat_amplitude_control = self.native_parameter_memory[entry_address + 0x4F]
        pat_lfo_pmod_depth = self.native_parameter_memory[entry_address + 0x50]
        pat_lfo_fmod_depth = self.native_parameter_memory[entry_address + 0x51]

        ac_1_pitch_control = self.native_parameter_memory[entry_address + 0x53]
        ac_1_filter_control = self.native_parameter_memory[entry_address + 0x54]
        ac_1_amplitude_control = self.native_parameter_memory[entry_address + 0x55]
        ac_1_lfo_pmod_depth = self.native_parameter_memory[entry_address + 0x56]
        ac_1_lfo_fmod_depth = self.native_parameter_memory[entry_address + 0x57]

        ac_2_pitch_control = self.native_parameter_memory[entry_address + 0x59]
        ac_2_filter_control = self.native_parameter_memory[entry_address + 0x5A]
        ac_2_amplitude_control = self.native_parameter_memory[entry_address + 0x5B]
        ac_2_lfo_pmod_depth = self.native_parameter_memory[entry_address + 0x5C]
        ac_2_lfo_fmod_depth = self.native_parameter_memory[entry_address + 0x5D]

        portamento_switch = self.native_parameter_memory[entry_address + 0x5F]
        portamento_time = self.native_parameter_memory[entry_address + 0x60]

        return YamahaMmtTgMidiParameterChangeTableMultiPartEntry(
            bank_select_msb,
            bank_select_lsb,
            program_number,
            rcv_channel,
            rcv_pitch_bend,
            rcv_ch_after_touch,
            rcv_program_change,
            rcv_control_change,
            rcv_poly_after_touch,
            rcv_note_message,
            rcv_rpn,
            rcv_nrpn,
            rcv_modulation,
            rcv_volume,
            rcv_pan,
            rcv_expression,
            rcv_hold_1,
            rcv_portamento,
            rcv_sostenuto,
            rcv_soft_pedal,
            mono_poly_mode,
            same_note_number_key_on_assign,
            part_mode,
            note_shift,
            detune,
            volume,
            velocity_sense_depth,
            velocity_sense_offset,
            pan,
            note_limit_low,
            note_limit_high,
            ac_1_controller_number,
            ac_2_controller_number,
            dry_level,
            chorus_send,
            reverb_send,
            variation_send,
            vibrato_rate,
            vibrato_depth,
            filter_cutoff_frequency,
            filter_resonance,
            eg_attack_time,
            eg_decay_time,
            eg_release_time,
            vibrato_delay,
            scale_tuning_c,
            scale_tuning_c_sharp,
            scale_tuning_d,
            scale_tuning_d_sharp,
            scale_tuning_e,
            scale_tuning_f,
            scale_tuning_f_sharp,
            scale_tuning_g,
            scale_tuning_g_sharp,
            scale_tuning_a,
            scale_tuning_a_sharp,
            scale_tuning_b,
            mw_pitch_control,
            mw_filter_control,
            mw_amplitude_control,
            mw_lfo_pmod_depth,
            mw_lfo_fmod_depth,
            bend_pitch_control,
            bend_filter_control,
            bend_amplitude_control,
            bend_lfo_pmod_depth,
            bend_lfo_fmod_depth,
            cat_pitch_control,
            cat_filter_control,
            cat_amplitude_control,
            cat_lfo_pmod_depth,
            cat_lfo_fmod_depth,
            pat_pitch_control,
            pat_filter_control,
            pat_amplitude_control,
            pat_lfo_pmod_depth,
            pat_lfo_fmod_depth,
            ac_1_pitch_control,
            ac_1_filter_control,
            ac_1_amplitude_control,
            ac_1_lfo_pmod_depth,
            ac_1_lfo_fmod_depth,
            ac_2_pitch_control,
            ac_2_filter_control,
            ac_2_amplitude_control,
            ac_2_lfo_pmod_depth,
            ac_2_lfo_fmod_depth,
            portamento_switch,
            portamento_time,
        )

    def get_general_midi_track_setup_messages(
        self, port: int, tracks_per_sysex_track: int
    ):
        general_midi_messages: list[OkdPTrackAbsoluteTimeMessage] = []
        for part_number in range(tracks_per_sysex_track):
            track_number = (port * YamahaMmtTg.CHANNEL_COUNT_PER_PORT) + part_number
            channel = part_number % YamahaMmtTg.CHANNEL_COUNT_PER_PORT
            multi_part_entry = self.get_midi_parameter_change_table_multi_part_entry(
                part_number
            )
            for key, value in multi_part_entry._asdict().items():
                # if key == "bank_select_msb":
                #     midi_message = mido.Message(
                #         "control_change",
                #         channel=channel,
                #         control=0x00,
                #         value=value,
                #     )
                #     midi_message_data = bytes(midi_message.bin())
                #     general_midi_messages.append(
                #         OkdPTrackAbsoluteTimeMessage(
                #             0, port, track_number, midi_message_data
                #         ),
                #     )
                # elif key == "bank_select_lsb":
                #     midi_message = mido.Message(
                #         "control_change",
                #         channel=channel,
                #         control=0x20,
                #         value=value,
                #     )
                #     midi_message_data = bytes(midi_message.bin())
                #     general_midi_messages.append(
                #         OkdPTrackAbsoluteTimeMessage(
                #             0, port, track_number, midi_message_data
                #         ),
                #     )
                if key == "program_number":
                    midi_message = mido.Message(
                        "program_change", channel=channel, program=value
                    )
                    midi_message_data = bytes(midi_message.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            0, port, track_number, midi_message_data
                        ),
                    )
                elif key == "volume":
                    midi_message = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x07,
                        value=value,
                    )
                    midi_message_data = bytes(midi_message.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            0, port, track_number, midi_message_data
                        ),
                    )
                elif key == "pan":
                    midi_message = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x0A,
                        value=value,
                    )
                    midi_message_data = bytes(midi_message.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            0, port, track_number, midi_message_data
                        ),
                    )
                elif key == "chorus_send":
                    midi_message = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x5D,
                        value=value,
                    )
                    midi_message_data = bytes(midi_message.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            0, port, track_number, midi_message_data
                        ),
                    )
                elif key == "reverb_send":
                    midi_message = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x5B,
                        value=value,
                    )
                    midi_message_data = bytes(midi_message.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            0, port, track_number, midi_message_data
                        ),
                    )
                elif key == "variation_send":
                    midi_message = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x46,
                        value=value,
                    )
                    midi_message_data = bytes(midi_message.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            0, port, track_number, midi_message_data
                        ),
                    )
                elif key == "vibrato_rate":
                    midi_message = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x4C,
                        value=value,
                    )
                    midi_message_data = bytes(midi_message.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            0, port, track_number, midi_message_data
                        ),
                    )
                elif key == "vibrato_depth":
                    midi_message = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x4D,
                        value=value,
                    )
                    midi_message_data = bytes(midi_message.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            0, port, track_number, midi_message_data
                        ),
                    )
                elif key == "vibrato_delay":
                    midi_message = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x4E,
                        value=value,
                    )
                    midi_message_data = bytes(midi_message.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            0, port, track_number, midi_message_data
                        ),
                    )
                elif key == "bend_pitch_control":
                    midi_message_1 = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x65,
                        value=0x00,
                    )
                    midi_message_1_data = bytes(midi_message_1.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            0, port, track_number, midi_message_1_data
                        ),
                    )
                    midi_message_2 = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x64,
                        value=0x00,
                    )
                    midi_message_2_data = bytes(midi_message_2.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            0, port, track_number, midi_message_2_data
                        ),
                    )
                    midi_message_3 = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x06,
                        value=value - 0x40,
                    )
                    midi_message_3_data = bytes(midi_message_3.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            0, port, track_number, midi_message_3_data
                        ),
                    )
                elif key == "sysex_portamento_switch":
                    midi_message = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x41,
                        value=0x00 if value == 0x00 else 0x7F,
                    )
                    midi_message_data = bytes(midi_message.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            0, port, track_number, midi_message_data
                        ),
                    )
                elif key == "sysex_portamento_time":
                    midi_message = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x05,
                        value=value,
                    )
                    midi_message_data = bytes(midi_message.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            0, port, track_number, midi_message_data
                        ),
                    )

        return general_midi_messages

    def __sysex_message_to_general_midi_message(
        self,
        sysex_port: int,
        sysex_track_number: int,
        tracks_per_sysex_track: int,
        message: OkdPTrackAbsoluteTimeMessage,
    ):
        if not YamahaMmtTg.__is_sysex_message(message):
            YamahaMmtTg.__logger.warning("Invalid message.")
            return []

        if (
            not YamahaMmtTg.__is_native_parameter_change_message(message)
            or message.data[4] != 0x02
        ):
            self.receive_sysex_message(message)
            return []

        before_multi_part_state: list[
            YamahaMmtTgMidiParameterChangeTableMultiPartEntry
        ] = []
        for part_number in range(tracks_per_sysex_track):
            before_multi_part_entry = (
                self.get_midi_parameter_change_table_multi_part_entry(part_number)
            )
            before_multi_part_state.append(before_multi_part_entry)
        self.receive_sysex_message(message)
        general_midi_messages: list[OkdPTrackAbsoluteTimeMessage] = []
        for part_number in range(tracks_per_sysex_track):
            before_multi_part_entry = before_multi_part_state[part_number]
            after_multi_part_entry = (
                self.get_midi_parameter_change_table_multi_part_entry(part_number)
            )
            multi_part_entry_difference = (
                after_multi_part_entry._asdict().items()
                - before_multi_part_entry._asdict().items()
            )

            track_number = sysex_track_number + part_number
            channel = part_number % YamahaMmtTg.CHANNEL_COUNT_PER_PORT
            for key, value in multi_part_entry_difference:
                # if key == "bank_select_msb":
                #     midi_message = mido.Message(
                #         "control_change",
                #         channel=channel,
                #         control=0x00,
                #         value=value,
                #     )
                #     midi_message_data = bytes(midi_message.bin())
                #     general_midi_messages.append(
                #         OkdPTrackAbsoluteTimeMessage(
                #             message.time, sysex_port, track_number, midi_message_data
                #         ),
                #     )
                # elif key == "bank_select_lsb":
                #     midi_message = mido.Message(
                #         "control_change",
                #         channel=channel,
                #         control=0x20,
                #         value=value,
                #     )
                #     midi_message_data = bytes(midi_message.bin())
                #     general_midi_messages.append(
                #         OkdPTrackAbsoluteTimeMessage(
                #             message.time, sysex_port, track_number, midi_message_data
                #         ),
                #     )
                if key == "program_number":
                    midi_message = mido.Message(
                        "program_change", channel=channel, program=value
                    )
                    midi_message_data = bytes(midi_message.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            message.time, sysex_port, track_number, midi_message_data
                        ),
                    )
                elif key == "volume":
                    midi_message = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x07,
                        value=value,
                    )
                    midi_message_data = bytes(midi_message.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            message.time, sysex_port, track_number, midi_message_data
                        ),
                    )
                elif key == "pan":
                    midi_message = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x0A,
                        value=value,
                    )
                    midi_message_data = bytes(midi_message.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            message.time, sysex_port, track_number, midi_message_data
                        ),
                    )
                elif key == "chorus_send":
                    midi_message = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x5D,
                        value=value,
                    )
                    midi_message_data = bytes(midi_message.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            message.time, sysex_port, track_number, midi_message_data
                        ),
                    )
                elif key == "reverb_send":
                    midi_message = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x5B,
                        value=value,
                    )
                    midi_message_data = bytes(midi_message.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            message.time, sysex_port, track_number, midi_message_data
                        ),
                    )
                elif key == "variation_send":
                    midi_message = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x46,
                        value=value,
                    )
                    midi_message_data = bytes(midi_message.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            message.time, sysex_port, track_number, midi_message_data
                        ),
                    )
                elif key == "vibrato_rate":
                    midi_message = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x4C,
                        value=value,
                    )
                    midi_message_data = bytes(midi_message.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            message.time, sysex_port, track_number, midi_message_data
                        ),
                    )
                elif key == "vibrato_depth":
                    midi_message = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x4D,
                        value=value,
                    )
                    midi_message_data = bytes(midi_message.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            message.time, sysex_port, track_number, midi_message_data
                        ),
                    )
                elif key == "vibrato_delay":
                    midi_message = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x4E,
                        value=value,
                    )
                    midi_message_data = bytes(midi_message.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            message.time, sysex_port, track_number, midi_message_data
                        ),
                    )
                elif key == "bend_pitch_control":
                    midi_message_1 = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x65,
                        value=0x00,
                    )
                    midi_message_1_data = bytes(midi_message_1.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            message.time, sysex_port, track_number, midi_message_1_data
                        ),
                    )
                    midi_message_2 = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x64,
                        value=0x00,
                    )
                    midi_message_2_data = bytes(midi_message_2.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            message.time, sysex_port, track_number, midi_message_2_data
                        ),
                    )
                    midi_message_3 = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x06,
                        value=value - 0x40,
                    )
                    midi_message_3_data = bytes(midi_message_3.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            message.time, sysex_port, track_number, midi_message_3_data
                        ),
                    )
                elif key == "sysex_portamento_switch":
                    midi_message = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x41,
                        value=0x00 if value == 0x00 else 0x7F,
                    )
                    midi_message_data = bytes(midi_message.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            message.time, sysex_port, track_number, midi_message_data
                        ),
                    )
                elif key == "sysex_portamento_time":
                    midi_message = mido.Message(
                        "control_change",
                        channel=channel,
                        control=0x05,
                        value=value,
                    )
                    midi_message_data = bytes(midi_message.bin())
                    general_midi_messages.append(
                        OkdPTrackAbsoluteTimeMessage(
                            message.time, sysex_port, track_number, midi_message_data
                        ),
                    )

        return general_midi_messages

    def sysex_messages_to_general_midi_messages(
        self,
        sysex_port: int,
        sysex_track_number: int,
        tracks_per_sysex_track: int,
        messages: list[OkdPTrackAbsoluteTimeMessage],
    ):
        general_midi_messages: list[OkdPTrackAbsoluteTimeMessage] = []
        for message in messages:
            status_byte = message.data[0]
            if status_byte != 0xF0:
                continue

            general_midi_message = self.__sysex_message_to_general_midi_message(
                sysex_port, sysex_track_number, tracks_per_sysex_track, message
            )
            general_midi_messages.extend(general_midi_message)

        return general_midi_messages

    sound_module_mode: int
    native_parameter_memory: list[int]
