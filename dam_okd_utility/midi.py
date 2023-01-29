import mido


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
