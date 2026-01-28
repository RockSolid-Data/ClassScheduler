from librepy.pybrex import dialog
import os
import uno
from librepy.pybrex import values


class AboutDialog(dialog.DialogBase):
    POS_SIZE = 0, 0, 390, 200
    TITLE_COLOR = 0x2B579A

    def __init__(self, ctx, smgr, parent, **props):
        props['Title'] = 'About'
        props['BackgroundColor'] = 0xFFFFFF
        self.ctx = ctx
        self.parent = parent
        self.logger = parent.logger if hasattr(parent, 'logger') else None

        # Get icon from component manager's cache
        try:
            if hasattr(parent, 'component_manager') and parent.component_manager:
                self.rocksolid_icon = parent.component_manager.get_cached_icon_url('rocksolid-icon.png')
                if self.rocksolid_icon:
                    if self.logger:
                        self.logger.info(f"Rocksolid icon loaded from cache: {self.rocksolid_icon}")
                else:
                    self.rocksolid_icon = ''
                    if self.logger:
                        self.logger.warning("Rocksolid icon not found in cache")
            else:
                self.rocksolid_icon = ''
                if self.logger:
                    self.logger.warning("Component manager not available for icon loading")
        except Exception as e:
            self.rocksolid_icon = ''
            if self.logger:
                self.logger.warning(f"Could not load icons for About dialog: {e}")

        super().__init__(ctx, smgr, **props)

    def _create(self):
        x = 10
        y = 10
        width = 250
        height = 12

        self.add_label(
            'LblTitle',
            x, y,
            width,
            height + 10,
            Label='Class Scheduler',
            FontHeight=25,
            FontWeight=150,
            TextColor=self.TITLE_COLOR,
            Align=1
        )

        y += height + 8

        self.add_label(
            'LblVersion',
            x, y,
            width,
            height,
            Label='Version 1.0',
            FontHeight=12,
            TextColor=0x666666,
            Align=1
        )

        y += height + 8

        self.add_line('line1', x + 10, y, width - 20, 1, Orientation=1, BackgroundColor=0x666666)
        y += 10

        description = 'Class Manager streamlines customer records, service appointments, employee management, documents, and reporting within LibreOffice environment.'
        self.add_label(
            'LblDescription',
            x, y,
            width,
            height * 3,
            Label=description,
            MultiLine=True,
            FontHeight=12,
            Align=1
        )

        y += height * 2

        self.add_line('line2', x + 10, y, width - 20, 1, Orientation=1, BackgroundColor=0x666666)
        y += 10

        credits = 'Developed by RockSolid Data Solutions\nContact: sales@rocksoliddata.solutions | 620-888-7050'
        self.add_label(
            'LblCredits',
            x, y,
            width,
            height * 2,
            Label=credits,
            MultiLine=True,
            FontHeight=12,
            Align=1
        )

        y += height * 2

        self.add_line('line3', x + 10, y, width - 20, 1, Orientation=1, BackgroundColor=0x666666)
        y += 10

        ownership = 'Hoover Bernina, phone: (570)966-3822, email: hooversbernina@emypeople.net'
        self.add_label(
            'LblOwnership',
            x, y,
            width,
            height * 3,
            Label=ownership,
            MultiLine=True,
            FontHeight=12,
            Align=1
        )
        y += height + 8

        image_y = 30
        self.add_image('sheep_pro_logo', 270, image_y, 100, 100, ImageURL=self.rocksolid_icon)

        y = self.POS_SIZE[3] - 35
        btn_width = 80
        self.add_button(
            'OkButton',
            int(self.POS_SIZE[2] / 2 - btn_width / 2),
            y,
            btn_width,
            20,
            Label='OK',
            PushButtonType=1,
            DefaultButton=True,
            BackgroundColor=self.TITLE_COLOR,
            TextColor=0xFFFFFF
        )

    def _prepare(self):
        pass

    def _dispose(self):
        pass

    def _done(self, ret):
        return ret