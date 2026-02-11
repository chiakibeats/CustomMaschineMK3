# ==================================================
#
# This file is part of CustomMaschineMK3.
# CustomMaschineMK3 is free software licensed under GPL-3.0.
# For more details, see "LICENSE" file.
# 
# Copyright (C) 2024-2025 chiaki
#
# ==================================================

import math
from ableton.v3.control_surface.component import Component
from ableton.v3.control_surface.display import Renderable
from ableton.v3.control_surface.mode import pop_last_mode
from ableton.v3.control_surface.controls import (
    StepEncoderControl,
    ButtonControl,
    MappedSensitivitySettingControl,
    control_list
)
from ableton.v3.base import clamp, depends, listens, listenable_property, task
from ableton.v3.live import liveobj_valid
from Live.Browser import BrowserItem # type: ignore
from Live.Device import Device # type: ignore
from Live.Sample import Sample # type: ignore
from Live.DrumPad import DrumPad # type: ignore

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
    is_folder = True
    is_device = False
    is_loadable = False

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


class BrowserTreeExplorer:

    @property
    def selected_item(self):
        return self._selected_item
    
    @property
    def selected_item_index(self):
        return self._selected_item_index
    
    @property
    def parent_item(self):
        return self._tree_stack[-1]
    
    @property
    def item_count(self):
        return self._tree_item_count
    
    @property
    def tree_depth(self):
        return len(self._tree_stack)

    def __init__(self, root_item):
        self._selected_item = root_item.children[0]
        self._selected_item_index = 0
        self._root_item = root_item
        # TODO: store URI for accurate traverse (items has identical name can be in same folder)
        self._tree_stack = [root_item]
        self._tree_item_count = len(self._tree_stack[-1].children)
    
    def set_root_item(self, new_root):
        self._root_item = new_root
        self.traverse_tree(self._root_item, self._selected_item)

    def enter_to_selected_item(self):
        # Cache item count to eliminate expensive operation
        item_count = len(self._selected_item.children)

        if self._selected_item.is_folder or item_count > 0:
            self._tree_stack.append(self._selected_item)
            self._tree_item_count = item_count
            if item_count == 0:
                self._selected_item = None
            else:
                self._selected_item = self._tree_stack[-1].children[0]

            self._selected_item_index = 0
            
            return True
        else:
            return False

    def leave_from_current_tree(self):
        if len(self._tree_stack) > 1:
            popped = self._tree_stack.pop()
            self._tree_item_count = len(self._tree_stack[-1].children)
            
            self._selected_item_index = 0
            for index, item in enumerate(self._tree_stack[-1].children):
                if item.uri == popped.uri:
                    self._selected_item_index = index
                    break

            self._selected_item = self._tree_stack[-1].children[self._selected_item_index]
            return True
        else:
            return False

    def move_pointer(self, offset):
        new_index = clamp(self._selected_item_index + offset, 0, self._tree_item_count - 1)
        if self._selected_item_index != new_index:
            self._selected_item_index = new_index
            self._selected_item = self.parent_item.children[self._selected_item_index]
            return True
        else:
            return False

    def is_valid_tree(self):
        # Test item is valid or not, but probably this doesn't work
        return liveobj_valid(self._selected_item) and liveobj_valid(self._tree_stack[-1])
    
    def refresh_tree(self):
        self.traverse_tree(self._root_item, self._selected_item)

    def traverse_tree(self, new_root, dest_item):
        # Traverse trees and navigate to selected item
        # Why did this: The design of browser intended to keep current selection even if the trees are modified by hot-swap filter
        dest_item_uri = dest_item.uri if dest_item else None
        logger.info(f"Start traverse tree = {[t.name for t in self._tree_stack]}, dest_item.uri = {dest_item_uri}")

        new_stack = [new_root]
        new_selected_item = None
        new_selected_item_index = 0

        traverse_succeeded = True
        for old_tree_item in self._tree_stack[1:]:
            item_found = False

            new_tree = new_stack[-1]
            logger.info(f"tree = {new_tree.name}, old_tree_item.uri = {old_tree_item.uri}")

            item_count = 0
            for item in new_tree.children:
                item_count += 1
                if item.uri == old_tree_item.uri:
                    logger.info(f"Found item = {item.uri}")
                    item_found = True
                    new_stack.append(item)
                    break

            if not item_found:
                logger.info("Tree item not found")
                new_selected_item = new_tree.children[0] if item_count > 0 else None
                new_selected_item_index = 0
                traverse_succeeded = False
                break

        if traverse_succeeded:
            item_found = False
            item_count = 0

            for index, item in enumerate(new_stack[-1].children):
                item_count += 1
                if item.uri == dest_item_uri:
                    item_found = True
                    new_selected_item = item
                    new_selected_item_index = index
                    break
            
            if not item_found:
                logger.info(f"Selected item not found")
                new_selected_item = new_stack[-1].children[0] if item_count > 0 else None
                new_selected_item_index = 0

        self._tree_stack = new_stack
        self._tree_item_count = len(self._tree_stack[-1].children)
        self._selected_item = new_selected_item
        self._selected_item_index = new_selected_item_index
        logger.info(f"Traverse completed tree = {[t.name for t in self._tree_stack]}, selected = {self._selected_item.name if self._selected_item else None}")

    def force_navigate_to(self, new_tree_stack):
        # Overwrite internal state to specified one
        # This is used for jumping to collections folder only!
        self._tree_stack = new_tree_stack
        self._tree_item_count = len(self._tree_stack[-1].children)
        if self._tree_item_count > 0:
            self._selected_item = self._tree_stack[-1].children[0]
        else:
            self._selected_item = None
        
        self._selected_item_index = 0

