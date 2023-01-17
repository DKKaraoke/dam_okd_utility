import bitstring
from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger


class OkdExtendedPTrackInfoChannelInfoEntry(NamedTuple):
    """DAM OKD Extended P-Track Information Channel Information Entry"""

    @staticmethod
    def read(stream: bitstring.BitStream):
        attribute: int = stream.read("uintle:16")
        ports: int = stream.read("uintbe:16")
        reserved: int = stream.read("uintbe:16")
        control_change_ax: int = stream.read("uint:8")
        control_change_cx: int = stream.read("uint:8")
        return OkdExtendedPTrackInfoChannelInfoEntry(
            attribute, ports, reserved, control_change_ax, control_change_cx
        )

    def is_chorus(self):
        return self.attribute & 0x80 != 0x80

    def is_guide_melody(self):
        return self.attribute & 0x0100 == 0x0100

    attribute: int
    ports: int
    reserved: int
    control_change_ax: int
    control_change_cx: int


class OkdExtendedPTrackInfoEntry(NamedTuple):
    """DAM OKD Extended P-Track Information Entry"""

    __logger = getLogger("OkdExtendedPTrackInfoEntry")

    @staticmethod
    def read(stream: bitstring.BitStream):
        track_number: int = stream.read("uint:8")
        track_status: int = stream.read("uint:8")
        reserved_1: int = stream.read("uintbe:16")

        single_channel_groups: list[int] = []
        for channel in range(16):
            single_channel_group: int = stream.read("uintbe:16")
            single_channel_groups.append(single_channel_group)

        channel_groups: list[int] = []
        for channel in range(16):
            channel_group: int = stream.read("uintbe:16")
            channel_groups.append(channel_group)

        channel_info: list[int] = []
        for channel in range(16):
            channel_info.append(OkdExtendedPTrackInfoChannelInfoEntry.read(stream))

        system_ex_port: int = stream.read("uintle:16")
        reserved_2: int = stream.read("uintbe:16")

        return OkdExtendedPTrackInfoEntry(
            track_number,
            track_status,
            reserved_1,
            single_channel_groups,
            channel_groups,
            channel_info,
            system_ex_port,
            reserved_2,
        )

    track_number: int
    track_status: int
    reserved_1: int
    single_channel_groups: list[int]
    channel_groups: list[int]
    channel_info: list[OkdExtendedPTrackInfoChannelInfoEntry]
    system_ex_port: int
    reserved_2: int


class OkdExtendedPTrackInfoChunk(NamedTuple):
    """DAM OKD Extended P-Track Information Chunk"""

    __logger = getLogger("OkdExtendedPTrackInfoChunk")

    @staticmethod
    def read(stream: bitstring.BitStream):
        # Skip unknown
        stream.bytepos += 8
        tg_mode = stream.read("uintbe:16")
        data: list[OkdExtendedPTrackInfoEntry] = []
        entry_count = stream.read("uintbe:16")
        for _ in range(entry_count):
            entry = OkdExtendedPTrackInfoEntry.read(stream)
            data.append(entry)
        return OkdExtendedPTrackInfoChunk(tg_mode, data)

    tg_mode: int
    data: list[OkdExtendedPTrackInfoEntry]
