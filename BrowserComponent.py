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
from . import Config

COLLECTION_COLORS = ["Red", "Orange", "Yellow", "Green", "Blue", "Purple", "Gray"]

class BrowserCollectionRootItem:

    def __init__(self, browser):
        self.name = "Collections"
        self.children = []
        self.is_folder = True
        self.is_device = False
        self.is_loadable = False
        self.uri = type(self).__name__

        for item in browser.colors:
            self.children.append(item)

class BrowserUserFoldersRootItem:

    def __init__(self, browser):
        self.name = "User Files"
        self.children = []
        self.is_folder = True
        self.is_device = False
        self.is_loadable = False
        self.uri = type(self).__name__

        for item in browser.user_folders:
            self.children.append(item)

class WrapBrowserItem:
    
    def __init__(self, item, name):
        self._wrapped_item = item
        self._name = name
    
    @property
    def children(self):
        return self._wrapped_item.children

    @property
    def is_device(self):
        return self._wrapped_item.is_device

    @property
    def is_folder(self):
        return self._wrapped_item.is_folder

    @property
    def is_loadable(self):
        return self._wrapped_item.is_loadable

    @property
    def is_selected(self):
        return self._wrapped_item.is_selected

    @property
    def iter_children(self):
        return self._wrapped_item.iter_children

    @property
    def name(self):
        return self._name

    @property
    def source(self):
        return self._wrapped_item.source

    @property
    def uri(self):
        return self._wrapped_item.uri

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
        audio_effects = WrapBrowserItem(browser.audio_effects, "Audio Effects")
        if target_is_midi_track:
            self.children.append(WrapBrowserItem(browser.sounds, "Sounds"))
            self.children.append(WrapBrowserItem(browser.drums, "Drums"))
            self.children.append(WrapBrowserItem(browser.instruments, "Instruments"))
            self.children.append(audio_effects)
            self.children.append(WrapBrowserItem(browser.midi_effects, "MIDI Effects"))
        else:
            self.children.append(audio_effects)

        self.children += [browser.max_for_live,
            WrapBrowserItem(browser.plugins, "Plug-Ins"),
            browser.packs,
            WrapBrowserItem(browser.current_project, "Current Project"),
            BrowserUserFoldersRootItem(browser)]

class BrowserComponent(Component, Renderable):
    select_encoder = StepEncoderControl(num_steps = 64)
    load_button = ButtonControl(color = None)
    enter_folder_button = ButtonControl(color = "Browser.CannotNavigateFolder", on_color = "Browser.CanNavigateFolder", pressed_color = "Browser.NavigateFolderPressed")
    leave_folder_button = ButtonControl(color = "Browser.CannotNavigateFolder", on_color = "Browser.CanNavigateFolder", pressed_color = "Browser.NavigateFolderPressed")
    jump_next_button = ButtonControl(color = "Browser.CannotNavigateItem", on_color = "Browser.CanNavigateItem", pressed_color = "Browser.NavigateItemPressed", repeat = True)
    jump_prev_button = ButtonControl(color = "Browser.CannotNavigateItem", on_color = "Browser.CanNavigateItem", pressed_color = "Browser.NavigateItemPressed", repeat = True)
    preview_toggle_button = ButtonControl(color = "Browser.PreviewOff", on_color = "Browser.PreviewOn")
    preview_volume_encoder = MappedSensitivitySettingControl()
    select_folder_buttons = control_list(ButtonControl)

    _selected_item_index = 0
    _selected_item_name = None
    _preview_enabled = True
    _parent_folder = None
    _parent_folder_name = None
    _root_item = None
    _folder_stack = []
    _browser = None
    _target_track = None

    @property
    def selected_item(self):
        if len(self.parent_folder.children) > 0:
            return self.parent_folder.children[self._selected_item_index]
        else:
            return None
        
    @listenable_property
    def selected_item_name(self):
        return self._selected_item_name
    
    @property
    def parent_folder(self):
        return self._parent_folder
    
    @parent_folder.setter
    def parent_folder(self, folder):
        self._parent_folder = folder
        self._parent_folder_name = folder.name
        self.notify_parent_folder_name()

    @listenable_property
    def parent_folder_name(self):
        return self._parent_folder_name

    @depends(target_track = None)
    def __init__(self, name = "Browser", target_track = None, *a, **k):
        super().__init__(name, *a, **k)
        self._target_track = target_track
        self._browser = self.application.browser
        self._root_item = BrowserRootItem(self._browser)
        self.enter_folder(self._root_item)
        self.preview_volume_encoder.mapped_parameter = self.song.master_track.mixer_device.cue_volume
        self._update_preview_state(True)
        self._update_led_feedback()

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
        # We have to scan library folders periodcally because not all items listed at startup.
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
        self.parent_folder = self._folder_stack[-1]
        self._set_item_index(new_selected_index)

    def update(self):
        super().update()
        self._update_browser_items()
        self._update_led_feedback()

    def _set_item_index(self, new_index, force_preview = False):
        old_index = self._selected_item_index
        self._selected_item_index = new_index
        self._selected_item_name = self.selected_item.name if self.selected_item else None
        logger.info(f"Select item {self._selected_item_name}")
        self.notify_selected_item_name()

        # Preview item function is blocking call (time depends on sample length and storage bandwidth)
        # We need to finish other tasks before item preview
        if self._preview_enabled and (old_index != new_index or force_preview):
            self._browser.stop_preview()
            preview_item = self.selected_item
            if isinstance(preview_item, BrowserItem):
                self._browser.preview_item(preview_item)

    def enter_folder(self, folder):
        self._folder_stack.append(folder)
        self.parent_folder = folder
        self._set_item_index(0, True)
        self._update_led_feedback()

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
        
        self._update_led_feedback()

    def _update_preview_state(self, new_state):
        self._preview_enabled = new_state
        if self._preview_enabled:
            preview_item = self.selected_item 
            if isinstance(preview_item, BrowserItem):
                self._browser.preview_item(preview_item)
        else:
            self._browser.stop_preview()
        
        self._update_led_feedback()

    def _update_led_feedback(self):
        item = self.selected_item
        can_enter = False if item == None else item.is_folder or len(item.children) > 0
        self.enter_folder_button.is_on = can_enter
        self.leave_folder_button.is_on = len(self._folder_stack) > 1
        self.jump_next_button.is_on = self._selected_item_index < len(self.parent_folder.children) - 1
        self.jump_prev_button.is_on = self._selected_item_index > 0
        self.preview_toggle_button.is_on = self._preview_enabled

    @select_encoder.value
    def _on_select_encoder_value(self, value, encoder):
        new_index = clamp(self._selected_item_index + value, 0, len(self.parent_folder.children) - 1)
        self._set_item_index(new_index)
        self._update_led_feedback()

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

    @jump_next_button.pressed
    def _on_jump_next_button_pressed(self, button):
        new_index = clamp(self._selected_item_index + Config.SKIP_ITEM_COUNT, 0, len(self.parent_folder.children) - 1)
        self._set_item_index(new_index)
        self._update_led_feedback()

    @jump_prev_button.pressed
    def _on_jump_prev_button_pressed(self, button):
        new_index = clamp(self._selected_item_index - Config.SKIP_ITEM_COUNT, 0, len(self.parent_folder.children) - 1)
        self._set_item_index(new_index)
        self._update_led_feedback()

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
     