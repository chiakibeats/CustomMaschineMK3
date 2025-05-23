# ==================================================
#
# This file is part of CustomMaschineMK3.
# CustomMaschineMK3 is free software licensed under GPL-3.0.
# For more details, see "LICENSE" file.
# 
# Copyright (C) 2024-2025 chiaki
#
# ==================================================

from functools import partial
from ableton.v3.control_surface.skin import Skin, BasicColors
from ableton.v3.control_surface.elements import SimpleColor, RgbColor, create_rgb_color
from ableton.v3.live.util import liveobj_valid


# Rules of color space use
#
# Maschine's indexed colors:
# These have 68 (17 x 4) color variation.
# These colors classified as 17 base colors and 4 brightness levels.
#
# Live's indexed colors:
# Live has 70 color variations, actual color of these are affected by theme settings.
#  
# For balancing visibility and color matching, I set up these rules.
# 1. Colors for objects (track, clip, scene, drum pad)
# Object colors are mapped to level 2 to 4 brightness colors with few exceptions.
# We don't use brightest white as object color, it's used for accent of pressed or selected states.
# And we use level 1 brightness white for displaying dark gray instead.
# Total variation is 17 * 3 = 51, thus some colors map to same indexed color.
# 
# 2. Colors for keyboard & group buttons
# Colors of each pads based on its track color.
# In normal keyboard mode, root and other notes color are determined by following conditions.
# Root note:
# If brightness is under 4, use level 3 brightness color with same base color.
# Otherwise use color same as  track.
# 
# Other note:
# If brightness is under 4, use level 1 brightness color with same base color.
# Otherwise use level 2 brightness color with same base color.
# 
# 3. Colors for drum rack and simpler
# Simpler slice colors are same to track.
# Drum pad colors in drum rack are same to track if auto-coloring is enabled, otherwise follow chain color.

# Constants for making color index
BLACK = 0
RED = 1
ORANGE = 2
LIGHT_ORANGE = 3
WARM_YELLOW = 4
YELLOW = 5
LIME = 6
GREEN = 7
MINT = 8
CYAN = 9
TURQUOISE = 10
BLUE = 11
PLUM = 12
VIOLET = 13
PURPLE = 14
MAGENTA = 15
FUCHSIA = 16
WHITE = 31

LEVEL_1 = 0
LEVEL_2 = 1
LEVEL_3 = 2
LEVEL_4 = 3


def make_color(base, level):
    return SimpleColor(4 * base + level)

LIVE_COLOR_MAP = {
    0: (FUCHSIA, LEVEL_4), 
    1: (ORANGE, LEVEL_4), 
    2: (WARM_YELLOW, LEVEL_2), 
    3: (YELLOW, LEVEL_4), 

    4: (LIME, LEVEL_3), 
    5: (GREEN, LEVEL_3), 
    6: (MINT, LEVEL_3), 
    7: (TURQUOISE, LEVEL_4), 

    8:  (BLUE, LEVEL_4), 
    9:  (BLUE, LEVEL_2), 
    10: (BLUE, LEVEL_4), 
    11: (MAGENTA, LEVEL_4), 

    12: (MAGENTA, LEVEL_2), 
    13: (WHITE, LEVEL_3), 



    14: (RED, LEVEL_3), 
    15: (ORANGE, LEVEL_3), 
    16: (LIGHT_ORANGE, LEVEL_2), 
    17: (WARM_YELLOW, LEVEL_4), 

    18: (GREEN, LEVEL_4), 
    19: (GREEN, LEVEL_2), 
    20: (MINT, LEVEL_2), 
    21: (CYAN, LEVEL_3), 

    22: (TURQUOISE, LEVEL_3), 
    23: (TURQUOISE, LEVEL_2), 
    24: (PLUM, LEVEL_3), 
    25: (VIOLET, LEVEL_2), 

    26: (MAGENTA, LEVEL_3), 
    27: (WHITE, LEVEL_3), 



    28: (RED, LEVEL_2), 
    29: (FUCHSIA, LEVEL_4), 
    30: (WARM_YELLOW, LEVEL_4), 
    31: (YELLOW, LEVEL_4), 

    32: (LIME, LEVEL_4), 
    33: (LIME, LEVEL_2), 
    34: (GREEN, LEVEL_2), 
    35: (MINT, LEVEL_4), 

    36: (TURQUOISE, LEVEL_4), 
    37: (BLUE, LEVEL_4), 
    38: (VIOLET, LEVEL_4), 
    39: (PLUM, LEVEL_4), 

    40: (MAGENTA, LEVEL_4), 
    41: (WHITE, LEVEL_2), 



    42: (MAGENTA, LEVEL_2), 
    43: (LIGHT_ORANGE, LEVEL_2), 
    44: (ORANGE, LEVEL_2), 
    45: (YELLOW, LEVEL_2), 

    46: (LIME, LEVEL_2), 
    47: (GREEN, LEVEL_2), 
    48: (CYAN, LEVEL_2), 
    49: (BLUE, LEVEL_4), 

    50: (TURQUOISE, LEVEL_4), 
    51: (BLUE, LEVEL_4), 
    52: (PLUM, LEVEL_4), 
    53: (VIOLET, LEVEL_4), 

    54: (PURPLE, LEVEL_2), 
    55: (WHITE, LEVEL_2), 



    56: (RED, LEVEL_2), 
    57: (LIGHT_ORANGE, LEVEL_2), 
    58: (ORANGE, LEVEL_2), 
    59: (YELLOW, LEVEL_3), 

    60: (LIME, LEVEL_2), 
    61: (GREEN, LEVEL_2), 
    62: (MINT, LEVEL_3), 
    63: (TURQUOISE, LEVEL_2), 

    64: (BLUE, LEVEL_2), 
    65: (BLUE, LEVEL_3), 
    66: (PLUM, LEVEL_2), 
    67: (PURPLE, LEVEL_3), 

    68: (FUCHSIA, LEVEL_3), 
    69: (WHITE, LEVEL_1)
}

