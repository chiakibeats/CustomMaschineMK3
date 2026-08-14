# ==================================================
#
# This file is part of CustomMaschineMK3.
# CustomMaschineMK3 is free software licensed under GPL-3.0.
# For more details, see "LICENSE" file.
# 
# Copyright (C) 2024-2025 chiaki
#
# ==================================================

from ableton.v3.control_surface.component import Component
from ableton.v3.control_surface.display import Renderable
from ableton.v3.control_surface.controls import ButtonControl, StepEncoderControl
from ableton.v3.base import sign, clamp
from .logger import logger


class MiscControlComponent(Component):
    """
    Miscellaneous operations for audio, MIDI, and return tracks.
    """
    new_audio_or_return_track_button = ButtonControl()
    new_midi_track_button = ButtonControl()
    duplicate_track_button = ButtonControl()
    delete_track_button = ButtonControl()

    select_track_encoder = StepEncoderControl(num_steps = 64)
    exclusive_arm_button = ButtonControl(color = None)
    arm_button = ButtonControl(color = None)

    def __init__(self, name = "Misc_Control", *a, **k):
        super().__init__(name, *a, **k)

    def _get_all_tracks(self):
        all_tracks = []
        all_tracks += self.song.visible_tracks
        all_tracks += self.song.return_tracks
        all_tracks.append(self.song.master_track)
        return all_tracks

    def _get_track_index(self, track_list, target_track):
        """
        Get track index of specified track.

        Args:
            track_list(list): List of all tracks.
            target_track(Live.Track.Track): Target track to find.

        Returns:
            int: Track index of `target_track`.
        """
        for index, track in enumerate(track_list):
            if track == target_track:
                return index

        # In case of track is not found.
        return -1

    @new_audio_or_return_track_button.pressed
    def _create_audio_track(self, button):
        all_tracks = self._get_all_tracks()
        track_index = self._get_track_index(all_tracks, self.song.view.selected_track)

        if track_index < len(self.song.visible_tracks):
            self.song.create_audio_track(track_index + 1)
        else:
            self.song.create_return_track()

    @new_midi_track_button.pressed
    def _create_midi_track(self, button):
        all_tracks = self._get_all_tracks()
        track_index = self._get_track_index(all_tracks, self.song.view.selected_track)

        if track_index < len(self.song.visible_tracks):
            self.song.create_midi_track(track_index + 1)

    @duplicate_track_button.pressed
    def _duplicate_selected_track(self, button):
        all_tracks = self._get_all_tracks()
        track_index = self._get_track_index(all_tracks, self.song.view.selected_track)

        if track_index < len(self.song.visible_tracks):
            self.song.duplicate_track(track_index)

    @delete_track_button.pressed
    def _delete_selected_track(self, button):
        all_tracks = self._get_all_tracks()
        track_index = self._get_track_index(all_tracks, self.song.view.selected_track)

        normal_track_count = len(self.song.visible_tracks)
        return_track_count = len(self.song.return_tracks)

        logger.info(f"Delete track index = {track_index}, Total = {len(all_tracks)}, Normal = {normal_track_count}, Return = {return_track_count}")
        if normal_track_count > 1 and track_index < normal_track_count:
            self.song.delete_track(track_index)
        elif return_track_count > 0 and normal_track_count <= track_index < normal_track_count + return_track_count:
            self.song.delete_return_track(track_index - normal_track_count)

    @select_track_encoder.value
    def _on_encoder_value_changed(self, value, encoder):
        """Scroll around between normal, return, and master tracks."""
        all_tracks = self._get_all_tracks()
        all_track_count = len(all_tracks)
        selected_index = self._get_track_index(all_tracks, self.song.view.selected_track)

        logger.info(f"Total tracks = {all_track_count}, Selected index = {selected_index}, Offset = {value}")

        new_selected_index = clamp(selected_index + value, 0, all_track_count - 1)
        self.song.view.selected_track = all_tracks[new_selected_index]

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
