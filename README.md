# CustomMaschineMK3
Ableton MIDI Remote Script for Maschine MK3

# Feature summary
* Transport control
    * Play, stop, pause song
    * Loop and metronome on / off
    * Trigger record / capture MIDI
    * Tap tempo
* Session view control
    * Launch, select, copy-paste, delete clips
    * Launch, delete, duplicate scenes
    * Quick page jump buttons available
* 3 keyboard modes
    * Normal: Typical MIDI keyboard integrated with Live's scale mode
    * Drum Rack: Trigger drum pads in Drum Rack device and pad LED colors reflect each pad color and states (mute or solo)
    * Simpler: If Simpler playback mode is "Slicing", You can trigger simpler slices
    * Auto-switching depends on inserted instrument type
* Additional features for keyboard modes
    * Quick page / octave jump by using group buttons
    * Note repeat
    * Fix note-on velocity to 127
    * 16 fixed velocity levels mode for selected note pitch / drum pad / simpler slice
    * Select corresponding MIDI notes in clip
* Step sequencer
    * Add or delete notes by pressing pads
    * Playback position highlight
    * Bars select buttons available
    * Select note velocity via 16 levels velocity mode
    * Copy, paste, erase each bars
    * Select each step notes in clip
    * Edit note properties (position, length, velocity)
* Touch strip features
    * Pitch bend
    * Assign device / mixer parameter to touch strip
    * Crossfader control & change channel assign
* Device control
    * Change focusing device
    * Select parameter bank
    * Enable, disable, delete device
    * Modify device parameter by using 8x knobs
    * Special device parameters like Push
        * Wavetable selection for Wavetable device
        * Playback mode selection & slice editing for Simpler device
* Mixer control
    * Arm, mute, solo track
    * Change volume, panning, send amount
    * Change selected track
* Clip control
    * Change clip start, clip end, loop start, loop length
    * Change various options (activation, loop, warp settings, launch settings, pitch, etc…)
* Simple browser
    * It works!…But it's **isolated** from Ableton Live's internal browser
    * Select item and load it
    * Enable, disable sound preview
* Text display
    * Show various parameters about focusing tracks, selected device, selected clip
* Various operations
    * Change master track volume
    * Change groove amount
    * Fast-forward, rewind playing position
    * Jump to next, previous cue point
    * Change song tempo
    * Change scale options (on / off, scale mode, root note)
    * Switch main view (session / arrangement)
    * Fixed length recording in session view
    * Lock target track

# Requirements
* Ableton Live 11: 11.3 or later
* Ableton Live 12: 12.1 or later
* Hardware: Maschine MK3, Maschine+(beta, not fully tested)

# Install
1. Import controller editor template
2. Place script at Ableton Live directory
3. Configure control surface on Ableton Live
4. Enjoy!

# How to use
Coming soon

# Known Issue
* In Live 12 browser mode, Dig into "Instruments" in "Max for Live" folder causes Live app crash
* Scrolling item in each "Collections" folders is laggy (depends on size of entire library? need to check more details)
