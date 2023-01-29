import bitstring
import mido
from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.midi import get_first_tempo, is_meta_track, get_track_port
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
