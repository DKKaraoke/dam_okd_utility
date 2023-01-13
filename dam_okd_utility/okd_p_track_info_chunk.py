import bitstring
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
    def read(stream: bitstring.BitStream):
        track_number = stream.read('uintle:16')
        use_channel_group_flag = stream.read('uintbe:16')

        channel_groups: list[int] = []
        for channel in range(16):
            if (use_channel_group_flag >> channel) & 0x0001 == 0x0001:
                channel_group = stream.read('uintbe:16')
                channel_groups.append(channel_group)
            else:
                channel_groups.append(0x0001 << channel)

        for channel in range(16):
            channel_group = stream.read('uintbe:16')
            channel_groups.append(channel_group)

        channel_info: list[int] = []
        for channel in range(16):
            channel_attribute = stream.read('uint:8')
            channel_port = stream.read('uint:8')
            channel_acchg_1 = stream.read('uint:8')
            channel_acchg_2 = stream.read('uint:8')
            channel_info.append(OkdPTrackInfoChannelInfoEntry(
                channel_attribute, channel_port, channel_acchg_1, channel_acchg_2))

        system_ex_port = stream.read('uintle:16')

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
    def read(stream: bitstring.BitStream):
        p_track_info: list[OkdPTrackInfoEntry] = []
        entry_count = stream.read('uintbe:16')
        for _ in range(entry_count):
            entry = OkdPTrackInfoEntry.read(stream)
            p_track_info.append(entry)
        return OkdPTrackInfoChunk(p_track_info)

    p_track_info: list[OkdPTrackInfoEntry]
