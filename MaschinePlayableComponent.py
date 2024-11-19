from itertools import product
from ableton.v3.control_surface.components import (
    PlayableComponent,
    ScrollComponent,
    Scrollable,
    PitchProvider
)

from ableton.v3.control_surface.display import Renderable

from ableton.v3.control_surface.controls import (
    ButtonControl,
    EncoderControl,
    TouchControl,
    MappedControl,
    SendValueInputControl,
    SendValueEncoderControl,
    PlayableControl,
    control_matrix
)

from ableton.v3.control_surface import ScriptForwarding

from ableton.v3.base import (
    listens,
    depends,
    listenable_property,
    task
)

from ableton.v3.control_surface.skin import LiveObjSkinEntry

from .Logger import logger
#from ableton.v3.base import 

MODE_PLAYABLE = 0
MODE_LISTENABLE = 1
MODE_PLAYABLE_LISTENABLE = 2

# This control class is just for bypass pitch bend message
class PlayableEncoderControl(SendValueEncoderControl):

    class State(SendValueEncoderControl.State):

        def __init__(self, mode = None, *a, **k):
            super().__init__(*a, **k)
            self._enabled = True
            self._mode = MODE_PLAYABLE if mode == None else mode
            self._mode_to_forwarding = {
                MODE_PLAYABLE: ScriptForwarding.none, 
                MODE_LISTENABLE: ScriptForwarding.exclusive, 
                MODE_PLAYABLE_LISTENABLE: ScriptForwarding.non_consuming}
            

        def set_control_element(self, control_element):
            logger.info(f"set_control_element element = {control_element}")
            super().set_control_element(control_element)
            self._update_script_forwarding()
            if control_element != None:
                control_element.send_value(self.value, True)


        def _update_script_forwarding(self):
            if self._control_element:
                if self._enabled:
                    self._control_element.script_forwarding = self._mode_to_forwarding[self._mode]

        def set_mode(self, value):
            self._mode = value
            self._update_script_forwarding()

        def _notifications_enabled(self):
            return super()._notifications_enabled()
        
        def _notify_encoder_value(self, value, *a, **k):
            self._call_listener("value", value)
            self.connected_property_value = value


