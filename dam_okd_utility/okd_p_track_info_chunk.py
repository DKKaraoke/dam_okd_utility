import io
from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger


class OkdPTrackInfoChannelInfoEntry(NamedTuple):
    """DAM OKD P-Track Information Channel Information Entry
    """

    attribute: int
    port: int
    acchg_1: int
    acchg_2: int


class OkdPTrackInfoEntry(NamedTuple):
    """DAM OKD P-Track Information Entry
    """

    __logger = getLogger('OkdPTrackInfoEntry')

    @staticmethod
    def read(stream: io.BufferedReader):
        header_buffer = stream.read(4)
        if len(header_buffer) != 4:
            raise RuntimeError('Invalid header_buffer length.')
        track_number = int.from_bytes(header_buffer[0:2], byteorder='little')
        use_channel_group_flag = int.from_bytes(
            header_buffer[2:4], byteorder='big')

        channel_groups: list[int] = []
        for channel in range(16):
            if (use_channel_group_flag >> channel) & 0x0001 == 0x0001:
                channel_group_buffer = stream.read(2)
                if len(channel_group_buffer) != 2:
                    raise RuntimeError('Invalid channel_group_buffer length.')
                channel_group = int.from_bytes(
                    channel_group_buffer, byteorder='big')
                channel_groups.append(channel_group)
            else:
                channel_groups.append(0x0001 << channel)

        for channel in range(16):
            channel_group_buffer = stream.read(2)
            if len(channel_group_buffer) != 2:
                raise RuntimeError('Invalid channel_group_buffer length.')
            channel_group = int.from_bytes(
                channel_group_buffer, byteorder='big')
            channel_groups.append(channel_group)

        channel_info: list[int] = []
        for channel in range(16):
            channel_info_entry_buffer = stream.read(4)
            if len(channel_info_entry_buffer) != 4:
                raise RuntimeError('Invalid channel_info_entry_buffer length.')
            channel_attribute = channel_info_entry_buffer[0]
            channel_port = channel_info_entry_buffer[1]
            channel_acchg_1 = channel_info_entry_buffer[2]
            channel_acchg_2 = channel_info_entry_buffer[3]
            channel_info.append(OkdPTrackInfoChannelInfoEntry(
                channel_attribute, channel_port, channel_acchg_1, channel_acchg_2))

        system_ex_port_buffer = stream.read(2)
        if len(system_ex_port_buffer) != 2:
            raise RuntimeError('Invalid system_ex_port_buffer length.')
        system_ex_port = int.from_bytes(
            system_ex_port_buffer, byteorder='little')

        return OkdPTrackInfoEntry(track_number, channel_groups, channel_info, system_ex_port)

    track_number: int
    channel_groups: list[int]
    channel_info: list[OkdPTrackInfoChannelInfoEntry]
    system_ex_port: int


class OkdPTrackInfoChunk(NamedTuple):
    """DAM OKD P-Track Information Chunk
    """

    __logger = getLogger('OkdPTrackInfoChunk')

    @staticmethod
    def read(stream: io.BufferedReader):
        p_track_info: list[OkdPTrackInfoEntry] = []
        entry_count_buffer = stream.read(2)
        if len(entry_count_buffer) != 2:
            raise RuntimeError('Invalid entry_count_buffer length.')
        entry_count = int.from_bytes(
            entry_count_buffer, byteorder='big')
        for _ in range(entry_count):
            p_track_info.append(OkdPTrackInfoEntry.read(stream))
        return OkdPTrackInfoChunk(p_track_info)

    p_track_info: list[OkdPTrackInfoEntry]
