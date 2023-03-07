# dam_okd_utility

## !! Important notes !!

This software is developed for technical research on DAM Karaoke machines.

The Karaoke music data normally recorded on DAM Karaoke machines is protected by copyright. You must handle it in accordance with your local laws and regulations.

## [Demonstration video](https://twitter.com/soltia48/status/1620095004374093824)

In this video, a song not normally included in the DAM Karaoke machine, "This is an Attack," is played and scored on that machine.

## Summary

This software reads and writes DAM Karaoke machines compatible Karaoke music data file.

## Usage

### Dump

Dump the contents of a Karaoke music data.

```
$ python dump_dam_okd.py --help
usage: dump_dam_okd.py [-h] input_path output_path

DAM OKD Dumper

positional arguments:
  input_path   Input DAM OKD file path
  output_path  Output directory path

options:
  -h, --help   show this help message and exit
```

### Compose

Compose a Karaoke music data from a MIDI file.

```
$ python compose_dam_okd.py --help
usage: compose_dam_okd.py [-h] karaoke_path main_output_path scoring_reference_output_path

DAM OKD Composer

positional arguments:
  karaoke_path          Karaoke MIDI file path
  main_output_path      Output Main file path
  scoring_reference_output_path
                        Output Scoring reference file path

options:
  -h, --help            show this help message and exit
```

### Pack

Pack a Karaoke music data by directly inputting the required data in each chunk.

```
$ python pack_dam_okd.py --help
usage: pack_dam_okd.py [-h] output_path [input_path ...]

DAM OKD Creator

positional arguments:
  output_path  Output DAM OKD file path
  input_path   Input file path

options:
  -h, --help   show this help message and exit
```

## How to craete MIDI data for compose

### MIDI port and track map

- Port 0, Track 0-15: Instrument
- Port 1, Track 0-7,9-15: Instrument
- Port 1, Track 8: Guide melody
- Port 15:, First valid track: M-Track

### P-Track

P(laying)-Track is performance data of the music.

### M-Track

M(arking)-Track includes list of hook section, two-chorus fadeout position and others.
The note map in MIDI for compose is as follows.

- Hook section: C3
- Two-chorus fadeout position: C5 (Note on alone is sufficient)

Please check [the test data](test/data/p_track.mid).

## List of verified DAM Karaoke machine

- DAM-XG8000[R] (LIVE DAM Ai[R])

## Authors

- soltia48 (ソルティアよんはち)

## Thanks

- [Nurupo](https://github.com/gta191977649) - Author of the MIDI file ["This is an Attack"](https://github.com/gta191977649/midi_godekisenda) from which [the test data](test/data/p_track.mid) was derived

## License

[MIT](https://opensource.org/licenses/MIT)

Copyright (c) 2023 soltia48 (ソルティアよんはち)
