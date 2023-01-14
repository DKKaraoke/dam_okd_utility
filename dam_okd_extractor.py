#!/usr/bin/env python
# coding: utf-8

import argparse
import io
import os

from dam_okd_utility.okd_file import OkdFile, OkdFileType
from dam_okd_utility.okd_p_track_chunk import OkdPTrackChunk
from dam_okd_utility.okd_adpcm_chunk import OkdAdpcmChunk


def main(argv=None):
    parser = argparse.ArgumentParser(
        description='DAM OKD Extractor')
    parser.add_argument(
        "input_path", help='Input DAM OKD file path')
    parser.add_argument(
        "output_path", help='Output directory path')
    args = parser.parse_args()

    with open(args.input_path, 'rb') as input_file:
        chunks_stream = io.BytesIO()
        okd_header = OkdFile.decrypt(
            input_file, chunks_stream, OkdFileType.OKD)
        print(f'Header found. header={okd_header}')
        chunks_stream.seek(0)

        chunk_index = OkdFile.index_chunk(chunks_stream)
        chunks_stream.seek(0)
        for chunk_position, chunk_size in chunk_index:
            chunks_stream.seek(chunk_position)
            chunk_buffer = chunks_stream.read(chunk_size)

            generic_chunk = OkdFile.parse_generic_chunk(chunk_buffer)
            output_path = os.path.join(
                args.output_path, 'chunk_0x' + generic_chunk.chunk_id.hex() + '.bin')
            with open(output_path, 'wb') as output_file:
                output_file.write(generic_chunk.data)

            chunk = OkdFile.parse_chunk(chunk_buffer)
            print(f'{type(chunk).__name__} found. chunk_id={generic_chunk.chunk_id}, chunk_id_hex={generic_chunk.chunk_id.hex()}')

            if isinstance(chunk, OkdPTrackChunk):
                output_path = os.path.join(
                    args.output_path, 'p_track_' + str(chunk_buffer[3]) + '.mid')
                midi = chunk.to_midi()
                midi.save(output_path)
            elif isinstance(chunk, OkdAdpcmChunk):
                for index, adpcm in enumerate(chunk.adpcms):
                    output_path = os.path.join(
                        args.output_path, 'adpcm_' + str(index) + '.bin')
                    with open(output_path, 'wb') as output_file:
                        output_file.write(adpcm)


if __name__ == "__main__":
    main()
