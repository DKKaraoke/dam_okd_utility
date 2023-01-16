import bitstring
from enum import Enum, auto
import io
import os

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.okd_file_data import (
    GenericOkdHeader,
    MmtOkdHeader,
    MmkOkdHeader,
    SprOkdHeader,
    DioOkdHeader,
    OkdHeader,
    OkaHeader,
    OkdGenericChunk,
)
from dam_okd_utility.okd_adpcm_chunk import OkdAdpcmChunk
from dam_okd_utility.okd_p_track_chunk import OkdPTrackChunk
from dam_okd_utility.okd_p_track_info_chunk import OkdPTrackInfoChunk
from dam_okd_utility.okd_extended_p_track_info_chunk import OkdExtendedPTrackInfoChunk


class OkdFileType(Enum):
    OKD = auto()
    P3 = auto()
    M3 = auto()
    DIFF = auto()
    ONTA = auto()
    MP3DIFF = auto()
    ONTADIFF = auto()
    MP3RAWDATA = auto()
    MMTTXT = auto()
    FILES = auto()


class OkdFileReadMode(Enum):
    MMT = auto()
    YKS = auto()
    ALL = auto()
    DATA = auto()


class OkdFile:
    """DAM OKD File"""

    __ENCRYPTION_KEY_TABLE = [
        0x87D2,
        0xEBBE,
        0xE2FC,
        0xDB17,
        0xE1A8,
        0x63BE,
        0x661E,
        0xF2F2,
        0x33EF,
        0x2E82,
        0x7A1E,
        0xAF30,
        0xD7CB,
        0xF9A1,
        0x0358,
        0x9DBF,
        0xBC0E,
        0x64A0,
        0xAE4D,
        0x74F3,
        0x722E,
        0xD5E5,
        0xCCAB,
        0xB88A,
        0x5B4B,
        0xEFC3,
        0xD244,
        0xFEA9,
        0x752B,
        0xA573,
        0x7214,
        0xD4DE,
        0xC73E,
        0xF016,
        0x5B3D,
        0xC51E,
        0x6F9C,
        0x23B6,
        0x960B,
        0xFAC5,
        0xD003,
        0x6443,
        0x80F1,
        0x079B,
        0xDADB,
        0xBA97,
        0x6D8B,
        0xC8CA,
        0x0034,
        0xC973,
        0x5D9B,
        0x6BE9,
        0x3AC3,
        0xA280,
        0xE00D,
        0x93F5,
        0x3CE9,
        0xBB50,
        0x8DF5,
        0x1E54,
        0xBDAC,
        0x825C,
        0x278D,
        0x87D1,
        0x65BD,
        0x9405,
        0x5138,
        0xF1A3,
        0xDC72,
        0x0F95,
        0xF082,
        0x4668,
        0xF4CA,
        0x8C3B,
        0xA91F,
        0xFF23,
        0x7A6E,
        0xAE13,
        0x79E9,
        0x0844,
        0x9EAB,
        0x5B1D,
        0xF9E3,
        0xC69D,
        0x857A,
        0x9042,
        0x353A,
        0xBC6E,
        0x7279,
        0x5654,
        0x2A40,
        0xCE5B,
        0x95F0,
        0xD70B,
        0x6670,
        0xA872,
        0xF9CE,
        0x920A,
        0x436E,
        0x4327,
        0x0EAB,
        0xB1D9,
        0xC404,
        0x8858,
        0xD8C4,
        0x80EA,
        0x9127,
        0x184B,
        0xBD03,
        0xFE95,
        0x16F2,
        0x2EAC,
        0x6DF6,
        0x141E,
        0xC1A6,
        0x2791,
        0xF8D3,
        0x69AA,
        0xDAB1,
        0x2476,
        0x727C,
        0x5B4E,
        0x85A5,
        0x5142,
        0xC476,
        0x8E01,
        0x5D3E,
        0xC941,
        0x99F2,
        0x24A6,
        0x305E,
        0x1C2A,
        0xECC5,
        0x1505,
        0xDF10,
        0x7317,
        0x3271,
        0x9CCF,
        0x578A,
        0xD590,
        0x291B,
        0x569F,
        0xB324,
        0x8E82,
        0xC492,
        0xEEF4,
        0x7364,
        0x3142,
        0x3B50,
        0xF938,
        0xDEF2,
        0x3E8D,
        0xB372,
        0x64BE,
        0x7EA5,
        0x6987,
        0x8FBF,
        0x91BD,
        0xBA76,
        0x7CBF,
        0x5CA8,
        0x0658,
        0x1689,
        0x5F2A,
        0xDD43,
        0x4397,
        0x1028,
        0x3925,
        0x3850,
        0xBA6B,
        0x9AC7,
        0xB975,
        0x4535,
        0x60AE,
        0x3D02,
        0xFA47,
        0x7902,
        0xE621,
        0x4D9C,
        0x8632,
        0xF36E,
        0x896E,
        0x507F,
        0x7D31,
        0x2BDA,
        0x8D25,
        0x73C0,
        0x59AB,
        0x3E4B,
        0xCCC0,
        0x2C99,
        0xD56B,
        0x5871,
        0xF1A0,
        0xF46D,
        0x6EA9,
        0x46A3,
        0x480F,
        0xA5C9,
        0x8D01,
        0xA0E1,
        0xB43D,
        0x795F,
        0x4678,
        0x97D1,
        0xC744,
        0x230A,
        0xC47B,
        0x61C4,
        0x7425,
        0x0ECE,
        0xC8E0,
        0x47B0,
        0x64CA,
        0xBDD5,
        0xD2E4,
        0xD234,
        0xEF02,
        0x4375,
        0xE42C,
        0x1699,
        0x298A,
        0x6226,
        0xE5C6,
        0x23CC,
        0x2100,
        0xC88D,
        0x2D27,
        0x0F66,
        0x2CEE,
        0x6E75,
        0x212C,
        0x22A5,
        0x64C6,
        0x91D1,
        0xFF19,
        0x2771,
        0x34E1,
        0xD3BC,
        0xBF9D,
        0xD558,
        0x937F,
        0x757B,
        0x1BCE,
        0x5E94,
        0x55CC,
        0xB577,
        0xB226,
        0x1D02,
        0x24D7,
        0xCC44,
        0xCB8D,
        0x5F29,
        0x9299,
        0x899E,
        0xC050,
    ]

    __logger = getLogger("OkdFile")

    @staticmethod
    def __detect_first_encryption_key_index(
        stream: io.BufferedReader, file_type: OkdFileType
    ):
        expected_magic_bytes: bytes
        if (
            file_type == OkdFileType.OKD
            or file_type == OkdFileType.P3
            or file_type == OkdFileType.DIFF
            or file_type == OkdFileType.MP3DIFF
            or file_type == OkdFileType.MMTTXT
        ):
            expected_magic_bytes = b"YKS1"
        elif (
            file_type == OkdFileType.M3
            or file_type == OkdFileType.ONTA
            or file_type == OkdFileType.ONTADIFF
        ):
            expected_magic_bytes = b"YOKA"
        else:
            raise RuntimeError(f"Invalid file_type. file_type={file_type}")
        expected_magic_bytes_int = int.from_bytes(expected_magic_bytes, byteorder="big")

        magic_bytes_buffer = stream.read(4)
        if len(magic_bytes_buffer) != 4:
            raise RuntimeError("Invalid magic_bytes_int_buffer length.")
        stream.seek(-4, os.SEEK_CUR)
        magic_bytes_int = int.from_bytes(magic_bytes_buffer, byteorder="big")
        if magic_bytes_int != expected_magic_bytes_int:
            OkdFile.__logger.info("OKD file is encrypted.")
            expected_key = magic_bytes_int ^ expected_magic_bytes_int
            for encryption_key_index in range(0x100):
                candidated_key: int
                if encryption_key_index == 0xFF:
                    candidated_key = 0x87D2
                else:
                    candidated_key = OkdFile.__ENCRYPTION_KEY_TABLE[
                        encryption_key_index + 1
                    ]
                candidated_key |= (
                    OkdFile.__ENCRYPTION_KEY_TABLE[encryption_key_index] << 16
                )
                if expected_key == candidated_key:
                    OkdFile.__logger.info(
                        f"OKD file encryption_key_index detected. encryption_key_index={encryption_key_index}"
                    )
                    return encryption_key_index
            raise RuntimeError("Failed to detect OKD file encryption_key_index.")

    @staticmethod
    def __decrypt(
        input_stream: io.BufferedReader,
        output_stream: io.BufferedWriter,
        encryption_key_index: int | None,
        length: int | None = None,
    ):
        start_position = input_stream.tell()
        while length is None or (
            length is not None and (input_stream.tell() - start_position) < length
        ):
            ciphertext_buffer = input_stream.read(2)
            if len(ciphertext_buffer) != 2:
                # return
                raise RuntimeError("Invalid ciphertext_buffer length.")
            ciphertext = int.from_bytes(ciphertext_buffer, byteorder="big")
            encryption_key: int
            if encryption_key_index is None:
                encryption_key = 0x17D7
            else:
                encryption_key = OkdFile.__ENCRYPTION_KEY_TABLE[
                    encryption_key_index % 0x100
                ]
            plaintext = ciphertext ^ encryption_key
            plaintext_buffer = plaintext.to_bytes(2, byteorder="big")
            output_stream.write(plaintext_buffer)
            if encryption_key_index is not None:
                encryption_key_index += 1
        return encryption_key_index

    @staticmethod
    def __read_okd_header(stream: io.BufferedReader, encryption_key_index: int):
        plaintext_stream = io.BytesIO()
        encryption_key_index = OkdFile.__decrypt(
            stream, plaintext_stream, encryption_key_index, 40
        )
        plaintext_stream.seek(0)

        header_buffer = plaintext_stream.read(40)
        if len(header_buffer) != 40:
            raise RuntimeError("Incalid header_buffer length.")

        magic_bytes = header_buffer[0:4]
        if magic_bytes != b"YKS1":
            raise RuntimeError("Invalid magic_bytes.")
        length = int.from_bytes(header_buffer[4:8], byteorder="big")
        version = str(header_buffer[8:24])
        id_karaoke = int.from_bytes(header_buffer[24:28], byteorder="big")
        adpcm_offset = int.from_bytes(header_buffer[28:32], byteorder="big")
        encryption_mode = int.from_bytes(header_buffer[32:36], byteorder="big")
        option_data_length: int = int.from_bytes(header_buffer[36:40], byteorder="big")

        encryption_key_index = OkdFile.__decrypt(
            stream, plaintext_stream, encryption_key_index, option_data_length
        )
        plaintext_stream.seek(40)
        option_data_buffer = plaintext_stream.read(option_data_length)
        if len(option_data_buffer) != option_data_length:
            raise RuntimeError("Invalid option_data_buffer length.")

        if option_data_length != 0:
            if option_data_length == 12:
                yks_chunk_length = int.from_bytes(
                    option_data_buffer[0:4], byteorder="big"
                )
                mmt_chunk_length = int.from_bytes(
                    option_data_buffer[4:8], byteorder="big"
                )
                crc_yks_loader = int.from_bytes(
                    option_data_buffer[8:10], byteorder="big"
                )
                crc_loader = int.from_bytes(option_data_buffer[10:12], byteorder="big")
                return MmtOkdHeader(
                    magic_bytes,
                    length,
                    version,
                    id_karaoke,
                    adpcm_offset,
                    encryption_mode,
                    yks_chunk_length,
                    mmt_chunk_length,
                    crc_yks_loader,
                    crc_loader,
                )
            elif option_data_length == 20:
                yks_chunk_length = int.from_bytes(
                    option_data_buffer[0:4], byteorder="big"
                )
                mmt_chunk_length = int.from_bytes(
                    option_data_buffer[4:8], byteorder="big"
                )
                mmk_chunk_length = int.from_bytes(
                    option_data_buffer[8:12], byteorder="big"
                )
                crc_yks_loader = int.from_bytes(
                    option_data_buffer[12:14], byteorder="big"
                )
                crc_yks_mmk_okd = int.from_bytes(
                    option_data_buffer[14:16], byteorder="big"
                )
                crc_loader = int.from_bytes(option_data_buffer[16:18], byteorder="big")
                return MmkOkdHeader(
                    magic_bytes,
                    length,
                    version,
                    id_karaoke,
                    adpcm_offset,
                    encryption_mode,
                    yks_chunk_length,
                    mmt_chunk_length,
                    mmk_chunk_length,
                    crc_yks_loader,
                    crc_yks_mmk_okd,
                    crc_loader,
                )
            elif option_data_length == 24:
                yks_chunk_length = int.from_bytes(
                    option_data_buffer[0:4], byteorder="big"
                )
                mmt_chunk_length = int.from_bytes(
                    option_data_buffer[4:8], byteorder="big"
                )
                mmk_chunk_length = int.from_bytes(
                    option_data_buffer[8:12], byteorder="big"
                )
                spr_chunk_length = int.from_bytes(
                    option_data_buffer[12:16], byteorder="big"
                )
                crc_yks_loader = int.from_bytes(
                    option_data_buffer[16:18], byteorder="big"
                )
                crc_yks_mmt_okd = int.from_bytes(
                    option_data_buffer[18:20], byteorder="big"
                )
                crc_yks_mmt_mmk_okd = int.from_bytes(
                    option_data_buffer[20:22], byteorder="big"
                )
                crc_loader = int.from_bytes(option_data_buffer[22:24], byteorder="big")
                return SprOkdHeader(
                    magic_bytes,
                    length,
                    version,
                    id_karaoke,
                    adpcm_offset,
                    encryption_mode,
                    yks_chunk_length,
                    mmt_chunk_length,
                    mmk_chunk_length,
                    spr_chunk_length,
                    crc_yks_loader,
                    crc_yks_mmt_okd,
                    crc_yks_mmt_mmk_okd,
                )
            elif option_data_length == 32:
                yks_chunk_length = int.from_bytes(
                    option_data_buffer[0:4], byteorder="big"
                )
                mmt_chunk_length = int.from_bytes(
                    option_data_buffer[4:8], byteorder="big"
                )
                mmk_chunk_length = int.from_bytes(
                    option_data_buffer[8:12], byteorder="big"
                )
                spr_chunk_length = int.from_bytes(
                    option_data_buffer[12:16], byteorder="big"
                )
                dio_chunk_length = int.from_bytes(
                    option_data_buffer[16:20], byteorder="big"
                )
                crc_yks_loader = int.from_bytes(
                    option_data_buffer[20:22], byteorder="big"
                )
                crc_yks_mmk_okd = int.from_bytes(
                    option_data_buffer[22:24], byteorder="big"
                )
                crc_yks_mmt_mmk_okd = int.from_bytes(
                    option_data_buffer[24:26], byteorder="big"
                )
                crc_yks_mmt_mmk_spr_okd = int.from_bytes(
                    option_data_buffer[26:28], byteorder="big"
                )
                crc_loader = int.from_bytes(option_data_buffer[28:30], byteorder="big")
                return DioOkdHeader(
                    magic_bytes,
                    length,
                    version,
                    id_karaoke,
                    adpcm_offset,
                    encryption_mode,
                    yks_chunk_length,
                    mmt_chunk_length,
                    mmk_chunk_length,
                    spr_chunk_length,
                    dio_chunk_length,
                    crc_yks_loader,
                    crc_yks_mmt_okd,
                    crc_yks_mmt_mmk_okd,
                    crc_yks_mmt_mmk_spr_okd,
                    crc_loader,
                )

        return GenericOkdHeader(
            magic_bytes,
            length,
            version,
            id_karaoke,
            adpcm_offset,
            encryption_mode,
            option_data_buffer,
        )

    @staticmethod
    def __validate_okd_header(data: OkdHeader, file_type: OkdFileType):
        if data.encryption_mode != 0x000000:
            OkdFile.__logger.info(
                f"Invalid encryption_mode. encryption_mode={data.encryption_mode}"
            )
            return False
        if (
            file_type == OkdFileType.OKD
            or file_type == OkdFileType.P3
            or file_type == OkdFileType.DIFF
            or file_type == OkdFileType.MP3DIFF
            or file_type == OkdFileType.MMTTXT
        ):
            if data.magic_bytes != b"YKS1":
                OkdFile.__logger.info(
                    f"Invalid magic_bytes. magic_bytes={data.magic_bytes}"
                )
                return False
            version_prefix = data.version[0:8]
            if version_prefix != "YKS-1    " and (
                file_type == OkdFileType.P3 and version_prefix != "YKS-2    "
            ):
                OkdFile.__logger.info(
                    f"Invalid version_prefix. version_prefix={version_prefix}"
                )
                return False
        elif (
            file_type == OkdFileType.M3
            or file_type == OkdFileType.ONTA
            or file_type == OkdFileType.ONTADIFF
        ):
            if data.magic_bytes != b"YOKA":
                OkdFile.__logger.info(
                    f"Invalid magic_bytes. magic_bytes={data.magic_bytes}"
                )
                return False
        else:
            raise RuntimeError(f"Invalid file_type. file_type={file_type}")
        return True

    @staticmethod
    def __read_oka_header(stream: io.BufferedReader, encryption_key_index: int):
        plaintext_stream = io.BytesIO()
        encryption_key_index = OkdFile.__decrypt(
            stream, plaintext_stream, encryption_key_index, 40
        )
        plaintext_stream.seek(0)

        header_buffer = plaintext_stream.read(40)
        if len(header_buffer) != 40:
            raise RuntimeError("Incalid header_buffer length.")

        magic_bytes = header_buffer[0:4]
        if magic_bytes != b"YOKA":
            raise RuntimeError("Invalid magic_bytes.")
        length = int.from_bytes(header_buffer[4:8], byteorder="big")
        version = str(header_buffer[8:24])
        id_karaoke = int.from_bytes(header_buffer[24:28], byteorder="big")
        data_offset = int.from_bytes(header_buffer[28:32], byteorder="big")
        reserved = int.from_bytes(header_buffer[32:36], byteorder="big")
        crc_loader: int = int.from_bytes(header_buffer[36:40], byteorder="big")

        return OkaHeader(
            magic_bytes, length, version, id_karaoke, data_offset, reserved, crc_loader
        )

    @staticmethod
    def __read_file_header(
        stream: io.BufferedReader, file_type: OkdFileType, encryption_key_index: int
    ):
        if (
            file_type == OkdFileType.OKD
            or file_type == OkdFileType.P3
            or file_type == OkdFileType.DIFF
            or file_type == OkdFileType.MP3DIFF
            or file_type == OkdFileType.MMTTXT
        ):
            return OkdFile.__read_okd_header(stream, encryption_key_index)
        elif (
            file_type == OkdFileType.M3
            or file_type == OkdFileType.ONTA
            or file_type == OkdFileType.ONTADIFF
        ):
            return OkdFile.__read_oka_header(stream, encryption_key_index)
        else:
            raise RuntimeError(f"Invalid file_type. file_type={file_type}")

    @staticmethod
    def __peek_chunk_header(stream: io.BufferedReader):
        while True:
            chunk_header_buffer = stream.read(8)
            chunk_header_length = len(chunk_header_buffer)
            if chunk_header_length < 8:
                stream.seek(-chunk_header_length, os.SEEK_CUR)
                return
            chunk_id = chunk_header_buffer[0:4]
            chunk_size = int.from_bytes(chunk_header_buffer[4:8], byteorder="big")
            stream.seek(-8, os.SEEK_CUR)
            return (chunk_id, chunk_size)

    @staticmethod
    def __seek_chunk_header(stream: io.BufferedReader, chunk_id: bytes | None = None):
        while True:
            chunk_header = OkdFile.__peek_chunk_header(stream)
            if chunk_header is None:
                return
            current_chunk_id, current_chunk_size = chunk_header
            if chunk_id is None:
                return (current_chunk_id, current_chunk_size)
            else:
                if current_chunk_id == chunk_id:
                    return (current_chunk_id, current_chunk_size)
            stream.seek(8 + current_chunk_size, os.SEEK_CUR)

    @staticmethod
    def decrypt(
        input_stream: io.BufferedReader,
        chunks_stream: io.BufferedWriter,
        file_type: OkdFileType,
    ):
        # Detect and skip SPR header
        spr_header_buffer = input_stream.read(4)
        if spr_header_buffer == b"SPRC":
            OkdFile.__logger.info("SPR hedaer detected.")
            input_stream.seek(16)
        else:
            input_stream.seek(0)

        start_position = input_stream.tell()

        encryption_key_index = OkdFile.__detect_first_encryption_key_index(
            input_stream, file_type
        )
        header = OkdFile.__read_file_header(
            input_stream, file_type, encryption_key_index
        )

        data_offset = input_stream.tell() - start_position
        data_length = header.length - data_offset

        extended_data_offset: int
        if isinstance(header, OkdHeader):
            extended_data_offset = header.adpcm_offset
        elif isinstance(header, OkaHeader):
            extended_data_offset = header.data_offset
        else:
            raise RuntimeError("Unknown header detected.")
        if extended_data_offset != 0:
            extended_data_offset -= 40

        extended_data_length: int
        if header.adpcm_offset == 0:
            extended_data_length = 0
        else:
            extended_data_length = data_length - extended_data_offset

        encrypted_length = data_length - extended_data_length

        # Decrypt
        OkdFile.__decrypt(
            input_stream, chunks_stream, encryption_key_index, encrypted_length
        )
        # Copy extended data
        chunks_stream.write(input_stream.read())

        return header

    @staticmethod
    def index_chunk(stream: io.BufferedReader):
        index: list[tuple[int, int]] = []

        last_position = -1
        while True:
            chunk_header = OkdFile.__seek_chunk_header(stream)
            if chunk_header is None:
                break
            chunk_id, chunk_size = chunk_header
            position = stream.tell()
            if last_position != -1:
                index.append((last_position, position - last_position))
            last_position = position
            stream.seek(8 + chunk_size, os.SEEK_CUR)

        if last_position != -1:
            position = stream.tell()
            index.append((last_position, position - last_position))

        return index

    @staticmethod
    def parse_generic_chunk(buffer: bytes):
        if len(buffer) < 8:
            raise RuntimeError("Invalid buffer length.")

        chunk_id = buffer[0:4]
        chunk_size = int.from_bytes(buffer[4:8], byteorder="big")
        chunk_data = buffer[8:]
        if len(chunk_data) != chunk_size:
            raise RuntimeError("Invalid chunk_data length.")

        return OkdGenericChunk(chunk_id, chunk_data)

    @staticmethod
    def parse_chunk(buffer: bytes):
        if len(buffer) < 8:
            raise RuntimeError("Invalid buffer length.")

        chunk_id = buffer[0:4]
        chunk_size = int.from_bytes(buffer[4:8], byteorder="big")
        chunk_data = buffer[8:]
        if len(chunk_data) != chunk_size:
            raise RuntimeError("Invalid chunk_data length.")
        chunk_data_stream = bitstring.BitStream(chunk_data)

        if chunk_id == b"YPTI":
            return OkdPTrackInfoChunk.read(chunk_data_stream)
        elif chunk_id == b"YPXI":
            return OkdExtendedPTrackInfoChunk.read(chunk_data_stream)
        elif chunk_id[0:3] == b"\xffPR":
            return OkdPTrackChunk.read(chunk_data_stream)
        elif chunk_id == b"YADD":
            return OkdAdpcmChunk.read(chunk_data_stream)

        return OkdGenericChunk(chunk_id, chunk_data)
