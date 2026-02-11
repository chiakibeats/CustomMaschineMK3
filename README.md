# CustomMaschineMK3

Ableton MIDI Remote Script for Maschine MK3 / Plus

# Requirements

* Ableton Live 11: 11.3.35 or later
* Ableton Live 12: 12.1.10 or later
* Hardware: Maschine MK3, Maschine Plus

# Install
See [How to Install](https://chiakibeats.github.io/CustomMaschineDocs/docs/how-to-install/) on GitHub Pages.

# Feature Summary
See [All Operations](https://chiakibeats.github.io/CustomMaschineDocs/docs/all-operations) for exhaustive list.

* Transport Control
    * Basic playback control, loop metronome ON / OFF, and tap tempo
* Session View Control
    * Clip and scene trigger and stop
    * Copy and delete available
    * Fixed-length recording
* 3 Keyboard Modes (Auto-switching)
    * Normal: Typical MIDI keyboard integrated with Live's scale mode
    * Drum Rack: Trigger drum pads in Drum Rack device, and pad LED colors reflect each pad color and states (mute or solo)
    * Simpler: If Simpler playback mode is "Slicing", you can trigger and edit simpler slices
* Additional Features for Keyboard Modes
    * Note repeat
    * Fix note-on velocity to 127
    * 16 fixed velocity levels mode for selected note pitch / drum pad / simpler slice
    * Select notes in clip
* Step Sequencer
    * Edit clip notes by pressing pads (tweak note position / length / velocity available)
    * Select focused bar by group buttons
    * Copy, paste, and erase each bar
* Touch Strip Features
    * Pitch bend
    * Control device / mixer parameter
    * Crossfader control
* Device Control
    * Select device and control its parameters
    * Custom parameter banks are available for Simpler, Wavetable, EQ Eight, Hybrid Reverb, and Meld
* Mixer Control (updated to 8-track version since v1.3)
    * Change volume, panning, and send amount
    * Select, arm, mute, and solo track
    * Change crossfader assign
* Clip Editor
    * Edit various clip properties
    * Example: clip start, clip length, loop settings, warp settings, launch settings, mute, pitch, gain, etc.
* Simple Browser
    * It works!… But it's isolated from Ableton Live's internal browser
    * Hot-swap available
* Text Display
    * Show parameter values and states about selected mode
* Custom MIDI Mapping Mode
    * Dedicated 16x knobs and buttons (8 elements, 2 pages) for MIDI mapping
* Various Operations
    * Change master track volume
    * Change groove amount
    * Fast-forward, rewind playing position
    * Jump to next or previous cue point
    * Change song tempo
    * Change scale options (ON / OFF, scale mode, root note)
    * Switch main view between session and arrangement

# Documents
https://chiakibeats.github.io/CustomMaschineDocs/

# Support
Contact via [NI forum thread](https://community.native-instruments.com/discussion/42193/) or open GitHub issue

# Known Issue
* LED feedback of custom MIDI mapping mode leaks into keyboard mode
    * This happens in the very low range notes (C-2 to G-2)
    * Currently under investigation, but you can play these notes normally