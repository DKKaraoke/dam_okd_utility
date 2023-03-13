#!/usr/bin/env python
# coding: utf-8

import argparse
import io
import mido
import mimetypes
import simplejson

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.midi import (
    get_first_tempo,
    get_port_channel_track,
    remove_port_tracks,
)
from dam_okd_utility.okd_file import OkdFile
from dam_okd_utility.okd_m_track_chunk import OkdMTrackChunk
from dam_okd_utility.okd_p_track_info_chunk import (
    OkdPTrackInfoChannelInfoEntry,
    OkdPTrackInfoEntry,
    OkdPTrackInfoChunk,
)
from dam_okd_utility.okd_extended_p_track_info_chunk import (
    OkdExtendedPTrackInfoChannelInfoEntry,
    OkdExtendedPTrackInfoEntry,
    OkdExtendedPTrackInfoChunk,
)
from dam_okd_utility.okd_p3_track_info_chunk import (
    OkdP3TrackInfoChunk,
)
from dam_okd_utility.okd_p_track_chunk import OkdPTrackChunk


class DamOkdComposer:
    __logger = getLogger("DamOkdComposer")

    @staticmethod
    def __exists_p_track_channel_message(p_track_chunk: OkdPTrackChunk, channel: int):
        for message in p_track_chunk.messages:
            status_byte = message.data[0]
            status_type = status_byte & 0xF0
            if status_type == 0xF0:
                continue

            message_channel = status_byte & 0x0F
            if message_channel == channel:
                return True

        return False

    @staticmethod
    def __p_track_info_chunk_from_p_track_chunks(p_track_chunks: list[OkdPTrackChunk]):
        if len(p_track_chunks) <= 2:
            p_track_info_entries: list[OkdPTrackInfoEntry] = []
            for p_track_chunk in p_track_chunks:
                ports = (
                    0x0001
                    << OkdPTrackChunk.CHUNK_NUMBER_PORT_MAP[p_track_chunk.chunk_number]
                )

                track_info_channel_info_entries: list[
                    OkdPTrackInfoChannelInfoEntry
                ] = []
                for channel in range(16):
                    exists_message = DamOkdComposer.__exists_p_track_channel_message(
                        p_track_chunk, channel
                    )
                    channel_attribute = (
                        127 if p_track_chunk.chunk_number == 1 and channel == 9 else 255
                    )
                    track_info_channel_info_entries.append(
                        OkdPTrackInfoChannelInfoEntry(
                            channel_attribute if exists_message else 0,
                            ports,
                            0x00,
                            0x00,
                        )
                    )

                p_track_info_entries.append(
                    OkdPTrackInfoEntry(
                        p_track_chunk.chunk_number,
                        0x40,
                        0x0000,
                        [0] * 16,
                        [0] * 16,
                        track_info_channel_info_entries,
                        ports,
                    )
                )

            return OkdPTrackInfoChunk(p_track_info_entries)

        else:
            p_track_info_entries: list[OkdExtendedPTrackInfoEntry] = []
            for p_track_chunk in p_track_chunks:
                ports = (
                    0x0001
                    << OkdPTrackChunk.CHUNK_NUMBER_PORT_MAP[p_track_chunk.chunk_number]
                )

                track_info_channel_info_entries: list[
                    OkdExtendedPTrackInfoChannelInfoEntry
                ] = []
                for channel in range(16):
                    exists_message = DamOkdComposer.__exists_p_track_channel_message(
                        p_track_chunk, channel
                    )
                    channel_attribute = (
                        127 if p_track_chunk.chunk_number == 1 and channel == 9 else 255
                    )
                    track_info_channel_info_entries.append(
                        OkdExtendedPTrackInfoChannelInfoEntry(
                            channel_attribute if exists_message else 0,
                            ports,
                            0x00,
                            0x00,
                            0x00,
                        )
                    )

                p_track_info_entries.append(
                    OkdExtendedPTrackInfoEntry(
                        p_track_chunk.chunk_number,
                        0x40,
                        0x00,
                        [0] * 16,
                        [0] * 16,
                        track_info_channel_info_entries,
                        ports,
                        0x00,
                    )
                )

            return OkdExtendedPTrackInfoChunk(0x00, p_track_info_entries)

    @staticmethod
    def __p3_track_info_chunk_from_p3_track_chunk(p_track_chunk: OkdPTrackChunk):
        track_info_channel_info_entries: list[OkdPTrackInfoChannelInfoEntry] = []
        for channel in range(16):
            exists_message = DamOkdComposer.__exists_p_track_channel_message(
                p_track_chunk, channel
            )
            track_info_channel_info_entries.append(
                OkdPTrackInfoChannelInfoEntry(
                    255 if exists_message else 0,
                    0x0004,
                    0x00,
                    0x00,
                )
            )

        return OkdP3TrackInfoChunk(
            0x02,
            0x40,
            0x0000,
            [0] * 16,
            [0] * 16,
            track_info_channel_info_entries,
            0x0004,
        )

    @staticmethod
    def compose(
        main_output_stream: io.BufferedWriter,
        scoring_reference_output_stream: io.BufferedWriter,
        karaoke_path: str,
    ):
        karaoke_midi = mido.MidiFile(karaoke_path)

        m_track_chunk = OkdMTrackChunk.from_midi(karaoke_midi)
        # Remove M-Track
        remove_port_tracks(karaoke_midi, 15)
        p_track_chunks = OkdPTrackChunk.from_midi(karaoke_midi)
        p_track_info_chunk = DamOkdComposer.__p_track_info_chunk_from_p_track_chunks(
            p_track_chunks
        )

        OkdFile.scramble(
            main_output_stream, [p_track_info_chunk, m_track_chunk, *p_track_chunks]
        )

        p3_track_midi = mido.MidiFile()
        karaoke_p3_track = get_port_channel_track(karaoke_midi, 1, 8)
        if karaoke_p3_track is None:
            raise ValueError("Melody track not found.")

        karaoke_p3_track = [
            message
            for message in karaoke_p3_track
            if message.type == "midi_port"
            or message.type == "note_on"
            or message.type == "note_off"
        ]
        karaoke_midi_tempo = get_first_tempo(karaoke_midi)
        karaoke_p3_track.append(mido.MetaMessage("set_tempo", tempo=karaoke_midi_tempo))
        for message in karaoke_p3_track:
            if message.type == "midi_port":
                message.port = 2
            if hasattr(message, "channel"):
                message.channel = 14
        p3_track_midi.tracks.append(karaoke_p3_track)

        p3_track_chunk = OkdPTrackChunk.from_midi(p3_track_midi)[0]
        p3_track_info_chunk = DamOkdComposer.__p3_track_info_chunk_from_p3_track_chunk(
            p3_track_chunk
        )

        OkdFile.scramble(
            scoring_reference_output_stream, [p3_track_info_chunk, p3_track_chunk]
        )


def main(argv=None):
    parser = argparse.ArgumentParser(description="DAM OKD Composer")
    parser.add_argument("karaoke_path", help="Karaoke MIDI file path")
    parser.add_argument("main_output_path", help="Output Main file path")
    parser.add_argument(
        "scoring_reference_output_path", help="Output Scoring reference file path"
    )
    args = parser.parse_args()

    with open(args.main_output_path, "wb") as main_output_stream, open(
        args.scoring_reference_output_path, "wb"
    ) as scoring_reference_output_stream:
        DamOkdComposer.compose(
            main_output_stream,
            scoring_reference_output_stream,
            args.karaoke_path,
        )


if __name__ == "__main__":
    main()
