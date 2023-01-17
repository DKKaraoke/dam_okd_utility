import bitstring
from enum import Enum, auto
import io
import os

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.okd_encryption_key_table import OKD_ENCRYPTION_KEY_TABLE
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
from dam_okd_utility.okd_m_track_chunk import OkdMTrackChunk
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
                    candidated_key = OKD_ENCRYPTION_KEY_TABLE[encryption_key_index + 1]
                candidated_key |= OKD_ENCRYPTION_KEY_TABLE[encryption_key_index] << 16
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
                encryption_key = OKD_ENCRYPTION_KEY_TABLE[encryption_key_index % 0x100]
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
        elif chunk_id == b"YP3I":
            return OkdPTrackInfoChunk.read(chunk_data_stream, False)
        elif chunk_id == b"YPXI":
            return OkdExtendedPTrackInfoChunk.read(chunk_data_stream)
        elif chunk_id[0:3] == b"\xffMR":
            return OkdMTrackChunk.read(chunk_data_stream)
        elif chunk_id[0:3] == b"\xffPR":
            return OkdPTrackChunk.read(chunk_data_stream)
        elif chunk_id == b"YADD":
            return OkdAdpcmChunk.read(chunk_data_stream)

        return OkdGenericChunk(chunk_id, chunk_data)