class BrowserComponent(Component, Renderable):
    select_encoder = StepEncoderControl(num_steps = 64)
    load_button = ButtonControl(color = None)
    enter_folder_button = ButtonControl(color = "Browser.CannotNavigateFolder", on_color = "Browser.CanNavigateFolder", pressed_color = "Browser.NavigateFolderPressed")
    leave_folder_button = ButtonControl(color = "Browser.CannotNavigateFolder", on_color = "Browser.CanNavigateFolder", pressed_color = "Browser.NavigateFolderPressed")
    jump_next_button = ButtonControl(color = "Browser.CannotNavigateItem", on_color = "Browser.CanNavigateItem", pressed_color = "Browser.NavigateItemPressed", repeat = True)
    jump_prev_button = ButtonControl(color = "Browser.CannotNavigateItem", on_color = "Browser.CanNavigateItem", pressed_color = "Browser.NavigateItemPressed", repeat = True)
    preview_toggle_button = ButtonControl(color = "Browser.PreviewOff", on_color = "Browser.PreviewOn")
    preview_volume_encoder = MappedSensitivitySettingControl()
    select_folder_buttons = control_list(ButtonControl, color = "DefaultColor.Off", pressed_color = "DefaultColor.On")
    hotswap_button = ButtonControl(color = "DefaultColor.Off", on_color = "DefaultButton.On")
    hotswap_content_button = ButtonControl(color = None)
        
    @listenable_property
    def selected_item_name(self):
        return self._selected_item_name
    
    @selected_item_name.setter
    def selected_item_name(self, value):
        self._selected_item_name = value
        self.notify_selected_item_name()

    @listenable_property
    def parent_folder_name(self):
        return self._parent_folder_name
    
    @parent_folder_name.setter
    def parent_folder_name(self, value):
        self._parent_folder_name = value
        self.notify_parent_folder_name()

    @property
    def preview_enabled(self):
        return self._preview_enabled
    
    @preview_enabled.setter
    def preview_enabled(self, value):
        self._preview_enabled = value
        self.preview_toggle_button.is_on = value
    
    @depends(target_track = None)
    def __init__(self, name = "Browser", target_track = None, *a, **k):
        super().__init__(name, *a, **k)
        
        self._target_track = target_track
        self._browser = self.application.browser
        self._root_item = BrowserRootItem(self._browser)
        self._explorer = BrowserTreeExplorer(self._root_item)

        # Folder iteration related
        self.selected_item_name = self._explorer.selected_item.name
        self.parent_folder_name = self._explorer.parent_item.name

        # Behaviour related
        self._close_browser = False
        self._display_modes = None
        self._preview_enabled = True
        self._hotswap_target_type = None
        self._tree_invalidated = False
        self._scroll_trigger_count = 0
        
        self.register_slot(self, self._update_led_feedback, "selected_item_name")
        self.preview_volume_encoder.mapped_parameter = self.song.master_track.mixer_device.cue_volume
        self._update_preview_state(True)
        self._on_browser_refresh_triggered.subject = self._browser
        # It seems be not triggered on Live 12.3.5
        self._on_hotswap_filter_type_changed.subject = self._browser
        self._on_hotswap_target_changed.subject = self._browser

    def set_display_modes(self, modes):
        self._display_modes = modes

    def update(self):
        logger.info("Update browser")
        super().update()
        result = self._explorer.is_valid_tree()
        logger.info(f"is_valid_tree() = {result}")
        if not result or self._tree_invalidated:
            self._do_refresh_browser()

        self._update_led_feedback()

        if not self.is_enabled():
            # Turn off preview and hotswap if the browser mode is inactive
            self._browser.stop_preview()
            self._browser.hotswap_target = None

    def _preview_item(self):
        item = self._explorer.selected_item
        self.selected_item_name = item.name if item else None
        uri = item.uri if item else None
        logger.debug(f"Preview item = {self.selected_item_name}, uri = {uri}")

        # Preview item function is time intensive (due to item loading)
        # We need to finish other tasks before item preview
        if self._preview_enabled:
            self._browser.stop_preview()
            if isinstance(item, BrowserItem):
                self._browser.preview_item(item)

    def _refresh_browser(self):
        # Just mark the flag and do actual refresh if this component is active
        # 2 reasons why this mechanism exists:
        # 1. Prevent excessive refresh
        # 2. Quick fix for the issue that items are not filtered immediately after hot-swap target is changed
        #    Sometimes happens, especially when hot-swap is enabled while browser is inactive
        self._tree_invalidated = True
        if self.is_enabled():
            self._do_refresh_browser()

    def _do_refresh_browser(self):
        self._root_item = BrowserRootItem(self._browser, self._target_track.target_track.has_midi_input)
        self._explorer.set_root_item(self._root_item)
        item = self._explorer.selected_item
        self.selected_item_name = item.name if item else None
        self.parent_folder_name = self._explorer.parent_item.name

        self._tree_invalidated = False

    def enter_folder(self):
        if self._explorer.enter_to_selected_item():
            self.parent_folder_name = self._explorer.parent_item.name
            self._preview_item()

    def leave_folder(self):
        if self._explorer.leave_from_current_tree():
            self.parent_folder_name = self._explorer.parent_item.name
            self._preview_item()
        
    def _update_preview_state(self, new_state):
        self.preview_enabled = new_state
        if self.preview_enabled:
            preview_item = self._explorer.selected_item 
            if isinstance(preview_item, BrowserItem):
                self._browser.preview_item(preview_item)
        else:
            self._browser.stop_preview()

    def _update_led_feedback(self):
        item = self._explorer.selected_item
        can_enter = False if item == None else item.is_folder or len(item.children) > 0
        self.enter_folder_button.is_on = can_enter
        self.leave_folder_button.is_on = self._explorer.tree_depth > 1
        self.jump_next_button.is_on = self._explorer.selected_item_index < self._explorer.item_count - 1
        self.jump_prev_button.is_on = self._explorer.selected_item_index > 0

    def _get_scroll_speed(self, trigger_count):
        if trigger_count <= 1:
            return 1
        elif trigger_count <= 20:
            return 5
        else:
            return 10

    @select_encoder.value
    def _on_select_encoder_value(self, value, encoder):
        if self._explorer.move_pointer(value):
            self._preview_item()

    @load_button.pressed
    def _on_load_button_pressed(self, button):
        item = self._explorer.selected_item
        if item != None:
            if item.is_loadable:
                logger.info(f"Load item {item.name}")
                self._browser.load_item(item)
                self._close_browser = self._browser.hotswap_target == None
            else:
                self.enter_folder()

    @load_button.released
    def _on_load_button_released(self, button):
        if self._close_browser:
            if self._display_modes != None:
                pop_last_mode(self._display_modes, "browser")
            self._close_browser = False

    @enter_folder_button.pressed
    def _on_enter_folder_button_pressed(self, button):
        self.enter_folder()

    @leave_folder_button.pressed
    def _on_leave_folder_button_pressed(self, button):
        self.leave_folder()

    @jump_next_button.pressed
    def _on_jump_next_button_pressed(self, button):
        self._scroll_trigger_count += 1
        if self._explorer.move_pointer(self._get_scroll_speed(self._scroll_trigger_count)):
            self._preview_item()

    @jump_next_button.released
    def _on_jump_next_button_released(self, button):
        self._scroll_trigger_count = 0

    @jump_prev_button.pressed
    def _on_jump_prev_button_pressed(self, button):
        self._scroll_trigger_count += 1
        if self._explorer.move_pointer(-self._get_scroll_speed(self._scroll_trigger_count)):
            self._preview_item()

    @jump_prev_button.released
    def _on_jump_prev_button_released(self, button):
        self._scroll_trigger_count = 0

    @preview_toggle_button.pressed
    def _on_preview_toggle_button_pressed(self, button):
        self._update_preview_state(not self.preview_enabled)
                
    @select_folder_buttons.pressed
    def _on_folder_buttons_pressed(self, button):
        if button.index < 6:
            for item in self._root_item.children:
                if isinstance(item, BrowserCollectionRootItem):
                    target = item.children[min(button.index, len(item.children) - 1)]
                    self._explorer.force_navigate_to([self._root_item, item, target])
                    break
        else:
            self._explorer.force_navigate_to([self._root_item])
        
        logger.info(f"Jump to {self._explorer.parent_item.name}")
        self.parent_folder_name = self._explorer.parent_item.name
        self._preview_item()

    @hotswap_button.pressed
    def _on_hotswap_button_pressed(self, button):
        if liveobj_valid(self._browser.hotswap_target):
            self._browser.hotswap_target = None
        else:
            self._browser.hotswap_target = self.song.view.selected_track.view.selected_device

    @hotswap_content_button.pressed
    def _on_hotswap_content_pressed(self, button):
        selected_device = self.song.view.selected_track.view.selected_device

        if liveobj_valid(self._browser.hotswap_target):
            self._browser.hotswap_target = None        
        elif selected_device.class_name == "OriginalSimpler":
            self._browser.hotswap_target = selected_device.sample
        elif selected_device.class_name == "DrumGroupDevice":
            self._browser.hotswap_target = selected_device.view.selected_drum_pad

    @listens("full_refresh")
    def _on_browser_refresh_triggered(self):
        # Refersh browser tree when 'Live.Browser.Browser.full_refersh' is triggered
        logger.info("Full refresh triggered")
        self._refresh_browser()

    @listens("filter_type")
    def _on_hotswap_filter_type_changed(self):
        logger.info("Hotswap type changed")

    @listens("hotswap_target")
    def _on_hotswap_target_changed(self):
        # Changing hotswap target causes browser item filtering, so refresh browser
        target = self._browser.hotswap_target

        self.hotswap_button.is_on = liveobj_valid(target)

        if target == None:
            new_target_type = None
        elif isinstance(target, Device):
            new_target_type = Device
        elif isinstance(target, DrumPad):
            new_target_type = DrumPad
        elif isinstance(target, Sample):
            new_target_type = Sample

        logger.info(f"Hotswap target = {target}, type = {new_target_type}")

        if self._hotswap_target_type != new_target_type:
            self._hotswap_target_type = new_target_type
            self._refresh_browser()
