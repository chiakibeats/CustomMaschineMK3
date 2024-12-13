from ableton.v3.control_surface.component import Component
from ableton.v3.control_surface.display import Renderable
from ableton.v3.control_surface.controls import (
    StepEncoderControl,
    ButtonControl,
    MappedSensitivitySettingControl,
    control_list
)
from ableton.v3.base import clamp, depends, listens, listenable_property
from Live.Browser import BrowserItem # type: ignore

from .Logger import logger

COLLECTION_COLORS = ["Red", "Orange", "Yellow", "Green", "Blue", "Purple", "Gray"]

class BrowserCollectionRootItem:
    name = "Collections"
    children = []
    is_folder = True
    is_device = False
    is_loadable = False
    uri = ""

    def __init__(self, browser):
        self.uri = type(self).__name__
        self.children = []
        for item in browser.colors:
            self.children.append(item)

class BrowserUserFoldersRootItem:
    name = "User Files"
    children = []
    is_folder = True
    is_device = False
    is_loadable = False
    uri = ""

    def __init__(self, browser):
        self.uri = type(self).__name__
        self.children = []
        for item in browser.user_folders:
            self.children.append(item)

class BrowserRootItem:
    name = "Browser Top"
    children = []
    is_folder = True
    is_device = False
    is_loadable = False
    uri = ""

    def __init__(self, browser, target_is_midi_track = True):
        self.uri = type(self).__name__
        self.children = [BrowserCollectionRootItem(browser)]
        if target_is_midi_track:
            self.children.append(browser.sounds)
            self.children.append(browser.drums)
            self.children.append(browser.instruments)
            self.children.append(browser.audio_effects)
            self.children.append(browser.midi_effects)
        else:
            self.children.append(browser.audio_effects)

        self.children += [browser.max_for_live,
            browser.plugins,
            browser.packs,
            browser.current_project,
            BrowserUserFoldersRootItem(browser)]

