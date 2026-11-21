# flake8: noqa
# mypy: ignore-errors
"""Create the project's original synthwave / chiptune soundtrack.

This file is for *offline* regeneration, not needed to run the game.
Optional build-time dependencies: pip install numpy soundfile
All note progressions and synthesized effects below were composed for
this project; no existing commercial recordings or sampled music are used.
"""

from pathlib import Path
import math
import numpy as np
import soundfile as sf

RATE = 22050
OUT = Path(__file__).resolve().parent.parent / 'assets' / 'audio'
OUT.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(4242)
NOTES = {'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
         'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11}


def hz(note):
    if note is None or note == '-':
        return 0.0
    key = note[:-1]
    octave = int(note[-1])
    return 440.0 * 2 ** ((12 * (octave + 1) + NOTES[key] - 69) / 12)


def waveform(phase, kind):
    # Band-limited-ish mixtures of the harmonics provide an arcade flavour
    # with much less harshness than a full-strength square wave.
    if kind == 'lead':
        return (np.sin(phase) + .25*np.sin(3*phase) + .11*np.sin(5*phase)) / 1.36
    if kind == 'bass':
        return (.75*np.sin(phase) + .22*np.sin(2*phase) + .07*np.sin(3*phase))
    if kind == 'arp':
        return (.80*np.sin(phase) + .18*np.sin(4*phase))
    if kind == 'bell':
        return (.75*np.sin(phase) + .17*np.sin(2.01*phase) + .08*np.sin(3.98*phase))
    return np.sin(phase)


def put_note(buf, start, duration, note, volume, kind='lead', attack=.009, release=.08):
    freq = hz(note)
    if not freq:
        return
    start_idx = max(0, round(start * RATE))
    length = min(round(duration * RATE), len(buf) - start_idx)
    if length < 2:
        return
    t = np.arange(length) / RATE
    f = freq * (1.0 + .003*np.exp(-t * 14))
    phase = 2*np.pi*np.cumsum(f) / RATE
    envelope = np.minimum(1., t / max(attack,.001))
    envelope *= np.minimum(1., (duration-t) / max(release,.001))
    if kind in ('arp','bell'):
        envelope *= .73 + .27 * np.exp(-3*t)
    buf[start_idx:start_idx+length] += volume * waveform(phase, kind) * envelope


def drum(buf, start, which, vol=1):
    i = round(start * RATE)
    dur = .25 if which == 'kick' else .15
    n = min(round(RATE*dur), len(buf)-i)
    if n <= 0: return
    t = np.arange(n)/RATE
    if which == 'kick':
        f = 45 + 110*np.exp(-t*32)
        phase = 2*np.pi*np.cumsum(f)/RATE
        wave = np.sin(phase)*np.exp(-t*22)
    elif which == 'snare':
        noise = RNG.uniform(-1,1,n)
        wave = (.64*noise + .36*np.sin(2*np.pi*170*t))*np.exp(-t*30)
    else:
        noise = RNG.uniform(-1,1,n)
        # crisp, gently decaying hat
        wave = (noise - np.convolve(noise, np.ones(6)/6,mode='same'))*np.exp(-t*55)
    buf[i:i+n] += wave * (0.17 if which == 'kick' else 0.088 if which == 'snare' else .030)*vol


def song(name, bpm, melody, chords, density='soft'):
    """Write a fully original eight-bar loop with drums, bass and arps."""
    beat = 60/bpm
    duration = beat*32
    signal = np.zeros(round(RATE*duration),dtype=np.float64)
    # Each bar consists of 8 eighth notes, 64 steps in total.
    melody = (melody*math.ceil(64/len(melody)))[:64]
    for bar in range(8):
        root, third, fifth = chords[bar % len(chords)]
        bar_time = bar*4*beat
        for off, bass_note in ((0,root),(2,root),(2.5,fifth),(3,third)):
            put_note(signal,bar_time+off*beat,beat*(.43 if off==2.5 else .82),
                     bass_note, .14 if density=='soft' else .19, 'bass',release=.12)
        for k in range(8):
            arp_note = (root,third,fifth,third,root,third,fifth,third)[k]
            # Octave-up chord arpeggios: enough detail to feel alive but
            # deliberately quiet so the melody stays in front.
            arp_up = arp_note[:-1] + str(int(arp_note[-1])+1)
            put_note(signal, bar_time+k*beat/2, beat*.34, arp_up,
                     .045 if density=='soft' else .065, 'arp',release=.09)
        for k in range(4):
            drum(signal,bar_time+k*beat,'kick' if k in (0,2) else 'snare',
                 .85 if density=='soft' else 1.05)
            drum(signal,bar_time+k*beat,'hat',1)
            if density!='soft': drum(signal,bar_time+(k+.5)*beat,'hat',.8)
    for k,note in enumerate(melody):
        if note=='-':continue
        start=k*beat/2
        put_note(signal,start,beat*(.38 if density!='power' else .28),note,
                 .19 if density=='soft' else .23,'lead',release=.055)
        if density=='power' and k%4==3:
            put_note(signal,start+beat*.18,beat*.17,note,.065,'bell',release=.04)
    # Avoid hard loop seams; notes deliberately release before the bar ends.
    # A gentle leading/trailing crossfade further avoids clicking.
    n=min(len(signal)//20,round(RATE*.08))
    signal[:n]*=np.linspace(0,1,n)
    signal[-n:]*=np.linspace(1,0,n)
    signal = np.tanh(signal * 1.65) * .83
    sf.write(OUT/f'{name}.ogg',signal.astype(np.float32),RATE,
             format='OGG',subtype='VORBIS')
    # Portable PCM fallback for SDL_mixer builds lacking Vorbis support.
    sf.write(OUT/f'{name}.wav',signal.astype(np.float32),RATE,subtype='PCM_16')
    print(name,round(duration,1),'seconds',round((OUT/f'{name}.ogg').stat().st_size/1024),'KiB')


menu_melody = ['E5','G5','A5','-','G5','E5','D5','C5',
               'D5','E5','G5','E5','D5','-','C5','B4',
               'C5','E5','G5','A5','G5','E5','D5','-','E5','D5','C5','D5','E5','-','G5','-']
maze_melody = ['D5','-','F5','D5','A5','F5','E5','D5',
               'C5','D5','F5','A5','G5','F5','E5','-',
               'D5','D5','F5','A5','C6','A5','G5','F5','E5','F5','G5','E5','D5','-','A4','-']
chase_melody = ['A5','D6','A5','G5','F5','A5','C6','A5',
                'G5','F5','E5','D5','F5','A5','D6','-',
                'C6','A5','G5','A5','F5','D5','E5','F5','G5','A5','C6','A5','G5','F5','E5','D5']
power_melody = ['A5','C6','D6','C6','A5','G5','F5','G5',
                'A5','A5','C6','D6','E6','D6','C6','A5',
                'G5','A5','C6','A5','F5','A5','C6','E6','D6','C6','A5','G5','F5','G5','A5','-']

song('menu_star_chomp',122,menu_melody,
     [('A3','C4','E4'),('F3','A3','C4'),('C4','E4','G4'),('G3','B3','D4')], 'soft')
song('maze_moonwalk',140,maze_melody,
     [('D3','F3','A3'),('C3','E3','G3'),('A2','C3','E3'),('G2','B2','D3')], 'normal')
song('maze_night_run',160,chase_melody,
     [('D3','F3','A3'),('A2','C3','E3'),('G2','B2','D3'),('A2','C3','E3')], 'normal')
song('power_rush',172,power_melody,
     [('F3','A3','C4'),('G3','B3','D4'),('A3','C4','E4'),('D3','F3','A3')], 'power')


def sfx(name, sequence, timbre='bell', gain=.6):
    """Playful original UI/game cues synthesized from short note phrases."""
    end=max(start+duration for start,duration,_,_ in sequence)+.035
    audio=np.zeros(round(end*RATE),dtype=np.float64)
    for start,dur,note,volume in sequence:
        put_note(audio,start,dur,note,volume,timbre,attack=.003,release=min(.11,dur*.55))
    audio=np.tanh(audio * gain * 2.4) *.86
    sf.write(OUT/f'{name}.wav',audio.astype(np.float32),RATE,subtype='PCM_16')

sfx('ui_move',[(0,.065,'E5',.35)],'bell',.5)
sfx('ui_select',[(0,.09,'C5',.4),(.07,.10,'G5',.34),(.15,.18,'C6',.28)],'bell',.8)
sfx('chomp_a',[(0,.056,'A4',.33),(.047,.053,'E5',.32)],'lead',.43)
sfx('chomp_b',[(0,.056,'C5',.32),(.048,.053,'G4',.31)],'lead',.43)
sfx('power',[(0,.13,'A4',.43),(.09,.13,'C5',.40),(.18,.13,'E5',.39),(.26,.23,'A5',.38)],'bell',.82)
sfx('ghost_eat',[(0,.085,'D5',.4),(.065,.085,'F5',.42),(.13,.09,'A5',.44),(.21,.19,'D6',.45)],'lead',.8)
sfx('life_lost',[(0,.15,'A4',.34),(.13,.18,'G4',.37),(.3,.23,'E4',.34),(.52,.29,'D4',.36)],'lead',.9)
sfx('level_up',[(0,.13,'D5',.37),(.10,.13,'F5',.38),(.20,.14,'A5',.39),(.34,.13,'C6',.37),(.47,.37,'D6',.45)],'bell',.8)
sfx('victory',[(0,.17,'C5',.42),(.12,.17,'E5',.44),(.24,.17,'G5',.46),(.36,.17,'C6',.5),(.55,.15,'E6',.5),(.74,.75,'G6',.45)],'bell',.86)
sfx('game_over',[(0,.23,'A4',.35),(.2,.23,'F4',.4),(.42,.28,'D4',.4),(.65,.50,'A3',.48)],'bass',.96)
print('Generated entirely original music and sound effects at',OUT)

sfx('warning',[(0,.13,'A5',.36),(.12,.2,'C6',.38)],'bell',.62)
