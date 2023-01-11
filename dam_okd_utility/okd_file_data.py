from typing import NamedTuple, Union


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


OkdHeader = Union[GenericOkdHeader, MmtOkdHeader,
                  MmkOkdHeader, SprOkdHeader, DioOkdHeader]


class OkaHeader(NamedTuple):
    magic_bytes: bytes
    length: int
    version: str
    id_karaoke: int
    data_offset: int
    reserved: int
    crc_loader: int


class OkdGenericChunk(NamedTuple):
    chunk_id: bytes
    data: bytes
