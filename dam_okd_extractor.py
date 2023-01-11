#!/usr/bin/env python
# coding: utf-8

import argparse
import io
import os

from dam_okd_utility.okd_file import OkdFile, OkdFileType
from dam_okd_utility.okd_file_data import OkdGenericChunk
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
        header = input_file.read(4)
        if header == b'SPRC':
            input_file.seek(16)
        else:
            input_file.seek(0)

        chunks_stream = io.BytesIO()
        okd_header = OkdFile.decrypt(
            input_file, chunks_stream, OkdFileType.OKD)
        print(okd_header)
        chunks_stream.seek(0)

        chunk_index = OkdFile.index_chunk(chunks_stream)
        chunks_stream.seek(0)
        for chunk_position, chunk_size in chunk_index:
            chunks_stream.seek(chunk_position)
            chunk_buffer = chunks_stream.read(chunk_size)
            chunk = OkdFile.read_chunk(chunk_buffer)
            if isinstance(chunk, OkdGenericChunk):
                print(f'Unknown chunk found. chunk_id={chunk.id}')
                output_path = os.path.join(args.output_path, 'chunk_' + chunk.id.hex() + '.bin')
                with open(output_path, 'wb') as output_file:
                    output_file.write(chunk.data)
            elif isinstance(chunk, OkdAdpcmChunk):
                for index, adpcm in enumerate(chunk.adpcms):
                    output_path = os.path.join(args.output_path, 'adpcm_' + str(index) + '.bin')
                    with open(output_path, 'wb') as output_file:
                        output_file.write(adpcm)
            else:
                print(chunk)


if __name__ == "__main__":
    main()
