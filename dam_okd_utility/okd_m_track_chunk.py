import bitstring
import mido
from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.midi import (
    get_first_tempo,
    get_first_port_track,
    get_port_channel_track,
    get_first_note_time,
    get_last_note_time,
)
from dam_okd_utility.okd_midi import OkdMidiMessage
from dam_okd_utility.okd_m_track_midi import OkdMTrackMidi


class OkdMTrackInterpretation(NamedTuple):
    tempos: list[tuple[int, int]]
    time_signatures: list[tuple[int, int]]
    hooks: list[tuple[int, int]]
    visible_guide_melody_delimiters: list[tuple[int, int]]
    two_chorus_fadeout_time: int
    song_section: tuple[int, int]
    adpcm_sections: list[tuple[int, int]]
    unknown_ff: list[tuple[int, bytes]]


class OkdMTrackChunk(NamedTuple):
    """DAM OKD M-Track Chunk"""

    MIDI_M_TRACK_PORT = 15

    __logger = getLogger("OkdMTrackChunk")

    @staticmethod
    def read(stream: bitstring.BitStream, chunk_number: int):
        messages = OkdMTrackMidi.read(stream)
        return OkdMTrackChunk(chunk_number, messages)

    @staticmethod
    def to_interpretation(relative_time_track: list[OkdMidiMessage]):
        absolute_time_track = OkdMTrackMidi.relative_time_track_to_absolute_time_track(
            relative_time_track
        )

        tempos: list[tuple[int, int]] = []
        time_signatures: list[tuple[int, int]] = []
        hooks: list[tuple[int, int]] = []
        visible_guide_melody_delimiters: list[tuple[int, int]] = []
        two_chorus_fadeout_time = -1
        song_section: tuple[int, int] = (-1, -1)
        adpcm_sections: list[tuple[int, int]] = []
        unknown_ff: list[tuple[int, bytes]] = []

        current_measure_start = -1
        current_beats = 0
        beats = 0
        current_beat_start = -1
        current_bpm = 125
        current_hook_start_time = 0
        song_section_start = -1
        current_adpcm_section_start = -1

        for absolute_time_message in absolute_time_track:
            status_byte = absolute_time_message.data[0]
            if status_byte == 0xF1:
                if current_beat_start != -1:
                    beat_length = absolute_time_message.time - current_beat_start
                    bpm = round(60000 / beat_length)
                    if bpm != current_bpm:
                        tempos.append((current_beat_start, bpm))
                    current_bpm = bpm

                if current_measure_start != -1 and beats != current_beats:
                    time_signatures.append((current_measure_start, beats))

                current_measure_start = absolute_time_message.time
                current_beats = beats
                beats = 1
                current_beat_start = absolute_time_message.time
            elif status_byte == 0xF2:
                if current_beat_start != -1:
                    beat_length = absolute_time_message.time - current_beat_start
                    bpm = round(60000 / beat_length)
                    if bpm != current_bpm:
                        tempos.append((current_beat_start, bpm))
                    current_bpm = bpm

                beats += 1
                current_beat_start = absolute_time_message.time
            elif status_byte == 0xF3:
                mark_type = absolute_time_message.data[1]
                if mark_type == 0x00 or mark_type == 0x02:
                    current_hook_start_time = absolute_time_message.time
                elif mark_type == 0x01 or mark_type == 0x03:
                    hooks.append((current_hook_start_time, absolute_time_message.time))
            elif status_byte == 0xF4:
                visible_guide_melody_delimiters.append(
                    (absolute_time_message.time, absolute_time_message.data[1])
                )
                pass
            elif status_byte == 0xF5:
                two_chorus_fadeout_time = absolute_time_message.time
            elif status_byte == 0xF6:
                mark_type = absolute_time_message.data[1]
                if mark_type == 0x00:
                    song_section_start = absolute_time_message.time
                elif mark_type == 0x01:
                    song_section = (song_section_start, absolute_time_message.time)
            elif status_byte == 0xF8:
                mark_type = absolute_time_message.data[1]
                if mark_type == 0x00:
                    current_adpcm_section_start = absolute_time_message.time
                elif mark_type == 0x01:
                    adpcm_sections.append(
                        (current_adpcm_section_start, absolute_time_message.time)
                    )
            elif status_byte == 0xFF:
                unknown_ff.append(
                    (absolute_time_message.time, absolute_time_message.data[1:-1])
                )

        return OkdMTrackInterpretation(
            tempos,
            time_signatures,
            hooks,
            visible_guide_melody_delimiters,
            two_chorus_fadeout_time,
            song_section,
            adpcm_sections,
            unknown_ff,
        )

    @staticmethod
    def from_midi(karaoke_midi: mido.MidiFile):
        karaoke_midi_m_track = get_first_port_track(
            karaoke_midi, OkdMTrackChunk.MIDI_M_TRACK_PORT
        )
        melody_track: mido.MidiTrack
        if karaoke_midi_m_track is None:
            OkdMTrackChunk.__logger.warning("M-Track not found.")

        melody_track = get_port_channel_track(karaoke_midi, 1, 8)
        if melody_track is None:
            raise ValueError("Melody track not found.")

        karaoke_midi_tempo = get_first_tempo(karaoke_midi)
        ppq_conversion_ratio = 480.0 / karaoke_midi.ticks_per_beat
        tempo_conversion_ratio = 125.0 / mido.tempo2bpm(karaoke_midi_tempo)
        time_conversion_ratio = ppq_conversion_ratio * tempo_conversion_ratio

        first_note_time = round(get_first_note_time(karaoke_midi) * time_conversion_ratio)
        last_note_time = round(get_last_note_time(karaoke_midi) * time_conversion_ratio)

        hooks: list[tuple[int, int]] = []

        current_hook_start = -1
        two_chorus_fadeout_time = -1

        if karaoke_midi_m_track is not None:
            absolute_time = 0
            for karaoke_midi_message in karaoke_midi_m_track:
                absolute_time += karaoke_midi_message.time
                converted_absoulte_time = round(absolute_time * time_conversion_ratio)

                if not isinstance(karaoke_midi_message, mido.Message):
                    continue

                if karaoke_midi_message.type == "note_on":
                    if karaoke_midi_message.note == 48:
                        current_hook_start = converted_absoulte_time
                    elif karaoke_midi_message.note == 108:
                        two_chorus_fadeout_time = converted_absoulte_time
                elif karaoke_midi_message.type == "note_off":
                    if karaoke_midi_message.note == 48:
                        hooks.append((current_hook_start, converted_absoulte_time))

        melody_notes: list[tuple[int, int]] = []
        current_melody_note_start = -1
        current_melody_node_number = -1

        absolute_time = 0
        for karaoke_midi_message in melody_track:
            absolute_time += karaoke_midi_message.time
            converted_absoulte_time = round(absolute_time * time_conversion_ratio)

            if not isinstance(karaoke_midi_message, mido.Message):
                continue

            if karaoke_midi_message.type == "note_on":
                current_melody_note_start = converted_absoulte_time
                current_melody_node_number = karaoke_midi_message.note
            elif (
                karaoke_midi_message.type == "note_off"
                and karaoke_midi_message.note == current_melody_node_number
            ):
                melody_notes.append(
                    (current_melody_note_start, converted_absoulte_time)
                )

        if len(melody_notes) < 1:
            raise ValueError("Melody note not found.")

        melody_notes_copy = melody_notes.copy()
        visible_guide_melody_delimiters: list[tuple[int, int]] = []
        current_page_start = -1
        while True:
            melody_note: tuple[int, int]
            try:
                melody_note = melody_notes_copy.pop(0)
            except IndexError:
                break
            melody_note_start, melody_note_end = melody_note

            if current_page_start == -1:
                current_page_start = melody_note_start
                visible_guide_melody_delimiters.append((melody_note_start, 0))
                continue

            next_melody_note: tuple[int, int]
            try:
                next_melody_note = melody_notes_copy[0]
            except IndexError:
                visible_guide_melody_delimiters.append((melody_note_end, 2))
                break
            next_melody_note_start, next_melody_note_end = next_melody_note

            page_length = melody_note_end - current_page_start
            if 8000 < page_length:
                void_length = next_melody_note_start - melody_note_end
                if 8000 < void_length:
                    melody_notes_copy.pop(0)
                    visible_guide_melody_delimiters.append((next_melody_note_end, 1))
                    current_page_start = -1
                else:
                    visible_guide_melody_delimiters.append((melody_note_end, 3))
                    current_page_start = next_melody_note_start

        absolute_time_messages: list[tuple[int, bytes]] = []

        current_beat_time = 0
        current_beat_count = 4
        while current_beat_time < melody_notes[-1][0]:
            if current_beat_count < 4:
                absolute_time_messages.append((current_beat_time, b"\xF2"))
                current_beat_count += 1
            else:
                absolute_time_messages.append((current_beat_time, b"\xF1"))
                current_beat_count = 1

            current_beat_time += karaoke_midi.ticks_per_beat

        absolute_time_messages.append((0, b"\xFF\x00\x04\x02\xFE"))

        absolute_time_messages.append((first_note_time, b"\xFF\x00\x04\x02\xFE"))
        absolute_time_messages.append((first_note_time, b"\xF6\x00"))
        absolute_time_messages.append((last_note_time, b"\xF6\x01"))

        for hook_start, hook_end in hooks[:-1]:
            absolute_time_messages.append((hook_start, b"\xF3\x00"))
            absolute_time_messages.append((hook_end, b"\xF3\x01"))

        if len(hooks) != 0:
            last_hook_start, last_hook_end = hooks[-1]
            absolute_time_messages.append((last_hook_start, b"\xF3\x02"))
            absolute_time_messages.append((last_hook_end, b"\xF3\x03"))

        for (
            visible_guide_melody_delimiter_time,
            visible_guide_melody_delimiter_type,
        ) in visible_guide_melody_delimiters:
            absolute_time_messages.append(
                (
                    visible_guide_melody_delimiter_time,
                    b"\xF4"
                    + visible_guide_melody_delimiter_type.to_bytes(1, byteorder="big"),
                )
            )

        if two_chorus_fadeout_time != -1:
            absolute_time_messages.append((two_chorus_fadeout_time, b"\xF5"))

        absolute_time_messages.sort(
            key=lambda absolute_time_message: absolute_time_message[0]
        )

        relative_time_messages: list[OkdMidiMessage] = []
        current_time = 0
        for absolute_time, message_buffer in absolute_time_messages:
            delta_time = absolute_time - current_time
            relative_time_messages.append(OkdMidiMessage(delta_time, message_buffer, 0))
            print(OkdMidiMessage(delta_time, message_buffer, 0))

            current_time = absolute_time

        return OkdMTrackChunk(0x00, relative_time_messages)

    @staticmethod
    def interpretation_to_midi(interpretation: OkdMTrackInterpretation):

        midi = mido.MidiFile()
        midi_track = mido.MidiTrack()
        # Tempo
        midi_track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(125)))
        # Port
        midi_track.append(
            mido.MetaMessage(
                "midi_port",
                port=0,
            )
        )

        for hook_start, hook_end in interpretation.hooks:
            midi_track.append(mido.Message("note_on", note=48, time=hook_start))
            midi_track.append(mido.Message("note_off", note=48, time=hook_end))

        if interpretation.two_chorus_fadeout_time != -1:
            midi_track.append(
                mido.Message(
                    "note_on", note=72, time=interpretation.two_chorus_fadeout_time
                )
            )
            midi_track.append(
                mido.Message(
                    "note_off",
                    note=72,
                    time=interpretation.two_chorus_fadeout_time + 1000,
                )
            )

        for adpcm_section_start, adpcm_section_end in interpretation.adpcm_sections:
            midi_track.append(
                mido.Message("note_on", note=108, time=adpcm_section_start)
            )
            midi_track.append(
                mido.Message("note_off", note=108, time=adpcm_section_end)
            )

        midi_track.sort(key=lambda midi_message: midi_message.time)

        current_time = 0
        for midi_message in midi_track:
            absolute_time = midi_message.time
            delta_time = absolute_time - current_time
            midi_message.time = delta_time
            current_time = absolute_time

        midi.tracks.append(midi_track)

        return midi

    def write(self, stream: bitstring.BitStream):
        OkdMTrackMidi.write(stream, self.messages)

    def to_json_serializable(self):
        json_track = []
        for message in self.messages:
            json_track.append(
                {
                    "delta_time": message.delta_time,
                    "data_hex": message.data.hex(" "),
                    "duration": message.duration,
                }
            )
        return {"track": json_track}

    chunk_number: int
    messages: list[OkdMidiMessage]
