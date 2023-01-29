import mido


def relative_time_track_to_absolute_time_track(relative_time_track: mido.MidiTrack):
    absolute_time_track = mido.MidiTrack()
    absolute_time = 0
    for relative_time_message in relative_time_track:
        absolute_time += relative_time_message.time
        absolute_time_message = relative_time_message.copy()
        absolute_time_message.time = absolute_time
        absolute_time_track.append(absolute_time_message)

    return absolute_time_track


def get_first_tempo(midi: mido.MidiFile):
    for track in midi.tracks:
        for midi_message in track:
            if midi_message.type == "set_tempo":
                return midi_message.tempo

    return 500000


def is_meta_track(midi_track: mido.MidiTrack):
    for midi_message in midi_track:
        if isinstance(midi_message, mido.Message):
            return False

    return True


def get_track_port(midi_track: mido.MidiTrack):
    for midi_message in midi_track:
        if midi_message.type == "midi_port":
            return midi_message.port

    return 0


def has_port_track(midi: mido.MidiFile, port: int):
    for track in midi.tracks:
        for midi_message in track:
            if midi_message.type == "midi_port" and midi_message.port == port:
                return True

    return False


def get_first_port_track(midi: mido.MidiFile, port: int):
    for track in midi.tracks:
        for midi_message in track:
            if midi_message.type == "midi_port" and midi_message.port == port:
                return track


def remove_port_tracks(midi: mido.MidiFile, port: int):
    for index, midi_track in enumerate(midi.tracks):
        if get_track_port(midi_track) == port:
            midi.tracks.pop(index)


def get_port_channel_track(midi: mido.MidiFile, port: int, channel: int):
    port_tracks: list[mido.MidiTrack] = []
    for track in midi.tracks:
        for midi_message in track:
            if midi_message.type == "midi_port" and midi_message.port == port:
                port_tracks.append(track)

    for port_track in port_tracks:
        for midi_message in port_track:
            if midi_message.type == "note_on" and midi_message.channel == channel:
                return port_track


def get_first_note_time(midi: mido.MidiFile):
    first_note_time = 16777216
    for track in midi.tracks:
        absolute_time_track = relative_time_track_to_absolute_time_track(track)
        for absolute_time_message in absolute_time_track:
            if absolute_time_message.type != "note_on":
                continue

            first_note_time = min(absolute_time_message.time, first_note_time)

    return first_note_time


def get_last_note_time(midi: mido.MidiFile):
    last_note_time = 0
    for track in midi.tracks:
        absolute_time_track = relative_time_track_to_absolute_time_track(track)
        for absolute_time_message in absolute_time_track:
            if absolute_time_message.type != "note_on":
                continue

            last_note_time = max(absolute_time_message.time, last_note_time)

    return last_note_time
