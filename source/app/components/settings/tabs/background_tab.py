from librepy.app.components.settings.tabs.base_tab import BaseTab
from librepy.pybrex.msgbox import msgbox
from librepy.app.data.dao.settings_dao import SettingsDAO


class BackgroundTab(BaseTab):

    DEFAULT_MAIN_BG_COLOR = "#F2F2F2"
    DEFAULT_SIDEBAR_BG_COLOR = "#357399"

    def __init__(self, dialog, page, ctx=None, smgr=None, logger=None):
        super().__init__(dialog, page, ctx, smgr, logger)
        self.settings_dao = SettingsDAO(logger)
        
        self.main_bg_color_label = None
        self.sidebar_bg_color_label = None
        
        self.main_bg_color = self.DEFAULT_MAIN_BG_COLOR
        self.sidebar_bg_color = self.DEFAULT_SIDEBAR_BG_COLOR

    def build(self):
        margin = 15
        btn_width = 120
        btn_height = 25
        tab_width = 410
        label_width = 150
        field_width = 100
        field_height = 20
        label_height = 15
        row_spacing = 40
        
        y = margin
        x_label = margin
        x_field = x_label + label_width + 10

        # -------------------- Main Background Color Group --------------------
        self.dialog.add_groupbox(
            "grp_main_bg",
            margin - 5,
            y - 5,
            tab_width - (margin * 2) + 10,
            60,
            Label="Main Container Background",
            FontWeight=110,
            page=self.page
        )

        y += 15

        self.dialog.add_label(
            "lbl_main_bg_color",
            x_label,
            y,
            label_width,
            label_height,
            Label="Background Color:",
            FontHeight=10,
            BackgroundColor=0xFFFFFF,
            Align=2,
            VerticalAlign=1,
            page=self.page
        )

        self.main_bg_color_label = self.dialog.add_label(
            "lbl_main_bg_display",
            x_field,
            y - 2,
            field_width,
            field_height,
            Label=self.main_bg_color,
            FontHeight=9,
            Align=1,
            VerticalAlign=1,
            Border=1,
            page=self.page
        )

        btn_x = x_field + field_width + 10
        color_btn_width = 80
        self.dialog.add_button(
            "btn_pick_main_bg",
            btn_x,
            y - 2,
            color_btn_width,
            field_height,
            Label="Pick Color",
            callback=self._pick_main_bg_color,
            BackgroundColor=0x001F3F,
            TextColor=0xFFFFFF,
            FontHeight=9,
            page=self.page
        )

        y += row_spacing + 10

        # -------------------- Sidebar Background Color Group --------------------
        self.dialog.add_groupbox(
            "grp_sidebar_bg",
            margin - 5,
            y - 5,
            tab_width - (margin * 2) + 10,
            60,
            Label="Sidebar Background",
            FontWeight=110,
            page=self.page
        )

        y += 15

        self.dialog.add_label(
            "lbl_sidebar_bg_color",
            x_label,
            y,
            label_width,
            label_height,
            Label="Background Color:",
            FontHeight=10,
            BackgroundColor=0xFFFFFF,
            Align=2,
            VerticalAlign=1,
            page=self.page
        )

        self.sidebar_bg_color_label = self.dialog.add_label(
            "lbl_sidebar_bg_display",
            x_field,
            y - 2,
            field_width,
            field_height,
            Label=self.sidebar_bg_color,
            FontHeight=9,
            Align=1,
            VerticalAlign=1,
            Border=1,
            page=self.page
        )

        self.dialog.add_button(
            "btn_pick_sidebar_bg",
            btn_x,
            y - 2,
            color_btn_width,
            field_height,
            Label="Pick Color",
            callback=self._pick_sidebar_bg_color,
            BackgroundColor=0x001F3F,
            TextColor=0xFFFFFF,
            FontHeight=9,
            page=self.page
        )

        y += row_spacing + 20

        # -------------------- Color Action Buttons --------------------
        color_btn_start_x = x_label
        action_btn_width = 100
        btn_spacing = 10

        self.dialog.add_button(
            "btn_save_colors",
            color_btn_start_x,
            y,
            action_btn_width,
            btn_height,
            Label="Save Colors",
            callback=self._save_colors,
            BackgroundColor=0x2E7D32,
            TextColor=0xFFFFFF,
            FontHeight=10,
            FontWeight=150,
            page=self.page
        )

        self.dialog.add_button(
            "btn_restore_defaults",
            color_btn_start_x + action_btn_width + btn_spacing,
            y,
            action_btn_width + 20,
            btn_height,
            Label="Restore Defaults",
            callback=self._restore_defaults,
            BackgroundColor=0x808080,
            TextColor=0xFFFFFF,
            FontHeight=10,
            FontWeight=150,
            page=self.page
        )

    def prepare(self):
        """Load saved color settings"""
        self._load_saved_colors()

    def _load_saved_colors(self):
        """Load saved color preferences from database."""
        try:
            main_bg = self.settings_dao.get_setting('main_bg_color')
            sidebar_bg = self.settings_dao.get_setting('sidebar_bg_color')

            if main_bg:
                self.main_bg_color = main_bg
            if sidebar_bg:
                self.sidebar_bg_color = sidebar_bg

            self._update_color_displays()

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error loading saved colors: {e}")

    def _pick_main_bg_color(self, *args):
        """Open color picker for main background."""
        self._open_color_picker('main')

    def _pick_sidebar_bg_color(self, *args):
        """Open color picker for sidebar background."""
        self._open_color_picker('sidebar')

    def _open_color_picker(self, color_type):
        """Open the system color picker dialog."""
        try:
            color_picker = self.smgr.createInstanceWithContext(
                "com.sun.star.ui.dialogs.ColorPicker", self.ctx
            )

            if color_picker is not None:
                title = "Select Main Background Color" if color_type == 'main' else "Select Sidebar Background Color"
                color_picker.setTitle(title)

                current_color = self.main_bg_color if color_type == 'main' else self.sidebar_bg_color
                if current_color:
                    try:
                        hex_color = current_color.replace('#', '')
                        int_color = int(hex_color, 16)
                        color_picker.setPropertyValue("Color", int_color)
                    except Exception:
                        pass

                dialog_result = color_picker.execute()

                if dialog_result == 1:
                    color_property = color_picker.getPropertyValues()

                    for prop in color_property:
                        if prop.Name == "Color":
                            selected_color = prop.Value
                            hex_color = "#{:06X}".format(selected_color)

                            if color_type == 'main':
                                self.main_bg_color = hex_color
                            else:
                                self.sidebar_bg_color = hex_color

                            self._update_color_displays()

                            if self.logger:
                                self.logger.info(f"{color_type} color selected: {hex_color}")
                            break
            else:
                msgbox("Error: Unable to open the color picker.", "Error")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error opening color picker: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
            msgbox(f"Error opening color picker: {str(e)}", "Error")

    def _update_color_displays(self):
        """Update the color display labels with current colors."""
        if self.main_bg_color_label:
            try:
                hex_color = self.main_bg_color.replace('#', '')
                int_color = int(hex_color, 16)

                self.main_bg_color_label.Model.BackgroundColor = int_color
                self.main_bg_color_label.Model.Label = self.main_bg_color

                r = (int_color >> 16) & 0xFF
                g = (int_color >> 8) & 0xFF
                b = int_color & 0xFF
                brightness = (r * 299 + g * 587 + b * 114) / 1000

                text_color = 0x000000 if brightness > 128 else 0xFFFFFF
                self.main_bg_color_label.Model.TextColor = text_color

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error updating main bg color display: {e}")

        if self.sidebar_bg_color_label:
            try:
                hex_color = self.sidebar_bg_color.replace('#', '')
                int_color = int(hex_color, 16)

                self.sidebar_bg_color_label.Model.BackgroundColor = int_color
                self.sidebar_bg_color_label.Model.Label = self.sidebar_bg_color

                r = (int_color >> 16) & 0xFF
                g = (int_color >> 8) & 0xFF
                b = int_color & 0xFF
                brightness = (r * 299 + g * 587 + b * 114) / 1000

                text_color = 0x000000 if brightness > 128 else 0xFFFFFF
                self.sidebar_bg_color_label.Model.TextColor = text_color

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error updating sidebar bg color display: {e}")

    def _save_colors(self, *args):
        """Save color preferences to database."""
        try:
            self.settings_dao.set_setting('main_bg_color', self.main_bg_color)
            self.settings_dao.set_setting('sidebar_bg_color', self.sidebar_bg_color)

            msgbox(
                "Colors saved successfully.\n\nPlease restart the application for the changes to take effect.",
                "Restart Required"
            )

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving colors: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
            msgbox(f"Error saving colors: {str(e)}", "Error")

    def _restore_defaults(self, *args):
        """Restore all color preferences to default values."""
        try:
            self.main_bg_color = self.DEFAULT_MAIN_BG_COLOR
            self.sidebar_bg_color = self.DEFAULT_SIDEBAR_BG_COLOR

            self._update_color_displays()

            if self.logger:
                self.logger.info("Colors restored to defaults (not saved yet)")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error restoring defaults: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
            msgbox(f"Error restoring defaults: {str(e)}", "Error")

    def dispose(self):
        """Clean up resources"""
        pass
