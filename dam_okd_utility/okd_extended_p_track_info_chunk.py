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

    def write(self, stream: bitstring.BitStream):
        stream.append(bitstring.pack("uintle:16", self.attribute))
        stream.append(bitstring.pack("uintbe:16", self.ports))
        stream.append(bitstring.pack("uintbe:16", self.reserved))
        stream.append(bitstring.pack("uint:8", self.control_change_ax))
        stream.append(bitstring.pack("uint:8", self.control_change_cx))

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
            single_channel_groups.append(stream.read("uintbe:16"))

        channel_groups: list[int] = []
        for channel in range(16):
            channel_groups.append(stream.read("uintbe:16"))

        channel_info: list[int] = []
        for channel in range(16):
            channel_info.append(OkdExtendedPTrackInfoChannelInfoEntry.read(stream))

        system_ex_ports: int = stream.read("uintbe:16")
        reserved_2: int = stream.read("uintbe:16")

        return OkdExtendedPTrackInfoEntry(
            track_number,
            track_status,
            reserved_1,
            single_channel_groups,
            channel_groups,
            channel_info,
            system_ex_ports,
            reserved_2,
        )

    def write(self, stream: bitstring.BitStream):
        stream.append(bitstring.pack("uint:8", self.track_number))
        stream.append(bitstring.pack("uint:8", self.track_status))
        stream.append(bitstring.pack("uintbe:16", self.reserved_1))
        for single_channel_group in self.single_channel_groups:
            stream.append(bitstring.pack("uintbe:16", single_channel_group))
        for channel_group in self.channel_groups:
            stream.append(bitstring.pack("uintbe:16", channel_group))
        for channel_info_entry in self.channel_info:
            channel_info_entry.write(stream)
        stream.append(bitstring.pack("uintbe:16", self.system_ex_ports))
        stream.append(bitstring.pack("uintbe:16", self.reserved_2))

    track_number: int
    track_status: int
    reserved_1: int
    single_channel_groups: list[int]
    channel_groups: list[int]
    channel_info: list[OkdExtendedPTrackInfoChannelInfoEntry]
    system_ex_ports: int
    reserved_2: int


class OkdExtendedPTrackInfoChunk(NamedTuple):
    """DAM OKD Extended P-Track Information Chunk"""

    __logger = getLogger("OkdExtendedPTrackInfoChunk")

    @staticmethod
    def read(stream: bitstring.BitStream):
        # Skip unknown
        stream.bytepos += 8
        tg_mode = stream.read("uintbe:16")
        entry_count = stream.read("uintbe:16")
        data: list[OkdExtendedPTrackInfoEntry] = []
        for _ in range(entry_count):
            entry = OkdExtendedPTrackInfoEntry.read(stream)
            data.append(entry)
        return OkdExtendedPTrackInfoChunk(tg_mode, data)

    def write(self, stream: bitstring.BitStream):
        # Write unknown
        stream.append(b"\x00" * 8)
        stream.append(bitstring.pack("uintbe:16", self.tg_mode))
        stream.append(bitstring.pack("uintbe:16", len(self.data)))
        for entry in self.data:
            entry.write(stream)

    @staticmethod
    def from_json_object(json_object: object):
        if "attribute" in json_object:
            return OkdExtendedPTrackInfoChannelInfoEntry(
                json_object["attribute"],
                json_object["ports"],
                json_object["reserved"],
                json_object["control_change_ax"],
                json_object["control_change_cx"],
            )
        elif "track_number" in json_object:
            return OkdExtendedPTrackInfoEntry(
                json_object["track_number"],
                json_object["track_status"],
                json_object["reserved_1"],
                json_object["single_channel_groups"],
                json_object["channel_groups"],
                json_object["channel_info"],
                json_object["system_ex_ports"],
                json_object["reserved_2"],
            )
        elif "data" in json_object:
            return OkdExtendedPTrackInfoChunk(
                json_object["tg_mode"], json_object["data"]
            )

    tg_mode: int
    data: list[OkdExtendedPTrackInfoEntry]
