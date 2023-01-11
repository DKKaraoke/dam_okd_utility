import bitstring
from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger

class OkdAdpcmChunk(NamedTuple):
    """DAM OKD ADPCM Chunk
    """

    __logger = getLogger('OkdAdpcmChunk')

    @staticmethod
    def read(stream: bitstring.BitStream):
        adpcms: list[bytes] = []
        while True:
            chunk_header_buffer = stream.read(8)
            if len(chunk_header_buffer) < 8:
                break
            chunk_id = chunk_header_buffer[0:4]
            if chunk_id != b'YAWV':
                raise RuntimeError('Invalid chunk_id.')
            chunk_size = int.from_bytes(
                chunk_header_buffer[4:8], byteorder='big')
            chunk_data = stream.read(chunk_size)
            if len(chunk_data) < chunk_size:
                raise RuntimeError('Invalid chunk_data length.')
            adpcms.append(chunk_data)

        return OkdAdpcmChunk(adpcms)

    adpcms: list[bytes]
