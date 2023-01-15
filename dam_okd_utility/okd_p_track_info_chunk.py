import bitstring
from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger


class OkdPTrackInfoChannelInfoEntry(NamedTuple):
    """DAM OKD P-Track Information Channel Information Entry
    """

    @staticmethod
    def read(stream: bitstring.BitStream):
        attribute: int = stream.read('uint:8')
        port: int = stream.read('uint:8')
        control_change_ax: int = stream.read('uint:8')
        control_change_cx: int = stream.read('uint:8')
        return OkdPTrackInfoChannelInfoEntry(attribute, port, control_change_ax, control_change_cx)

    attribute: int
    port: int
    control_change_ax: int
    control_change_cx: int


class OkdPTrackInfoEntry(NamedTuple):
    """DAM OKD P-Track Information Entry
    """

    __logger = getLogger('OkdPTrackInfoEntry')

    @staticmethod
    def read(stream: bitstring.BitStream):
        track_number: int = stream.read('uint:8')
        track_status: int = stream.read('uint:8')
        use_channel_group_flag: int = stream.read('uintbe:16')

        single_channel_groups: list[int] = []
        for channel in range(16):
            if (use_channel_group_flag >> channel) & 0x0001 == 0x0001:
                single_channel_group: int = stream.read('uintbe:16')
                single_channel_groups.append(single_channel_group)
            else:
                single_channel_groups.append(0x0000)

        channel_groups: list[int] = []
        for channel in range(16):
            channel_group: int = stream.read('uintbe:16')
            channel_groups.append(channel_group)

        channel_info: list[int] = []
        for channel in range(16):
            channel_info.append(OkdPTrackInfoChannelInfoEntry.read(stream))

        system_ex_port: int = stream.read('uintle:16')

        return OkdPTrackInfoEntry(track_number, track_status, single_channel_groups, channel_groups, channel_info, system_ex_port)

    track_number: int
    track_status: int
    single_channel_groups: list[int]
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