class BrowserComponent(Component, Renderable):
    select_encoder = StepEncoderControl(num_steps = 64)
    load_button = ButtonControl(color = None)
    enter_folder_button = ButtonControl(color = "DefaultButton.Off", on_color = "DefaultButton.On")
    leave_folder_button = ButtonControl(color = "DefaultButton.Off", on_color = "DefaultButton.On")
    preview_toggle_button = ButtonControl(color = "DefaultButton.Off", on_color = "DefaultButton.On")
    preview_volume_encoder = MappedSensitivitySettingControl()
    select_folder_buttons = control_list(ButtonControl, color = "DefaultButton.Off", on_color = "DefaultButton.On")

    _selected_item_index = 0
    _preview_enabled = True
    _parent_folder = None
    _root_item = None
    _folder_stack = []
    _browser = None
    _target_track = None

    @listenable_property
    def selected_item(self):
        if len(self.parent_folder.children) > 0:
            return self.parent_folder.children[self._selected_item_index]
        else:
            return None
    
    @listenable_property
    def parent_folder(self):
        return self._parent_folder
    
    @parent_folder.setter
    def parent_folder(self, folder):
        self._parent_folder = folder
        self.notify_parent_folder()

    @depends(target_track = None)
    def __init__(self, name = "Browser", target_track = None, *a, **k):
        super().__init__(name, *a, **k)
        self._target_track = target_track
        self._browser = self.application.browser
        self._root_item = BrowserRootItem(self._browser)
        self.enter_folder(self._root_item)
        self.preview_volume_encoder.mapped_parameter = self.song.master_track.mixer_device.cue_volume
        self._update_preview_state(True)
        
        # for item in self.application.browser.max_for_live.children:
        #     logger.info(f"name = {item.name}, children = {item.children}, is_device = {item.is_device}, is_folder = {item.is_folder}, is_loadable = {item.is_loadable}, uri = {item.uri}")
 
        # for item in self.application.browser.max_for_live.children.iter_children:
        #     logger.info(f"name = {item.name}, children = {item.children}, is_device = {item.is_device}, is_folder = {item.is_folder}, is_loadable = {item.is_loadable}, uri = {item.uri}")

        # for folder in browser.user_folders:
        #     logger.info(f"user folder name = {folder.name}, uri = {folder.uri}")
        #     for item in folder.children:
        #         logger.info(f"item name = {item.name}, uri = {item.uri}")

    def _update_folder_stack(self, new_root_item, current_stack):
        # Update stack items based on its URI
        # If matched item didn't find, stop searching and select first item of current folder instead
        new_stack = [new_root_item]
        for old_item in current_stack[1:]:
            matched_item = None

            folder = new_stack[-1]
            for new_item in folder.children:
                if new_item.uri == old_item.uri:
                    matched_item = new_item
                    break

            if matched_item != None:
                new_stack.append(matched_item)
            else:
                break
        
        return new_stack

    def _update_browser_items(self):
        current_selected_item = self.selected_item
        new_root_item = BrowserRootItem(self._browser, self._target_track.target_track.has_midi_input)
        new_folder_stack = self._update_folder_stack(new_root_item, self._folder_stack)

        new_selected_index = 0
        if len(new_folder_stack[-1].children) > 0 and current_selected_item != None:
            for index, item in enumerate(new_folder_stack[-1].children):
                if item.uri == current_selected_item.uri:
                    new_selected_index = index
                    break

        self._root_item = new_root_item
        self._folder_stack = new_folder_stack
        self._selected_item_index = new_selected_index
        self.notify_parent_folder()
        self.notify_selected_item()

    def update(self):
        super().update()
        self._update_browser_items()

    def _set_item_index(self, new_index, force_preview = False):
        old_index = self._selected_item_index
        self._selected_item_index = new_index
        logger.info(f"Select item {self.selected_item.name if self.selected_item else None}")
        self.notify_selected_item()
        if self._preview_enabled and (old_index != new_index or force_preview):
            self._browser.stop_preview()
            preview_item = self.selected_item
            if isinstance(preview_item, BrowserItem):
                self._browser.preview_item(preview_item)

    def enter_folder(self, folder):
        self._folder_stack.append(folder)
        self.parent_folder = folder
        self._set_item_index(0, True)

    def leave_folder(self):
        if len(self._folder_stack) > 1:
            last_item = self._folder_stack[-1]
            self._folder_stack.pop()
            self.parent_folder = self._folder_stack[-1]
            item_index = 0
            for index, item in enumerate(self.parent_folder.children):
                if item.uri == last_item.uri:
                    item_index = index
                    break

            self._set_item_index(item_index, True)

    def _update_preview_state(self, new_state):
        self._preview_enabled = new_state
        self.preview_toggle_button.is_on = self._preview_enabled
        if self._preview_enabled:
            preview_item = self.selected_item 
            if isinstance(preview_item, BrowserItem):
                self._browser.preview_item(preview_item)
        else:
            self._browser.stop_preview()

    @select_encoder.value
    def _on_select_encoder_value(self, value, encoder):
        new_index = self._selected_item_index + value
        new_index = clamp(new_index, 0, len(self.parent_folder.children) - 1)
        self._set_item_index(new_index)

    @load_button.pressed
    def _on_load_button_pressed(self, button):
        item = self.selected_item
        if item != None:
            if item.is_loadable:
                logger.info(f"Load item {self.selected_item.name}")
                self.application.browser.load_item(self.selected_item)
            elif item.is_folder or len(item.children) > 0:
                self.enter_folder(item)

    @enter_folder_button.pressed
    def _on_enter_folder_button_pressed(self, button):
        item = self.selected_item
        if item != None and (item.is_folder or len(item.children) > 0):
            self.enter_folder(item)

    @leave_folder_button.pressed
    def _on_leave_folder_button_pressed(self, button):
        self.leave_folder()

    @preview_toggle_button.pressed
    def _on_preview_toggle_button_pressed(self, button):
        self._update_preview_state(not self._preview_enabled)
                
    @select_folder_buttons.pressed
    def _on_folder_buttons_pressed(self, button):
        if button.index == 0:
            self.parent_folder = self._root_item
            self._folder_stack = [self._root_item]
        else:
            for item in self._root_item.children:
                if isinstance(item, BrowserCollectionRootItem):
                    self.parent_folder = item.children[min(button.index - 1, len(item.children) - 1)]
                    self._folder_stack = [self._root_item, self.parent_folder]
                    break
        
        logger.info(f"Select folder {self.parent_folder.name}")
        self._set_item_index(0, True)
        

        