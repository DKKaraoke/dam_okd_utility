import bitstring
from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger


class OkdAdpcmChunk(NamedTuple):
    """DAM OKD ADPCM Chunk"""

    __logger = getLogger("OkdAdpcmChunk")

    @staticmethod
    def read(stream: bitstring.BitStream):
        adpcms: list[bytes] = []
        while True:
            chunk_id: bytes
            try:
                chunk_id = stream.read("bytes:4")
            except bitstring.ReadError:
                break

            if chunk_id == b"YAWV":
                chunk_size: int = stream.read("uintbe:32")
                chunk_data: bytes = stream.read(8 * chunk_size).bytes
                adpcms.append(chunk_data)
            else:
                chunk_data: bytes = stream.read("bytes")
                adpcms.append(chunk_data)

        return OkdAdpcmChunk(adpcms)

    def write(self, stream: bitstring.BitStream):
        for adpcm in self.adpcms:
            stream.append(bitstring.pack("uintbe:32", len(adpcm)))
            stream.append(adpcm)

    adpcms: list[bytes]
