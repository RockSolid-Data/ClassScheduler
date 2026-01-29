from librepy.pybrex import dialog
from librepy.app.components.settings.tabs.background_tab import BackgroundTab


class AppSettingsDialog(dialog.DialogBase):
    """
    Application settings dialog with tabs for various app preferences.
    Currently includes:
    - Background: UI color customization
    """

    POS_SIZE = 0, 0, 450, 300
    MARGIN = 12
    BUTTON_HEIGHT = 22

    def __init__(self, ctx, parent, logger, **props):
        props['Title'] = props.get('Title', 'Application Settings')
        self.ctx = ctx
        self.parent = parent
        self.logger = logger
        
        # Tab view instances
        self.background_tab = None
        
        super().__init__(ctx, self.parent, **props)

    def _create(self):
        """Create the dialog UI with tabs"""
        # Layout calculations
        content_x = self.MARGIN
        content_y = self.MARGIN
        content_w = self.POS_SIZE[2] - (self.MARGIN * 2)
        content_h = self.POS_SIZE[3] - (self.MARGIN * 3) - self.BUTTON_HEIGHT

        # Create tab container
        tabs = self.add_page_container('Tabs', content_x, content_y, content_w, content_h)

        # Add Background tab page
        page_background = self.add_page(tabs, 'BackgroundPage', 'Background')

        # Instantiate tab view and build
        self.background_tab = BackgroundTab(
            self, 
            page_background, 
            self.ctx, 
            self.smgr, 
            self.logger
        )
        self.background_tab.build()

        # OK button at bottom-right
        btn_width = 70
        btn_y = self.POS_SIZE[3] - self.MARGIN - self.BUTTON_HEIGHT
        ok_x = self.POS_SIZE[2] - self.MARGIN - btn_width

        self.add_button(
            'BtnOK', 
            ok_x, 
            btn_y, 
            btn_width, 
            self.BUTTON_HEIGHT, 
            Label='OK', 
            PushButtonType=1, 
            DefaultButton=True
        )

    def _prepare(self):
        """Prepare the dialog - load settings into tabs"""
        if self.background_tab:
            self.background_tab.prepare()

    def _dispose(self):
        """Clean up resources when dialog is closed"""
        if self.background_tab:
            self.background_tab.dispose()

    def _done(self, ret):
        """Handle dialog close"""
        return ret
