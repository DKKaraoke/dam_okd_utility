#!/usr/bin/env python
# coding: utf-8

import argparse
import io
import mido
import mimetypes
import simplejson

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.okd_file import OkdFile
from dam_okd_utility.okd_file_data import OkdChunk
from dam_okd_utility.okd_p_track_info_chunk import (
    OkdPTrackInfoChunk,
)
from dam_okd_utility.okd_p3_track_info_chunk import (
    OkdP3TrackInfoChunk,
)
from dam_okd_utility.okd_p_track_chunk import OkdPTrackChunk


class DamOkdPacker:
    __logger = getLogger("DamOkdPacker")

    @staticmethod
    def load_json(stream: io.BufferedReader):
        raw_json_object = simplejson.load(stream)

        stream.seek(0)
        if "data" in raw_json_object:
            p_track_info_chunk: OkdPTrackInfoChunk = simplejson.load(
                stream, object_hook=OkdPTrackInfoChunk.from_json_object
            )
            DamOkdPacker.__logger.info("P-Track Information loaded.")
            return p_track_info_chunk
        elif "track_number" in raw_json_object:
            p3_track_info_chunk: OkdP3TrackInfoChunk = simplejson.load(
                stream, object_hook=OkdP3TrackInfoChunk.from_json_object
            )
            DamOkdPacker.__logger.info("P3-Track Information loaded.")
            return p3_track_info_chunk

    @staticmethod
    def load_file(path: str):
        mime_type: tuple[(str | None), (str | None)] = mimetypes.guess_type(path)
        with open(path, "rb") as input_file:
            if mime_type[0] == "application/json":
                return DamOkdPacker.load_json(input_file)
            elif mime_type[0] == "audio/sp-midi":
                midi = mido.MidiFile(file=input_file)
                p_track_chunk = OkdPTrackChunk.from_midi(midi)
                DamOkdPacker.__logger.info("P-Track loaded.")
                return p_track_chunk

        raise ValueError(f"Unknown file type detected. mime_type={mime_type[0]}")

    @staticmethod
    def pack(
        output_stream: io.BufferedWriter,
        *input_file_paths: str,
    ):
        chunks: list[OkdChunk] = []
        for input_file_path in input_file_paths:
            chunk = DamOkdPacker.load_file(input_file_path)
            if chunk is None:
                continue

            if isinstance(chunk, list):
                chunks.extend(chunk)
            else:
                chunks.append(chunk)

        OkdFile.encrypt(output_stream, chunks)


def main(argv=None):
    parser = argparse.ArgumentParser(description="DAM OKD Creator")
    parser.add_argument("output_path", help="Output DAM OKD file path")
    parser.add_argument("input_path", help="Input file path", nargs="*")
    args = parser.parse_args()

    with open(args.output_path, "wb") as output_file:
        DamOkdPacker.pack(output_file, *args.input_path)


if __name__ == "__main__":
    main()
