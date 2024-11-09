from ableton.v3.control_surface.skin import Skin, BasicColors
from ableton.v3.control_surface.elements import SimpleColor, RgbColor, create_rgb_color
from ableton.v3.live.util import liveobj_valid


# constants for making color index
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
    0: make_color(FUCHSIA, LEVEL_4), 
    1: make_color(YELLOW, LEVEL_2), 
    2: make_color(YELLOW, LEVEL_1), 
    3: make_color(YELLOW, LEVEL_4), 
    4: make_color(GREEN, LEVEL_4), 
    5: make_color(GREEN, LEVEL_3), 
    6: make_color(MINT, LEVEL_4), 
    7: make_color(CYAN, LEVEL_4), 
    8:  make_color(BLUE, LEVEL_4), 
    9:  make_color(PLUM, LEVEL_1), 
    10: make_color(PLUM, LEVEL_4), 
    11: make_color(MAGENTA, LEVEL_4), 
    12: make_color(MAGENTA, LEVEL_2), 
    13: make_color(WHITE, LEVEL_4), 

    14: make_color(RED, LEVEL_3), 
    15: make_color(ORANGE, LEVEL_3), 
    16: make_color(WARM_YELLOW, LEVEL_1), 
    17: make_color(YELLOW, LEVEL_3), 
    18: make_color(GREEN, LEVEL_4), 
    19: make_color(GREEN, LEVEL_2), 
    20: make_color(MINT, LEVEL_1), 
    21: make_color(BLUE, LEVEL_4), 
    22: make_color(CYAN, LEVEL_2), 
    23: make_color(CYAN, LEVEL_1), 
    24: make_color(VIOLET, LEVEL_2), 
    25: make_color(PURPLE, LEVEL_2), 
    26: make_color(MAGENTA, LEVEL_3), 
    27: make_color(WHITE, LEVEL_4), 

    28: make_color(MINT, LEVEL_1), 
    29: make_color(MINT, LEVEL_2), 
    30: make_color(MINT, LEVEL_3), 
    31: make_color(MINT, LEVEL_4), 
    32: make_color(CYAN, LEVEL_1), 
    33: make_color(CYAN, LEVEL_2), 
    34: make_color(CYAN, LEVEL_3), 
    35: make_color(CYAN, LEVEL_4), 
    36: make_color(TURQUOISE, LEVEL_1), 
    37: make_color(TURQUOISE, LEVEL_2), 
    38: make_color(TURQUOISE, LEVEL_3), 
    39: make_color(TURQUOISE, LEVEL_4), 
    40: make_color(BLUE, LEVEL_1), 
    41: make_color(BLUE, LEVEL_2), 

    42: make_color(BLUE, LEVEL_3), 
    43: make_color(BLUE, LEVEL_4), 
    44: make_color(PLUM, LEVEL_1), 
    45: make_color(PLUM, LEVEL_2), 
    46: make_color(PLUM, LEVEL_3), 
    47: make_color(PLUM, LEVEL_4), 
    48: make_color(VIOLET, LEVEL_1), 
    49: make_color(VIOLET, LEVEL_2), 
    50: make_color(VIOLET, LEVEL_3), 
    51: make_color(VIOLET, LEVEL_4), 
    52: make_color(PURPLE, LEVEL_1), 
    53: make_color(PURPLE, LEVEL_2), 
    54: make_color(PURPLE, LEVEL_3), 
    55: make_color(PURPLE, LEVEL_4), 

    56: make_color(MAGENTA, LEVEL_1), 
    57: make_color(MAGENTA, LEVEL_2), 
    58: make_color(MAGENTA, LEVEL_3), 
    59: make_color(MAGENTA, LEVEL_4), 
    60: make_color(FUCHSIA, LEVEL_1), 
    61: make_color(FUCHSIA, LEVEL_2), 
    62: make_color(FUCHSIA, LEVEL_3), 
    63: make_color(FUCHSIA, LEVEL_4), 
    64: make_color(WHITE, LEVEL_1), 
    65: make_color(WHITE, LEVEL_2), 
    66: make_color(WHITE, LEVEL_3), 
    67: make_color(WHITE, LEVEL_4), 
    68: make_color(WHITE, LEVEL_1), 
    69: make_color(WHITE, LEVEL_2)
}