class MaschinePlayableComponent(PlayableComponent, ScrollComponent, PitchProvider, Renderable):
    octave_select_buttons = control_matrix(ButtonControl, color = "Keyboard.Octave", on_color = "Keyboard.OctaveSelected")
    octave_up_button = ButtonControl()
    octave_down_button = ButtonControl()
    semitone_up_button = ButtonControl()
    semitone_down_button = ButtonControl()
    scale_mode_button = ButtonControl()
    pitchbend_encoder = PlayableEncoderControl()
    pitchbend_reset = PlayableEncoderControl()
    modulation_encoder = EncoderControl()

    _scale_notes_only = False
    _root_note = 0
    _intervals = list(range(0, 12))
    _octave_root_notes = list(range(0, 128, 12))
    _octave_notes_count = 12
    _all_scale_notes = list(range(128))
    _all_chromatic_scale_notes = list(range(128))
    _select_start_octave = 2
    _position = 60
    _target_track = None

    @property
    def position(self):
        return self._position
    
    @position.setter
    def position(self, pos):
        if self._position != pos:
            self._position = pos
            self._update_note_translations()
            #self._update_scroll_buttons()
            ScrollComponent.update(self)
            self._update_led_feedback()

    @property
    def available_notes(self):
        if self._scale_notes_only:
            return self._all_scale_notes
        else:
            return self._all_chromatic_scale_notes

    @depends(target_track = None)
    def __init__(self, name = 'MaschinePlayable', matrix_always_listenable = True, target_track = None, *a, **k):
        super().__init__(name, matrix_always_listenable, *a, **k)
        self._target_track = target_track
        self.pitchbend_encoder.value = 8192
        self.register_slot(self.song, self._scale_root_note_changed, "root_note")
        self.register_slot(self.song, self._scale_intervals_changed, "scale_intervals")
        self.register_slot(self.song, self._scale_mode_changed, "scale_mode")
        self.register_slot(self.select_button, self._on_select_button_pressed, "is_pressed")
        self._on_target_track_changed.subject = self._target_track
        self._update_scale_and_adjust_position(True)
        self.pitches = [self.available_notes[self.position]]

    def set_matrix(self, matrix):
        first_pad_note = self.available_notes[self.position]
        changed = self._update_scale_info()
        if changed:
            self._adjust_position(first_pad_note)
        super().set_matrix(matrix)
        for button in self.matrix:
            button.set_mode(PlayableControl.Mode.playable_and_listenable)

    def update(self):
        super().update()
        first_pad_note = self.available_notes[self.position]
        self._update_scale_info()
        self._adjust_position(first_pad_note)
        self._update_led_feedback()

    def _on_matrix_pressed(self, target_button):
        if self._takeover_pads:
            for button in self.matrix:
                if button == target_button:
                    pitch, _ = self._note_translation_for_button(button)
                    self.pitches = [pitch]

    def _on_matrix_released(self, button):
        super()._on_matrix_released(button)
        self._update_button_color(button)

    def _note_translation_for_button(self, button):
        row, column = button.coordinate
        inverted_row = self.height - row - 1
        pad_index = inverted_row * self.width + column
        notes = self.available_notes
        target_note = notes[min(self.position + pad_index, len(notes) - 1)]
        return (target_note, 1)
        #return super()._note_translation_for_button(button)
    
    def _update_led_feedback(self):
        notes = self.available_notes
        for button in self.matrix:
            row, column = button.coordinate
            inverted_row = self.height - row - 1
            note_index = self.position + (inverted_row * self.width + column)

            new_color = "Keyboard.NoNote"
            if note_index < len(notes):
                note = notes[note_index]
                if note in self._octave_root_notes:
                    new_color = "Keyboard.RootNote"
                elif note in self._all_scale_notes:
                    new_color = "Keyboard.ScaleNote"
                else:
                    new_color = "Keyboard.Note"

            button.color = LiveObjSkinEntry(new_color, self._target_track.target_track)
            button.pressed_color = LiveObjSkinEntry("Keyboard.NotePressed", self._target_track.target_track)

        selectable_octaves = self._octave_root_notes[self._select_start_octave : self._select_start_octave + 8]
        first_note = self.available_notes[self.position]
        selected_octave = list(filter(lambda note: note + (self._octave_notes_count - 1) - first_note >= 0, selectable_octaves))

        selected_index = self._find_note_index(selectable_octaves, selected_octave[0]) if len(selected_octave) > 0 else -1

        logger.info(f"Selected index {selected_octave}")

        for button in self.octave_select_buttons:
            row, column = button.coordinate
            index = row * self.width + column

            #button.is_on = index == selected_index
            if index == selected_index:
                button.color = LiveObjSkinEntry("Keyboard.OctaveSelected", self._target_track.target_track)
            else:
                button.color = LiveObjSkinEntry("Keyboard.Octave", self._target_track.target_track)

    def can_scroll_up(self):
        visible_notes_count = self.width * self.height
        return self.position + visible_notes_count < len(self.available_notes)
    
    def can_scroll_down(self):
        return 0 < self.position
    
    def scroll_up(self):
        self.position -= self._octave_notes_count
    
    def scroll_down(self):
        self.position += self._octave_notes_count
    
    @semitone_down_button.pressed
    def _on_semitone_down_pressed(self, button):
        self.position -= 1

    @semitone_up_button.pressed
    def _on_semitone_up_pressed(self, button):
        self.position += 1

    @octave_down_button.pressed
    def _on_octave_down_pressed(self, button):
        self.position -= self._octave_notes_count if self._scale_notes_only else 12

    @octave_up_button.pressed
    def _on_octave_up_pressed(self, button):
        self.position += self._octave_notes_count if self._scale_notes_only else 12

    @octave_select_buttons.pressed
    def _on_octave_select_buttons_pressed(self, target_button):
        for button in self.octave_select_buttons:
            if button == target_button:
                row, column = button.coordinate
                base_note = self._octave_root_notes[self._select_start_octave + row * self.width + column]
                self.position = self._find_note_index(self.available_notes, base_note)

    def _on_select_button_pressed(self):
        logger.info("Select button pressed in keyboard mode")

    def _find_note_index(self, note_list, target_note):
        for index, note in enumerate(note_list):
            if note == target_note:
                return index

        return -1
    
    def _scale_root_note_changed(self):
        self._update_scale_and_adjust_position(True)

    def _scale_intervals_changed(self):
        self._update_scale_and_adjust_position(True)

    def _scale_mode_changed(self):
        self._update_scale_and_adjust_position(True)

    def _update_scale_and_adjust_position(self, root_changed = False):
        first_pad_note = self.available_notes[self.position]
        logger.info(f"first pad note = {first_pad_note}")
        changed = self._update_scale_info()
        if changed:
            self._adjust_position(first_pad_note, root_changed)
        self._update_note_translations()
        self._update_led_feedback()

    def _update_scale_info(self):
        if self._scale_notes_only != self.song.scale_mode or self._root_note != self.song.root_note or self._intervals != self.song.scale_intervals:
            self._scale_notes_only = self.song.scale_mode
            self._root_note = self.song.root_note
            self._intervals = [note for note in self.song.scale_intervals]
            self._all_scale_notes = []

            octaves = [octave + self._root_note for octave in range(-12, 12 * 11, 12)]
            self._octave_notes_count = len(self._intervals)

            self._octave_root_notes = list(filter(lambda note: note >= 0 and note < 128, octaves))
            
            for octave in octaves:
                octave_notes = filter(lambda note: note >= 0 and note < 128, (octave + interval for interval in self._intervals))
                self._all_scale_notes += list(octave_notes)

            logger.info(f"Scale mode = {self.song.scale_mode}")
            logger.info(f"Root note = {self.song.root_note}, Name = {self.song.scale_name}, Intervals = {self.song.scale_intervals}")
            logger.info(f"All scale notes = {self._all_scale_notes}")
            logger.info(f"Octave root notes = {self._octave_root_notes}")

            return True
        else:
            logger.info("Scale unchanged")
            logger.info(f"Scale mode = {self.song.scale_mode}")
            logger.info(f"Root note = {self.song.root_note}, Name = {self.song.scale_name}, Intervals = {self.song.scale_intervals}")
            logger.info(f"All scale notes = {self._all_scale_notes}")
            logger.info(f"Octave root notes = {self._octave_root_notes}")
            return False

    def _adjust_position(self, first_pad_note, root_note_only = False):
        # Adjust scroll position near to previous first pad note
        nearest_note = 0

        for note in (self._octave_root_notes if root_note_only else self.available_notes):
            if abs(note - first_pad_note) < abs(nearest_note - first_pad_note):
                nearest_note = note

        self.position = self._find_note_index(self.available_notes, nearest_note)
        
    @modulation_encoder.value
    def _on_modulation_encoder(self, value, control):
        logger.info(f"Modulation encoder value = {value}")

    @listens("target_track")
    def _on_target_track_changed(self):
        self._on_track_color_changed.subject = self._target_track.target_track
        self._update_led_feedback()

    @listens("color_index")
    def _on_track_color_changed(self):
        self._update_led_feedback()

