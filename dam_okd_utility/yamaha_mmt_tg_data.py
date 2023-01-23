from typing import NamedTuple


class YamahaMmtTgMidiParameterChangeTableSystem(NamedTuple):
    master_tune: int
    master_volume: int
    transpose: int
    master_pan: int
    master_cutoff: int
    master_pitch_modulation_depth: int
    variation_effect_send_control_change_number: int


class YamahaMmtTgMidiParameterChangeTableMultiEffect(NamedTuple):
    chorus_type: int
    variation_type: int
    pre_variation_type: int
    pre_reverb_type: int
    reverb_input: int
    chorus_input: int
    variation_input: int
    dry_level: int
    reverb_return: int
    chorus_return: int
    variation_return: int
    send_variation_to_chorus: int
    send_variation_to_reverb: int
    send_chorus_to_reverb: int

    chorus_param_1: int
    chorus_param_2: int
    chorus_param_3: int
    chorus_param_4: int
    chorus_param_5: int
    chorus_param_6: int
    chorus_param_7: int
    chorus_param_8: int
    chorus_param_9: int
    chorus_param_10: int

    variation_param_1_msb: int
    variation_param_1_lsb: int
    variation_param_2_msb: int
    variation_param_2_lsb: int
    variation_param_3_msb: int
    variation_param_3_lsb: int
    variation_param_4_msb: int
    variation_param_4_lsb: int
    variation_param_5_msb: int
    variation_param_5_lsb: int
    variation_param_6: int
    variation_param_7: int
    variation_param_8: int
    variation_param_9: int
    variation_param_10: int

    pre_variation_param_1: int
    pre_variation_param_2: int
    pre_variation_param_3: int
    pre_variation_param_4: int
    pre_variation_param_5: int
    pre_variation_param_6: int
    pre_variation_param_7: int
    pre_variation_param_8: int

    pre_reverb_param_1: int
    pre_reverb_param_2: int
    pre_reverb_param_3: int
    pre_reverb_param_4: int
    pre_reverb_param_5: int
    pre_reverb_param_6: int
    pre_reverb_param_7: int
    pre_reverb_param_8: int
    pre_reverb_param_9: int

    reverb_param_1: int
    reverb_param_2: int
    reverb_param_3: int
    reverb_param_4: int
    reverb_param_5: int
    reverb_param_6: int
    reverb_param_7: int
    reverb_param_8: int
    reverb_param_9: int
    reverb_param_10: int


class YamahaMmtTgMidiParameterChangeTableMultiPartEntry(NamedTuple):
    bank_select_msb: int
    bank_select_lsb: int
    program_number: int
    rcv_channel: int
    rcv_pitch_bend: int
    rcv_ch_after_touch: int
    rcv_program_change: int
    rcv_control_change: int
    rcv_poly_after_touch: int
    rcv_note_message: int
    rcv_rpn: int
    rcv_nrpn: int
    rcv_modulation: int
    rcv_volume: int
    rcv_pan: int
    rcv_expression: int
    rcv_hold_1: int
    rcv_portamento: int
    rcv_sostenuto: int
    rcv_soft_pedal: int

    mono_poly_mode: int
    same_note_number_key_on_assign: int
    part_mode: int
    note_shift: int
    detune: int
    volume: int
    velocity_sense_depth: int
    velocity_sense_offset: int
    pan: int
    note_limit_low: int
    note_limit_high: int
    ac_1_controller_number: int
    ac_2_controller_number: int
    dry_level: int
    chorus_send: int
    reverb_send: int
    variation_send: int

    vibrato_rate: int
    vibrato_depth: int
    filter_cutoff_frequency: int
    filter_resonance: int
    eg_attack_time: int
    eg_decay_time: int
    eg_release_time: int
    vibrato_delay: int

    scale_tuning_c: int
    scale_tuning_c_sharp: int
    scale_tuning_d: int
    scale_tuning_d_sharp: int
    scale_tuning_e: int
    scale_tuning_f: int
    scale_tuning_f_sharp: int
    scale_tuning_g: int
    scale_tuning_g_sharp: int
    scale_tuning_a: int
    scale_tuning_a_sharp: int
    scale_tuning_b: int

    mw_pitch_control: int
    mw_filter_control: int
    mw_amplitude_control: int
    mw_lfo_pmod_depth: int
    mw_lfo_fmod_depth: int

    bend_pitch_control: int
    bend_filter_control: int
    bend_amplitude_control: int
    bend_lfo_pmod_depth: int
    bend_lfo_fmod_depth: int

    cat_pitch_control: int
    cat_filter_control: int
    cat_amplitude_control: int
    cat_lfo_pmod_depth: int
    cat_lfo_fmod_depth: int

    pat_pitch_control: int
    pat_filter_control: int
    pat_amplitude_control: int
    pat_lfo_pmod_depth: int
    pat_lfo_fmod_depth: int

    ac_1_pitch_control: int
    ac_1_filter_control: int
    ac_1_amplitude_control: int
    ac_1_lfo_pmod_depth: int
    ac_1_lfo_fmod_depth: int

    ac_2_pitch_control: int
    ac_2_filter_control: int
    ac_2_amplitude_control: int
    ac_2_lfo_pmod_depth: int
    ac_2_lfo_fmod_depth: int

    portamento_switch: int
    portamento_time: int