def make_color_from_element(element):
    if liveobj_valid(element):
        if element.color_index is not None:
            return LIVE_COLOR_MAP.get(element.color_index, BasicColors.OFF)
    return BasicColors.OFF


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
        SeekPressed = BasicColors.ON
        Seek = BasicColors.OFF
        CanReEnableAutomation = BasicColors.ON
        CanCaptureMidi = BasicColors.ON
        CanJumpToCue = BasicColors.ON
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
        Scene = make_color(WHITE, LEVEL_2)
        SceneTriggered = make_color(WHITE, LEVEL_4)
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
        Stopped = make_color(WHITE, LEVEL_1)
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
        NavigationPressed = BasicColors.ON
        Navigation = BasicColors.OFF

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
        PadSelected = make_color(WHITE, LEVEL_2)
        PadMuted = make_color(ORANGE, LEVEL_1)
        PadMutedSelected = make_color(ORANGE, LEVEL_4)
        PadSoloed = make_color(TURQUOISE, LEVEL_1)
        PadSoloedSelected = make_color(TURQUOISE, LEVEL_4)
        PadAction = make_color(WHITE, LEVEL_4)
        ScrollPressed = BasicColors.ON
        Scroll = BasicColors.ON
        # Used in custom component
        Group = BasicColors.OFF
        GroupSelected = make_color(WHITE, LEVEL_4)
        GroupHasFilledPad = make_color(WHITE, LEVEL_2)
        GroupHasFilledPadSelected = make_color(WHITE, LEVEL_4)

    class SlicedSimpler:
        NoSlice = BasicColors.OFF
        SliceNotSelected = make_color(WHITE, LEVEL_2)
        SliceSelected = make_color(WHITE, LEVEL_4)
        NextSlice = make_color(WHITE, LEVEL_1)
        PadAction = make_color(GREEN, LEVEL_3)
        ScrollPressed = BasicColors.ON
        Scroll = BasicColors.OFF
        # Used in custom component
        Group = BasicColors.OFF
        GroupSelected = make_color(WHITE, LEVEL_4)
        GroupHasSlice = make_color(WHITE, LEVEL_2)
        GroupHasSliceSelected = make_color(WHITE, LEVEL_4)


    class Keyboard:
        Note = BasicColors.OFF
        NoNote = BasicColors.OFF
        ScaleNote = make_color(WHITE, LEVEL_1)
        RootNote = make_color(WHITE, LEVEL_3)
        NotePressed = make_color(WHITE, LEVEL_4)
        Octave = make_color(WHITE, LEVEL_1)
        OctaveSelected = make_color(WHITE, LEVEL_4)

    class Scale:
        On = make_color(PURPLE, LEVEL_3)
        Off = BasicColors.OFF

    class NoteEditor:
        NoClip = BasicColors.OFF
        StepDisabled = BasicColors.OFF
        StepEmpty = BasicColors.OFF
        StepFilled = make_color(WHITE, LEVEL_3)
        StepMuted = make_color(WHITE, LEVEL_1)

        class Resolution:
            Selected = BasicColors.ON
            NotSelected = BasicColors.OFF

    class LoopSelector:
        InsideLoopSelected = make_color(WHITE, LEVEL_4)
        InsideLoop = make_color(WHITE, LEVEL_2)
        OutsideLoopSelected = make_color(WHITE, LEVEL_3)
        OutsideLoop = BasicColors.OFF
        Playhead = make_color(GREEN, LEVEL_3)
        PlayheadRecord = make_color(RED, LEVEL_3)
        NavigationPressed = make_color(WHITE, LEVEL_4)
        Navigation = make_color(WHITE, LEVEL_2)

    class Clipboard:
        Empty = BasicColors.OFF
        Filled = BasicColors.ON

    class Translation:

        class Channel:
            Selected = BasicColors.ON
            NotSelected = BasicColors.OFF

MaschineSkin = Skin(MaschineLEDColors)
