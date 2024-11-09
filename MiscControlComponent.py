from ableton.v3.control_surface.component import Component
from ableton.v3.control_surface.display import Renderable
from ableton.v3.control_surface.controls import ButtonControl, StepEncoderControl
from ableton.v3.base import sign
from .Logger import logger


class MiscControlComponent(Component):
    new_audio_or_return_track_button = ButtonControl()
    new_midi_track_button = ButtonControl()
    duplicate_track_button = ButtonControl()
    delete_track_button = ButtonControl()

    select_track_encoder = StepEncoderControl(num_steps = 64)
    exclusive_arm_button = ButtonControl(color = None)
    arm_button = ButtonControl(color = None)
    _selected_track = None

    def __init__(self, name = "MiscControl", *a, **k):
        super().__init__(name, *a, **k)

    def _get_selected_track_info(self):
        selected_track = self.song.view.selected_track

        # Return True if selected track is midi or audio track
        # If track is return or master track, return False
        for index, track in enumerate(self.song.visible_tracks):
            if track == selected_track:
                return (True, index)
        
        for index, track in enumerate(self.song.return_tracks):
            if track == selected_track:
                return (False, index)

        return (False, -1)            

    @new_audio_or_return_track_button.pressed
    def _create_audio_track(self, button):
        is_normal, track_index = self._get_selected_track_info()

        if is_normal:
            self.song.create_audio_track(track_index + 1)
        else:
            self.song.create_return_track()

    @new_midi_track_button.pressed
    def _create_midi_track(self, button):
        # insert if selected track is not return nor master track
        is_normal, track_index = self._get_selected_track_info()

        if is_normal:
            self.song.create_midi_track(track_index + 1)

    @duplicate_track_button.pressed
    def _duplicate_selected_track(self, button):
        is_normal, track_index = self._get_selected_track_info()

        if is_normal:
            self.song.duplicate_track(track_index)

    @delete_track_button.pressed
    def _delete_selected_track(self, button):
        is_normal, track_index = self._get_selected_track_info()

        if is_normal and len(self.song.tracks) > 1:
            self.song.delete_track(track_index)
        elif not is_normal and track_index != -1:
            self.song.delete_return_track(track_index)

    @select_track_encoder.value
    def _on_encoder_value_changed(self, value, encoder):
        direction = int(sign(value))
        is_normal, track_index = self._get_selected_track_info()

        return_and_master_tracks = self.song.return_tracks + [self.song.master_track]
        if not is_normal and track_index == -1:
            track_index = len(return_and_master_tracks) - 1

        new_selected_track = None

        new_index = track_index + direction

        logger.info(f"is_normal = {is_normal}, track_index = {track_index}, direction = {direction}, new_index = {new_index}, len(visible_tracks) = {len(self.song.visible_tracks)}")

        if is_normal:
            if new_index >= 0 and new_index < len(self.song.visible_tracks):
                # normal track -> normal track
                new_selected_track = self.song.visible_tracks[new_index]
            elif new_index == len(self.song.visible_tracks):
                # normal track -> reutrn / master track
                new_selected_track = return_and_master_tracks[0]

        else:
            if new_index >= 0 and new_index < len(return_and_master_tracks):
                # return / master track -> return / master track
                new_selected_track = return_and_master_tracks[new_index]
            elif new_index < 0:
                # return / master track -> normal track
                new_selected_track = self.song.visible_tracks[-1]

        if new_selected_track is not None:
            self.song.view.selected_track = new_selected_track

    @exclusive_arm_button.pressed
    def _on_exclusive_arm_button_pressed(self, button):
        selected_track = self.song.view.selected_track
        selected_track.arm = not selected_track.arm
        if self.song.exclusive_arm:
            for track in self.song.tracks:
                if track.can_be_armed and track != selected_track:
                    track.arm = False

    @arm_button.pressed
    def _on_arm_button_pressed(self, button):
        selected_track = self.song.view.selected_track
        selected_track.arm = not selected_track.arm