def make_color_from_element(element):
    if liveobj_valid(element):
        if element.color_index != None:
            return make_color(*LIVE_COLOR_MAP.get(element.color_index, (0, 0)))
            #return SimpleColor(element.color_index)
        else:
            return make_color(WHITE, LEVEL_3)
    else:
        return BasicColors.OFF

def make_keyboard_color(element, accent = False, group = False):
    if liveobj_valid(element):
        if element.color_index != None:
            base_color, brightness = LIVE_COLOR_MAP.get(element.color_index, (0, 0))
            if accent:
                return make_color(base_color, LEVEL_3 if brightness < LEVEL_4 else LEVEL_2)
            elif group:
                return make_color(base_color, LEVEL_2 if brightness < LEVEL_4 else LEVEL_4)
            else:
                return make_color(base_color, LEVEL_1 if brightness < LEVEL_4 else LEVEL_4)
    return BasicColors.OFF

def make_velocity_color(element, level = LEVEL_1):
    if liveobj_valid(element):
        if element.color_index != None:
            base_color, brightness = LIVE_COLOR_MAP.get(element.color_index, (0, 0))
            return make_color(base_color, level)
    BasicColors.ON

class MaschineLEDColors:

    class DefaultButton:
        On = BasicColors.ON
        Off = BasicColors.OFF
        Disabled = BasicColors.OFF

    class TargetTrack:
        LockOn = BasicColors.ON
        LockOff = BasicColors.OFF

    class Transport:
        PlayOn = BasicColors.ON
        PlayOff = BasicColors.OFF
        StopOn = BasicColors.ON
        StopOff = BasicColors.OFF
        AutomationArmOn = BasicColors.ON
        AutomationArmOff = BasicColors.OFF
        LoopOn = BasicColors.ON
        LoopOff = BasicColors.OFF
        MetronomeOn = BasicColors.ON
        MetronomeOff = BasicColors.OFF
        PunchOn = BasicColors.ON
        PunchOff = BasicColors.OFF
        TapTempoPressed = BasicColors.ON
        TapTempo = BasicColors.OFF
        NudgePressed = make_color(WHITE, LEVEL_2)
        Nudge = make_color(WHITE, LEVEL_4)
        SeekPressed = make_color(GREEN, LEVEL_3)
        Seek = make_color(GREEN, LEVEL_1)
        CanReEnableAutomation = BasicColors.ON
        CanCaptureMidi = BasicColors.ON
        CanJumpToCue = make_color(WHITE, LEVEL_3)
        CannotJumpToCue = BasicColors.OFF
        SetCuePressed = BasicColors.ON
        SetCue = BasicColors.OFF
        RecordQuantizeOn = BasicColors.ON
        RecordQuantizeOff = BasicColors.OFF

    class Recording:
        ArrangementRecordOn = BasicColors.ON
        ArrangementRecordOff = BasicColors.OFF
        ArrangementOverdubOn = BasicColors.ON
        ArrangementOverdubOff = BasicColors.OFF
        SessionRecordOn = BasicColors.ON
        SessionRecordTransition = BasicColors.ON
        SessionRecordOff = BasicColors.OFF
        SessionOverdubOn = BasicColors.ON
        SessionOverdubOff = BasicColors.OFF
        NewPressed = BasicColors.ON
        New = BasicColors.OFF

    class RecordLength:
        FixedOn = BasicColors.ON
        FixedOff = BasicColors.OFF
        Length = make_color(WHITE, LEVEL_2)
        LengthSelected = make_color(WHITE, LEVEL_4)

    class UndoRedo:
        UndoPressed = make_color(WHITE, LEVEL_2)
        Undo = make_color(WHITE, LEVEL_4)
        RedoPressed = make_color(WHITE, LEVEL_2)
        Redo = make_color(WHITE, LEVEL_4)

    class ViewControl:
        TrackPressed = BasicColors.ON
        Track = BasicColors.ON
        ScenePressed = make_color(WHITE, LEVEL_4)
        Scene = make_color(WHITE, LEVEL_2)

    class ViewToggle:
        SessionOn = BasicColors.OFF
        SessionOff = BasicColors.ON
        DetailOn = BasicColors.ON
        DetailOff = BasicColors.OFF
        ClipOn = BasicColors.ON
        ClipOff = BasicColors.OFF
        BrowserOn = BasicColors.ON
        BrowserOff = BasicColors.OFF

    class Browser:
        CanNavigateFolder = make_color(WHITE, LEVEL_2)
        CannotNavigateFolder = BasicColors.OFF
        NavigateFolderPressed = make_color(WHITE, LEVEL_4)
        CanNavigateItem = make_color(WHITE, LEVEL_2)
        CannotNavigateItem = BasicColors.OFF
        NavigateItemPressed = make_color(WHITE, LEVEL_4)
        PreviewOn = BasicColors.ON
        PreviewOff = BasicColors.OFF

    class Mixer:
        ArmOn = BasicColors.ON
        ArmOff = BasicColors.OFF
        ImplicitArmOn = BasicColors.ON
        MuteOn = BasicColors.ON
        MuteOff = BasicColors.OFF
        SoloOn = BasicColors.ON
        SoloOff = BasicColors.OFF
        Selected = BasicColors.ON
        NotSelected = BasicColors.OFF
        CrossfadeA = make_color(YELLOW, LEVEL_3)
        CrossfadeB = make_color(CYAN, LEVEL_3)
        CrossfadeOff = make_color(WHITE, LEVEL_3)
        CycleSendIndexPressed = BasicColors.OFF
        CycleSendIndex = BasicColors.ON
        CycleSendIndexDisabled = BasicColors.OFF
        NoTrack = BasicColors.OFF

    class Session:
        Slot = BasicColors.OFF
        SlotRecordButton = make_color(WHITE, LEVEL_1)
        NoSlot = BasicColors.OFF
        ClipStopped = make_color_from_element
        ClipTriggeredPlay = make_color(GREEN, LEVEL_2)
        ClipTriggeredRecord = make_color(RED, LEVEL_1)
        ClipPlaying = make_color(GREEN, LEVEL_3)
        ClipRecording = make_color(RED, LEVEL_3)
        ClipPlayingDimmed = make_color(GREEN, LEVEL_2)
        ClipRecordingDimmed = make_color(RED, LEVEL_2)
        Scene = make_color_from_element
        SceneTriggered = make_color(GREEN, LEVEL_3)
        NoScene = BasicColors.OFF
        StopClipTriggered = make_color(WHITE, LEVEL_2)
        StopClip = make_color(WHITE, LEVEL_4)
        StopClipDisabled = BasicColors.OFF
        StopAllClipsPressed = make_color(WHITE, LEVEL_4)
        StopAllClips = make_color(WHITE, LEVEL_1)
        NavigationPressed = make_color(WHITE, LEVEL_4)
        Navigation = make_color(WHITE, LEVEL_2)

    class Zooming:
        Selected = make_color(WHITE, LEVEL_4)
        Stopped = make_color(WHITE, LEVEL_2)
        Playing = make_color(GREEN, LEVEL_3)
        Empty = BasicColors.OFF

    class ClipActions:
        Delete = BasicColors.OFF
        DeletePressed = BasicColors.ON
        Double = BasicColors.OFF
        DoublePressed = BasicColors.ON
        Duplicate = BasicColors.OFF
        DuplicatePressed = BasicColors.ON
        Quantize = make_color(WHITE, LEVEL_4)
        QuantizedPressed = make_color(WHITE, LEVEL_2)

    class Device:
        On = BasicColors.ON
        Off = BasicColors.OFF
        LockOn = BasicColors.ON
        LockOff = BasicColors.OFF
        NavigationPressed = make_color(WHITE, LEVEL_4)
        Navigation = make_color(WHITE, LEVEL_2)

        class Bank:
            Selected = BasicColors.ON
            NotSelected = BasicColors.OFF
            NavigationPressed = BasicColors.ON
            Navigation = BasicColors.ON

    class Accent:
        On = BasicColors.ON
        Off = BasicColors.OFF

    class DrumGroup:
        PadEmpty = BasicColors.OFF
        PadFilled = make_color_from_element
        PadSelected = make_color(WHITE, LEVEL_3)
        PadMuted = make_color(ORANGE, LEVEL_1)
        PadMutedSelected = make_color(ORANGE, LEVEL_4)
        PadSoloed = make_color(TURQUOISE, LEVEL_1)
        PadSoloedSelected = make_color(TURQUOISE, LEVEL_4)
        PadAction = make_color(WHITE, LEVEL_4)
        ScrollPressed = make_color(WHITE, LEVEL_2)
        Scroll = make_color(WHITE, LEVEL_4)
        # Used in custom component
        Group = BasicColors.OFF
        GroupSelected = make_color(WHITE, LEVEL_4)
        GroupHasFilledPad = partial(make_keyboard_color, group = True)
        GroupHasFilledPadSelected = make_color(WHITE, LEVEL_4)
        PadPressed = make_color(WHITE, LEVEL_4)

    class SlicedSimpler:
        NoSlice = BasicColors.OFF
        SliceNotSelected = make_keyboard_color
        SliceSelected = make_color(WHITE, LEVEL_3)
        NextSlice = make_color(WHITE, LEVEL_1)
        PadAction = make_color(GREEN, LEVEL_3)
        ScrollPressed = make_color(WHITE, LEVEL_2)
        Scroll = make_color(WHITE, LEVEL_4)
        # Used in custom component
        SlicePressed = make_color(WHITE, LEVEL_4)
        Group = BasicColors.OFF
        GroupSelected = make_color(WHITE, LEVEL_4)
        GroupHasSlice = partial(make_keyboard_color, group = True)
        GroupHasSliceSelected = make_color(WHITE, LEVEL_4)

    class Keyboard:
        Note = BasicColors.OFF
        NoNote = BasicColors.OFF
        ScaleNote = make_keyboard_color
        RootNote = partial(make_keyboard_color, accent = True)
        NotePressed = make_color(WHITE, LEVEL_4)
        NoteSelected = make_color(WHITE, LEVEL_4)
        Octave = partial(make_keyboard_color, group = True)
        OctaveSelected = make_color(WHITE, LEVEL_4)
        Scroll = make_color(WHITE, LEVEL_4)
        ScrollPressed = make_color(WHITE, LEVEL_2)

    class VelocityLevels:
        Level1 = partial(make_velocity_color, level = LEVEL_1)
        Level2 = partial(make_velocity_color, level = LEVEL_1)
        Level3 = partial(make_velocity_color, level = LEVEL_2)
        Level4 = partial(make_velocity_color, level = LEVEL_3)
        Pressed = make_color(WHITE, LEVEL_4)
        Selected = make_color(WHITE, LEVEL_4)

    class Scale:
        On = make_color(VIOLET, LEVEL_3)
        Off = BasicColors.OFF

    class NoteRepeat:
        On = BasicColors.ON
        Off = BasicColors.OFF
        LockOn = BasicColors.ON
        LockOff = BasicColors.OFF
        Rate = make_color(WHITE, LEVEL_2)
        RateSelected = make_color(WHITE, LEVEL_4)

    class NoteEditor:
        NoClip = BasicColors.OFF
        StepDisabled = BasicColors.OFF
        StepEmpty = BasicColors.OFF
        StepFilled = make_color_from_element
        StepMuted = make_color(WHITE, LEVEL_1)

        class Resolution:
            Selected = make_color(WHITE, LEVEL_4)
            NotSelected = make_color(WHITE, LEVEL_2)

    class LoopSelector:
        InsideLoopSelected = make_color(WHITE, LEVEL_4)
        InsideLoop = partial(make_keyboard_color, group = True)
        OutsideLoopSelected = make_color(WHITE, LEVEL_4)
        OutsideLoop = BasicColors.OFF
        Playhead = make_color(GREEN, LEVEL_3)
        PlayheadRecord = make_color(RED, LEVEL_3)
        NavigationPressed = make_color(WHITE, LEVEL_2)
        Navigation = make_color(WHITE, LEVEL_4)

    class Clipboard:
        Empty = BasicColors.OFF
        Filled = BasicColors.ON

    class Translation:

        class Channel:
            Selected = BasicColors.ON
            NotSelected = BasicColors.OFF

MaschineSkin = Skin(MaschineLEDColors)
