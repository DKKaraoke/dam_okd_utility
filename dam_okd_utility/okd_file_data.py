import bitstring
from typing import NamedTuple, Union


from dam_okd_utility.okd_p_track_info_chunk import OkdPTrackInfoChunk
from dam_okd_utility.okd_extended_p_track_info_chunk import OkdExtendedPTrackInfoChunk
from dam_okd_utility.okd_p3_track_info_chunk import OkdP3TrackInfoChunk
from dam_okd_utility.okd_m_track_chunk import OkdMTrackChunk
from dam_okd_utility.okd_p_track_chunk import OkdPTrackChunk
from dam_okd_utility.okd_adpcm_chunk import OkdAdpcmChunk


class GenericOkdHeader(NamedTuple):
    magic_bytes: bytes
    length: int
    version: str
    id_karaoke: int
    adpcm_offset: int
    encryption_mode: int
    option_data: bytes


class MmtOkdHeader(NamedTuple):
    magic_bytes: bytes
    length: int
    version: str
    id_karaoke: int
    adpcm_offset: int
    encryption_mode: int
    # option_data
    yks_chunks_length: int
    mmt_chunks_length: int
    crc_yks_loader: int
    crc_loader: int


class MmkOkdHeader(NamedTuple):
    magic_bytes: bytes
    length: int
    version: str
    id_karaoke: int
    adpcm_offset: int
    encryption_mode: int
    # option_data
    yks_chunks_length: int
    mmt_chunks_length: int
    mmk_chunks_length: int
    crc_yks_loader: int
    crc_yks_mmk_okd: int
    crc_loader: int


class SprOkdHeader(NamedTuple):
    magic_bytes: bytes
    length: int
    version: str
    id_karaoke: int
    adpcm_offset: int
    encryption_mode: int
    # option_data
    yks_chunks_length: int
    mmt_chunks_length: int
    mmk_chunks_length: int
    spr_chunks_length: int
    crc_yks_loader: int
    crc_yks_mmt_okd: int
    crc_yks_mmt_mmk_okd: int
    crc_loader: int


class DioOkdHeader(NamedTuple):
    magic_bytes: bytes
    length: int
    version: str
    id_karaoke: int
    adpcm_offset: int
    encryption_mode: int
    # option_data
    yks_chunks_length: int
    mmt_chunks_length: int
    mmk_chunks_length: int
    spr_chunks_length: int
    dio_chunks_length: int
    crc_yks_loader: int
    crc_yks_mmt_okd: int
    crc_yks_mmt_mmk_okd: int
    crc_yks_mmt_mmk_spr_okd: int
    crc_loader: int


OkdHeader = Union[
    GenericOkdHeader, MmtOkdHeader, MmkOkdHeader, SprOkdHeader, DioOkdHeader
]


class OkaHeader(NamedTuple):
    magic_bytes: bytes
    length: int
    version: str
    id_karaoke: int
    data_offset: int
    reserved: int
    crc_loader: int


class OkdGenericChunk(NamedTuple):
    def write(self, stream: bitstring.BitStream):
        stream.append(self.data)

    chunk_id: bytes
    data: bytes


OkdChunk = Union[
    OkdGenericChunk,
    OkdPTrackInfoChunk,
    OkdExtendedPTrackInfoChunk,
    OkdP3TrackInfoChunk,
    OkdMTrackChunk,
    OkdPTrackChunk,
    OkdAdpcmChunk,
]
