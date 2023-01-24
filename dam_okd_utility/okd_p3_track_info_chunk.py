import bitstring
from typing import NamedTuple

from dam_okd_utility.customized_logger import getLogger


class OkdP3TrackInfoChannelInfoEntry(NamedTuple):
    """DAM OKD P3-Track Information Channel Information Entry"""

    @staticmethod
    def read(stream: bitstring.BitStream):
        attribute: int = stream.read("uint:8")
        ports: int = stream.read("uint:8") & 0x07
        control_change_ax: int = stream.read("uint:8")
        control_change_cx: int = stream.read("uint:8")
        return OkdP3TrackInfoChannelInfoEntry(
            attribute, ports, control_change_ax, control_change_cx
        )

    def is_chorus(self):
        return self.attribute & 0x01 != 0x01

    def is_guide_melody(self):
        return self.attribute & 0x80 != 0x80

    def write(self, stream: bitstring.BitStream):
        stream.append(bitstring.pack("uint:8", self.attribute))
        stream.append(bitstring.pack("uint:8", self.ports))
        stream.append(bitstring.pack("uint:8", self.control_change_ax))
        stream.append(bitstring.pack("uint:8", self.control_change_cx))

    attribute: int
    ports: int
    control_change_ax: int
    control_change_cx: int


class OkdP3TrackInfoChunk(NamedTuple):
    """DAM OKD P3-Track Information Chunk"""

    __logger = getLogger("OkdP3TrackInfoEntry")

    @staticmethod
    def read(stream: bitstring.BitStream):
        track_number: int = stream.read("uint:8")
        track_status: int = stream.read("uint:8")
        use_channel_group_flag: int = stream.read("uintbe:16")

        single_channel_groups: list[int] = []
        for channel in range(16):
            if (use_channel_group_flag >> channel) & 0x0001 == 0x0001:
                single_channel_groups.append(stream.read("uintbe:16"))
            else:
                single_channel_groups.append(0x0000)

        channel_groups: list[int] = []
        for channel in range(16):
            channel_groups.append(stream.read("uintbe:16"))

        channel_info: list[int] = []
        for channel in range(16):
            channel_info.append(OkdP3TrackInfoChannelInfoEntry.read(stream))

        system_ex_ports: int = stream.read("uintle:16")

        return OkdP3TrackInfoChunk(
            track_number,
            track_status,
            use_channel_group_flag,
            single_channel_groups,
            channel_groups,
            channel_info,
            system_ex_ports,
        )

    def write(self, stream: bitstring.BitStream):
        stream.append(bitstring.pack("uint:8", self.track_number))
        stream.append(bitstring.pack("uint:8", self.track_status))
        stream.append(bitstring.pack("uintbe:16", self.use_channel_group_flag))
        for channel, single_channel_group in enumerate(self.single_channel_groups):
            if (self.use_channel_group_flag >> channel) & 0x0001 == 0x0001:
                stream.append(bitstring.pack("uintbe:16", single_channel_group))
        for channel_group in self.channel_groups:
            stream.append(bitstring.pack("uintbe:16", channel_group))
        for channel_info_entry in self.channel_info:
            channel_info_entry.write(stream)
        stream.append(bitstring.pack("uintle:16", self.system_ex_ports))

    @staticmethod
    def from_json_object(json_object: object):
        if "attribute" in json_object:
            return OkdP3TrackInfoChannelInfoEntry(
                json_object["attribute"],
                json_object["ports"],
                json_object["control_change_ax"],
                json_object["control_change_cx"],
            )
        elif "track_number" in json_object:
            return OkdP3TrackInfoChunk(
                json_object["track_number"],
                json_object["track_status"],
                json_object["use_channel_group_flag"],
                json_object["single_channel_groups"],
                json_object["channel_groups"],
                json_object["channel_info"],
                json_object["system_ex_ports"],
            )

    track_number: int
    track_status: int
    use_channel_group_flag: int
    single_channel_groups: list[int]
    channel_groups: list[int]
    channel_info: list[OkdP3TrackInfoChannelInfoEntry]
    system_ex_ports: int
