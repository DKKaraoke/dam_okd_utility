from enum import Enum, auto
import io
import os

from dam_okd_utility.customized_logger import getLogger
from dam_okd_utility.okd_file_data import GenericOkdHeader, MmtOkdHeader, MmkOkdHeader, SprOkdHeader, DioOkdHeader, OkdHeader, OkaHeader, OkdGenericChunk
from dam_okd_utility.okd_adpcm_chunk import OkdAdpcmChunk
from dam_okd_utility.okd_p_track_info_chunk import OkdPTrackInfoChunk


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
    """DAM OKD File
    """

    __ENCRYPTION_KEY_TABLE = [0x87d2, 0xebbe, 0xe2fc, 0xdb17, 0xe1a8, 0x63be, 0x661e, 0xf2f2,
                              0x33ef, 0x2e82, 0x7a1e, 0xaf30, 0xd7cb, 0xf9a1, 0x0358, 0x9dbf,
                              0xbc0e, 0x64a0, 0xae4d, 0x74f3, 0x722e, 0xd5e5, 0xccab, 0xb88a,
                              0x5b4b, 0xefc3, 0xd244, 0xfea9, 0x752b, 0xa573, 0x7214, 0xd4de,
                              0xc73e, 0xf016, 0x5b3d, 0xc51e, 0x6f9c, 0x23b6, 0x960b, 0xfac5,
                              0xd003, 0x6443, 0x80f1, 0x079b, 0xdadb, 0xba97, 0x6d8b, 0xc8ca,
                              0x0034, 0xc973, 0x5d9b, 0x6be9, 0x3ac3, 0xa280, 0xe00d, 0x93f5,
                              0x3ce9, 0xbb50, 0x8df5, 0x1e54, 0xbdac, 0x825c, 0x278d, 0x87d1,
                              0x65bd, 0x9405, 0x5138, 0xf1a3, 0xdc72, 0x0f95, 0xf082, 0x4668,
                              0xf4ca, 0x8c3b, 0xa91f, 0xff23, 0x7a6e, 0xae13, 0x79e9, 0x0844,
                              0x9eab, 0x5b1d, 0xf9e3, 0xc69d, 0x857a, 0x9042, 0x353a, 0xbc6e,
                              0x7279, 0x5654, 0x2a40, 0xce5b, 0x95f0, 0xd70b, 0x6670, 0xa872,
                              0xf9ce, 0x920a, 0x436e, 0x4327, 0x0eab, 0xb1d9, 0xc404, 0x8858,
                              0xd8c4, 0x80ea, 0x9127, 0x184b, 0xbd03, 0xfe95, 0x16f2, 0x2eac,
                              0x6df6, 0x141e, 0xc1a6, 0x2791, 0xf8d3, 0x69aa, 0xdab1, 0x2476,
                              0x727c, 0x5b4e, 0x85a5, 0x5142, 0xc476, 0x8e01, 0x5d3e, 0xc941,
                              0x99f2, 0x24a6, 0x305e, 0x1c2a, 0xecc5, 0x1505, 0xdf10, 0x7317,
                              0x3271, 0x9ccf, 0x578a, 0xd590, 0x291b, 0x569f, 0xb324, 0x8e82,
                              0xc492, 0xeef4, 0x7364, 0x3142, 0x3b50, 0xf938, 0xdef2, 0x3e8d,
                              0xb372, 0x64be, 0x7ea5, 0x6987, 0x8fbf, 0x91bd, 0xba76, 0x7cbf,
                              0x5ca8, 0x0658, 0x1689, 0x5f2a, 0xdd43, 0x4397, 0x1028, 0x3925,
                              0x3850, 0xba6b, 0x9ac7, 0xb975, 0x4535, 0x60ae, 0x3d02, 0xfa47,
                              0x7902, 0xe621, 0x4d9c, 0x8632, 0xf36e, 0x896e, 0x507f, 0x7d31,
                              0x2bda, 0x8d25, 0x73c0, 0x59ab, 0x3e4b, 0xccc0, 0x2c99, 0xd56b,
                              0x5871, 0xf1a0, 0xf46d, 0x6ea9, 0x46a3, 0x480f, 0xa5c9, 0x8d01,
                              0xa0e1, 0xb43d, 0x795f, 0x4678, 0x97d1, 0xc744, 0x230a, 0xc47b,
                              0x61c4, 0x7425, 0x0ece, 0xc8e0, 0x47b0, 0x64ca, 0xbdd5, 0xd2e4,
                              0xd234, 0xef02, 0x4375, 0xe42c, 0x1699, 0x298a, 0x6226, 0xe5c6,
                              0x23cc, 0x2100, 0xc88d, 0x2d27, 0x0f66, 0x2cee, 0x6e75, 0x212c,
                              0x22a5, 0x64c6, 0x91d1, 0xff19, 0x2771, 0x34e1, 0xd3bc, 0xbf9d,
                              0xd558, 0x937f, 0x757b, 0x1bce, 0x5e94, 0x55cc, 0xb577, 0xb226,
                              0x1d02, 0x24d7, 0xcc44, 0xcb8d, 0x5f29, 0x9299, 0x899e, 0xc059]

    __logger = getLogger('OkdFile')

    @staticmethod
    def __detect_first_encryption_key_index(stream: io.BufferedReader, file_type: OkdFileType):
        expected_magic_bytes: bytes
        if file_type == OkdFileType.OKD or file_type == OkdFileType.P3 or file_type == OkdFileType.DIFF or file_type == OkdFileType.MP3DIFF or file_type == OkdFileType.MMTTXT:
            expected_magic_bytes = b'YKS1'
        elif file_type == OkdFileType.M3 or file_type == OkdFileType.ONTA or file_type == OkdFileType.ONTADIFF:
            expected_magic_bytes = b'YOKA'
        else:
            raise RuntimeError(f'Invalid file_type. file_type={file_type}')
        expected_magic_bytes_int = int.from_bytes(
            expected_magic_bytes, byteorder='big')

        magic_bytes_buffer = stream.read(4)
        if len(magic_bytes_buffer) != 4:
            raise RuntimeError('Invalid magic_bytes_int_buffer length.')
        stream.seek(-4, os.SEEK_CUR)
        magic_bytes_int = int.from_bytes(magic_bytes_buffer, byteorder='big')
        if magic_bytes_int != expected_magic_bytes_int:
            OkdFile.__logger.info('OKD file is encrypted.')
            expected_key = magic_bytes_int ^ expected_magic_bytes_int
            for encryption_key_index in range(0x100):
                candidated_key: int
                if encryption_key_index == 0xff:
                    candidated_key = 0x87d2
                else:
                    candidated_key = OkdFile.__ENCRYPTION_KEY_TABLE[encryption_key_index + 1]
                candidated_key |= OkdFile.__ENCRYPTION_KEY_TABLE[encryption_key_index] << 16
                if expected_key == candidated_key:
                    OkdFile.__logger.info(
                        f'OKD file encryption_key_index detected. encryption_key_index={encryption_key_index}')
                    return encryption_key_index
            raise RuntimeError(
                'Failed to detect OKD file encryption_key_index.')

    @staticmethod
    def __decrypt(input_stream: io.BufferedReader, output_stream: io.BufferedWriter, encryption_key_index: int | None, length: int | None = None):
        start_position = input_stream.tell()
        while length is None or (length is not None and (input_stream.tell() - start_position) < length):
            ciphertext_buffer = input_stream.read(2)
            if len(ciphertext_buffer) != 2:
                # return
                raise RuntimeError('Invalid ciphertext_buffer length.')
            ciphertext = int.from_bytes(ciphertext_buffer, byteorder='big')
            encryption_key: int
            if encryption_key_index is None:
                encryption_key = 0x17d7
            else:
                encryption_key = OkdFile.__ENCRYPTION_KEY_TABLE[encryption_key_index % 0x100]
            plaintext = ciphertext ^ encryption_key
            plaintext_buffer = plaintext.to_bytes(2, byteorder='big')
            output_stream.write(plaintext_buffer)
            if encryption_key_index is not None:
                encryption_key_index += 1
        return encryption_key_index

    @staticmethod
    def __read_okd_header(stream: io.BufferedReader, encryption_key_index: int):
        plaintext_stream = io.BytesIO()
        encryption_key_index = OkdFile.__decrypt(
            stream, plaintext_stream, encryption_key_index, 40)
        plaintext_stream.seek(0)

        header_buffer = plaintext_stream.read(40)
        if len(header_buffer) != 40:
            raise RuntimeError('Incalid header_buffer length.')

        magic_bytes = header_buffer[0:4]
        if magic_bytes != b'YKS1':
            raise RuntimeError('Invalid magic_bytes.')
        length = int.from_bytes(header_buffer[4:8], byteorder='big')
        version = str(header_buffer[8:24])
        id_karaoke = int.from_bytes(header_buffer[24:28], byteorder='big')
        adpcm_offset = int.from_bytes(header_buffer[28:32], byteorder='big')
        encryption_mode = int.from_bytes(header_buffer[32:36], byteorder='big')
        option_data_length: int = int.from_bytes(
            header_buffer[36:40], byteorder='big')

        encryption_key_index = OkdFile.__decrypt(
            stream, plaintext_stream, encryption_key_index, option_data_length)
        plaintext_stream.seek(40)
        option_data_buffer = plaintext_stream.read(option_data_length)
        if len(option_data_buffer) != option_data_length:
            raise RuntimeError('Invalid option_data_buffer length.')

        if option_data_length != 0:
            if option_data_length == 12:
                yks_chunk_length = int.from_bytes(
                    option_data_buffer[0:4], byteorder='big')
                mmt_chunk_length = int.from_bytes(
                    option_data_buffer[4:8], byteorder='big')
                crc_yks_loader = int.from_bytes(
                    option_data_buffer[8:10], byteorder='big')
                crc_loader = int.from_bytes(
                    option_data_buffer[10:12], byteorder='big')
                return MmtOkdHeader(magic_bytes, length, version, id_karaoke, adpcm_offset, encryption_mode, yks_chunk_length, mmt_chunk_length, crc_yks_loader, crc_loader)
            elif option_data_length == 20:
                yks_chunk_length = int.from_bytes(
                    option_data_buffer[0:4], byteorder='big')
                mmt_chunk_length = int.from_bytes(
                    option_data_buffer[4:8], byteorder='big')
                mmk_chunk_length = int.from_bytes(
                    option_data_buffer[8:12], byteorder='big')
                crc_yks_loader = int.from_bytes(
                    option_data_buffer[12:14], byteorder='big')
                crc_yks_mmk_okd = int.from_bytes(
                    option_data_buffer[14:16], byteorder='big')
                crc_loader = int.from_bytes(
                    option_data_buffer[16:18], byteorder='big')
                return MmkOkdHeader(magic_bytes, length, version, id_karaoke, adpcm_offset, encryption_mode, yks_chunk_length, mmt_chunk_length, mmk_chunk_length, crc_yks_loader, crc_yks_mmk_okd, crc_loader)
            elif option_data_length == 24:
                yks_chunk_length = int.from_bytes(
                    option_data_buffer[0:4], byteorder='big')
                mmt_chunk_length = int.from_bytes(
                    option_data_buffer[4:8], byteorder='big')
                mmk_chunk_length = int.from_bytes(
                    option_data_buffer[8:12], byteorder='big')
                spr_chunk_length = int.from_bytes(
                    option_data_buffer[12:16], byteorder='big')
                crc_yks_loader = int.from_bytes(
                    option_data_buffer[16:18], byteorder='big')
                crc_yks_mmt_okd = int.from_bytes(
                    option_data_buffer[18:20], byteorder='big')
                crc_yks_mmt_mmk_okd = int.from_bytes(
                    option_data_buffer[20:22], byteorder='big')
                crc_loader = int.from_bytes(
                    option_data_buffer[22:24], byteorder='big')
                return SprOkdHeader(magic_bytes, length, version, id_karaoke, adpcm_offset, encryption_mode, yks_chunk_length, mmt_chunk_length, mmk_chunk_length, spr_chunk_length, crc_yks_loader, crc_yks_mmt_okd, crc_yks_mmt_mmk_okd)
            elif option_data_length == 32:
                yks_chunk_length = int.from_bytes(
                    option_data_buffer[0:4], byteorder='big')
                mmt_chunk_length = int.from_bytes(
                    option_data_buffer[4:8], byteorder='big')
                mmk_chunk_length = int.from_bytes(
                    option_data_buffer[8:12], byteorder='big')
                spr_chunk_length = int.from_bytes(
                    option_data_buffer[12:16], byteorder='big')
                dio_chunk_length = int.from_bytes(
                    option_data_buffer[16:20], byteorder='big')
                crc_yks_loader = int.from_bytes(
                    option_data_buffer[20:22], byteorder='big')
                crc_yks_mmk_okd = int.from_bytes(
                    option_data_buffer[22:24], byteorder='big')
                crc_yks_mmt_mmk_okd = int.from_bytes(
                    option_data_buffer[24:26], byteorder='big')
                crc_yks_mmt_mmk_spr_okd = int.from_bytes(
                    option_data_buffer[26:28], byteorder='big')
                crc_loader = int.from_bytes(
                    option_data_buffer[28:30], byteorder='big')
                return DioOkdHeader(magic_bytes, length, version, id_karaoke, adpcm_offset, encryption_mode, yks_chunk_length, mmt_chunk_length, mmk_chunk_length, spr_chunk_length, dio_chunk_length, crc_yks_loader, crc_yks_mmt_okd, crc_yks_mmt_mmk_okd, crc_yks_mmt_mmk_spr_okd, crc_loader)

        return GenericOkdHeader(magic_bytes, length, version, id_karaoke, adpcm_offset, encryption_mode, option_data_buffer)

    @staticmethod
    def __validate_okd_header(data: OkdHeader, file_type: OkdFileType):
        if data.encryption_mode != 0x000000:
            OkdFile.__logger.info(
                f'Invalid encryption_mode. encryption_mode={data.encryption_mode}')
            return False
        if file_type == OkdFileType.OKD or file_type == OkdFileType.P3 or file_type == OkdFileType.DIFF or file_type == OkdFileType.MP3DIFF or file_type == OkdFileType.MMTTXT:
            if data.magic_bytes != b'YKS1':
                OkdFile.__logger.info(
                    f'Invalid magic_bytes. magic_bytes={data.magic_bytes}')
                return False
            version_prefix = data.version[0:8]
            if version_prefix != 'YKS-1    ' and (file_type == OkdFileType.P3 and version_prefix != 'YKS-2    '):
                OkdFile.__logger.info(
                    f'Invalid version_prefix. version_prefix={version_prefix}')
                return False
        elif file_type == OkdFileType.M3 or file_type == OkdFileType.ONTA or file_type == OkdFileType.ONTADIFF:
            if data.magic_bytes != b'YOKA':
                OkdFile.__logger.info(
                    f'Invalid magic_bytes. magic_bytes={data.magic_bytes}')
                return False
        else:
            raise RuntimeError(f'Invalid file_type. file_type={file_type}')
        return True

    @staticmethod
    def __read_oka_header(stream: io.BufferedReader, encryption_key_index: int):
        plaintext_stream = io.BytesIO()
        encryption_key_index = OkdFile.__decrypt(
            stream, plaintext_stream, encryption_key_index, 40)
        plaintext_stream.seek(0)

        header_buffer = plaintext_stream.read(40)
        if len(header_buffer) != 40:
            raise RuntimeError('Incalid header_buffer length.')

        magic_bytes = header_buffer[0:4]
        if magic_bytes != b'YOKA':
            raise RuntimeError('Invalid magic_bytes.')
        length = int.from_bytes(header_buffer[4:8], byteorder='big')
        version = str(header_buffer[8:24])
        id_karaoke = int.from_bytes(header_buffer[24:28], byteorder='big')
        data_offset = int.from_bytes(header_buffer[28:32], byteorder='big')
        reserved = int.from_bytes(header_buffer[32:36], byteorder='big')
        crc_loader: int = int.from_bytes(header_buffer[36:40], byteorder='big')

        return OkaHeader(magic_bytes, length, version, id_karaoke, data_offset, reserved, crc_loader)

    @staticmethod
    def __read_file_header(stream: io.BufferedReader, file_type: OkdFileType, encryption_key_index: int):
        if file_type == OkdFileType.OKD or file_type == OkdFileType.P3 or file_type == OkdFileType.DIFF or file_type == OkdFileType.MP3DIFF or file_type == OkdFileType.MMTTXT:
            return OkdFile.__read_okd_header(stream, encryption_key_index)
        elif file_type == OkdFileType.M3 or file_type == OkdFileType.ONTA or file_type == OkdFileType.ONTADIFF:
            return OkdFile.__read_oka_header(stream, encryption_key_index)
        else:
            raise RuntimeError(f'Invalid file_type. file_type={file_type}')

    @staticmethod
    def __peek_chunk_header(stream: io.BufferedReader):
        while True:
            chunk_header_buffer = stream.read(8)
            chunk_header_length = len(chunk_header_buffer)
            if chunk_header_length < 8:
                stream.seek(-chunk_header_length, os.SEEK_CUR)
                return
            chunk_id = chunk_header_buffer[0:4]
            chunk_size = int.from_bytes(
                chunk_header_buffer[4:8], byteorder='big')
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
    def decrypt(input_stream: io.BufferedReader, chunks_stream: io.BufferedWriter, file_type: OkdFileType):
        start_position = input_stream.tell()

        encryption_key_index = OkdFile.__detect_first_encryption_key_index(
            input_stream, file_type)
        header = OkdFile.__read_file_header(
            input_stream, file_type, encryption_key_index)

        data_offset = input_stream.tell() - start_position
        data_length = header.length - data_offset

        extended_data_offset: int
        if isinstance(header, OkdHeader):
            extended_data_offset = header.adpcm_offset
        else:
            extended_data_offset = header.data_offset
        if extended_data_offset != 0:
            extended_data_offset -= 40

        extended_data_length: int
        if header.adpcm_offset == 0:
            extended_data_length = 0
        else:
            extended_data_length = data_length - extended_data_offset

        encrypted_length = data_length - extended_data_length

        # Decrypt
        OkdFile.__decrypt(input_stream, chunks_stream,
                          encryption_key_index, encrypted_length)
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
    def read_chunk(buffer: bytes):
        if len(buffer) < 8:
            raise RuntimeError('Invalid buffer length.')

        chunk_id = buffer[0:4]
        chunk_size = int.from_bytes(buffer[4:8], byteorder='big')
        chunk_data = buffer[8:]
        if len(chunk_data) < chunk_size:
            raise RuntimeError('Invalid chunk_data length.')
        chunk_data_stream = io.BytesIO(chunk_data)

        if chunk_id == b'YPTI':
            return OkdPTrackInfoChunk.read(
                chunk_data_stream)
        elif chunk_id == b'YADD':
            return OkdAdpcmChunk.read(chunk_data_stream)

        return OkdGenericChunk(chunk_id, chunk_data)
