#!/usr/bin/env python
# coding: utf-8

import argparse
import io
import os
import simplejson

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.okd_file import OkdFile, OkdFileType
from dam_okd_utility.okd_file_data import OkdGenericChunk
from dam_okd_utility.okd_midi import OkdMidiMessage
from dam_okd_utility.okd_m_track_chunk import OkdMTrackChunk
from dam_okd_utility.okd_p_track_info_chunk import (
    OkdPTrackInfoChunk,
    OkdPTrackInfoEntry,
)
from dam_okd_utility.okd_p3_track_info_chunk import (
    OkdP3TrackInfoChunk,
)
from dam_okd_utility.okd_extended_p_track_info_chunk import (
    OkdExtendedPTrackInfoChunk,
    OkdExtendedPTrackInfoEntry,
)
from dam_okd_utility.okd_p_track_chunk import OkdPTrackChunk
from dam_okd_utility.okd_adpcm_chunk import OkdAdpcmChunk


class DamOkdDumper:
    __logger = getLogger("DamOkdDumper")

    @staticmethod
    def dump(stream: io.BufferedReader, directory_path: str):
        chunks_stream = io.BytesIO()
        okd_header = OkdFile.decrypt(stream, chunks_stream, OkdFileType.OKD)
        DamOkdDumper.__logger.info(f"Header found. header={okd_header}")

        chunks_stream.seek(0)
        chunks_buffer = chunks_stream.read()
        output_path = os.path.join(directory_path, "chunks.bin")
        with open(output_path, "wb") as output_file:
            output_file.write(chunks_buffer)

        p_track_info: list[OkdPTrackInfoEntry] | list[
            OkdExtendedPTrackInfoEntry
        ] | list[OkdP3TrackInfoChunk] | None = None
        p_tracks: list[tuple[int, list[OkdMidiMessage]]] = []

        chunks_stream.seek(0)
        chunk_index = OkdFile.index_chunk(chunks_stream)
        chunks_stream.seek(0)
        for chunk_position, chunk_size in chunk_index:
            chunks_stream.seek(chunk_position)
            chunk_buffer = chunks_stream.read(chunk_size)

            generic_chunk: OkdGenericChunk
            try:
                generic_chunk = OkdFile.parse_generic_chunk(chunk_buffer)
            except:
                DamOkdDumper.__logger.info(f"Unchunked data found.")
                unchunked_buffer = chunk_buffer
                output_path = os.path.join(directory_path, "unchunked.bin")
                with open(output_path, "wb") as output_file:
                    output_file.write(unchunked_buffer)
                continue
            output_path = os.path.join(
                directory_path, "chunk_0x" + generic_chunk.chunk_id.hex() + ".bin"
            )
            with open(output_path, "wb") as output_file:
                output_file.write(generic_chunk.data)

            chunk = OkdFile.parse_chunk(chunk_buffer)
            DamOkdDumper.__logger.info(
                f"{type(chunk).__name__} found. chunk_id={generic_chunk.chunk_id}, chunk_id_hex={generic_chunk.chunk_id.hex()}"
            )

            if isinstance(chunk, OkdMTrackChunk):
                track_number = chunk_buffer[3]
                output_path = os.path.join(
                    directory_path, "m_track_" + str(track_number) + ".json"
                )
                output_json = simplejson.dumps(
                    chunk.to_json_serializable(),
                    sort_keys=True,
                    indent=2,
                )
                with open(output_path, "w") as output_file:
                    output_file.write(output_json)
            elif isinstance(chunk, OkdPTrackInfoChunk):
                output_path = os.path.join(directory_path, "p_track_info.json")
                output_json = simplejson.dumps(
                    chunk,
                    indent=2,
                )
                with open(output_path, "w") as output_file:
                    output_file.write(output_json)

                p_track_info = chunk.data
            elif isinstance(chunk, OkdExtendedPTrackInfoChunk):
                output_path = os.path.join(directory_path, "extended_p_track_info.json")
                output_json = simplejson.dumps(
                    chunk,
                    sort_keys=True,
                    indent=2,
                )
                with open(output_path, "w") as output_file:
                    output_file.write(output_json)

                p_track_info = chunk.data
            elif isinstance(chunk, OkdP3TrackInfoChunk):
                output_path = os.path.join(directory_path, "p3_track_info.json")
                output_json = simplejson.dumps(
                    chunk,
                    indent=2,
                )
                with open(output_path, "w") as output_file:
                    output_file.write(output_json)

                p_track_info = [chunk]
            elif isinstance(chunk, OkdPTrackChunk):
                track_number = chunk_buffer[3]
                output_path = os.path.join(
                    directory_path, "p_track_" + str(track_number) + ".json"
                )
                output_json = simplejson.dumps(
                    chunk.to_json_serializable(),
                    sort_keys=True,
                    indent=2,
                )
                with open(output_path, "w") as output_file:
                    output_file.write(output_json)

                p_tracks.append((track_number, chunk.messages))
            elif isinstance(chunk, OkdAdpcmChunk):
                for index, adpcm in enumerate(chunk.adpcms):
                    output_path = os.path.join(
                        directory_path, "adpcm_" + str(index) + ".bin"
                    )
                    with open(output_path, "wb") as output_file:
                        output_file.write(adpcm)

        output_path = os.path.join(directory_path, "p_track.mid")
        p_track_midi = OkdPTrackChunk.to_midi(p_track_info, p_tracks)
        p_track_midi.save(output_path)


def main(argv=None):
    parser = argparse.ArgumentParser(description="DAM OKD Extractor")
    parser.add_argument("input_path", help="Input DAM OKD file path")
    parser.add_argument("output_path", help="Output directory path")
    args = parser.parse_args()

    with open(args.input_path, "rb") as input_file:
        DamOkdDumper.dump(input_file, args.output_path)


if __name__ == "__main__":
    main()
