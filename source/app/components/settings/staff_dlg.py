from librepy.pybrex import dialog
from librepy.app.components.settings.tabs.employees_tab import EmployeesTab
from librepy.app.components.settings.tabs.teachers_tab import TeachersTab


class StaffDialog(dialog.DialogBase):
    """
    Staff management dialog with two empty tabs (Employees, Teachers) and OK/Cancel buttons.
    """

    POS_SIZE = 0, 0, 500, 400
    MARGIN = 12
    BUTTON_HEIGHT = 22

    def __init__(self, ctx, parent, logger, **props):
        props['Title'] = props.get('Title', 'Staff')
        self.ctx = ctx
        self.parent = parent
        self.logger = logger
        # Tab view instances
        self.employees_tab = None
        self.teachers_tab = None
        super().__init__(ctx, self.parent, **props)

    def _create(self):
        # Layout calculations
        content_x = self.MARGIN
        content_y = self.MARGIN
        content_w = self.POS_SIZE[2] - (self.MARGIN * 2)
        content_h = self.POS_SIZE[3] - (self.MARGIN * 3) - self.BUTTON_HEIGHT

        # Create tab container
        tabs = self.add_page_container('Tabs', content_x, content_y, content_w, content_h)

        # Add pages
        page_employees = self.add_page(tabs, 'EmployeesPage', 'Employees')
        page_teachers = self.add_page(tabs, 'TeachersPage', 'Teachers')

        # Instantiate tab views and build
        self.employees_tab = EmployeesTab(self, page_employees, self.ctx, self.smgr, self.logger)
        self.employees_tab.build()

        self.teachers_tab = TeachersTab(self, page_teachers, self.ctx, self.smgr, self.logger)
        self.teachers_tab.build()

        # Buttons at bottom-right
        btn_width = 70
        gap = 8
        btn_y = self.POS_SIZE[3] - self.MARGIN - self.BUTTON_HEIGHT
        ok_x = self.POS_SIZE[2] - self.MARGIN - btn_width
        cancel_x = ok_x - gap - btn_width

        # Cancel
        self.add_cancel('BtnCancel', cancel_x, btn_y, btn_width, self.BUTTON_HEIGHT)
        # OK
        self.add_button('BtnOK', ok_x, btn_y, btn_width, self.BUTTON_HEIGHT, Label='OK', PushButtonType=1, DefaultButton=True)

    def _prepare(self):
        pass

    def _dispose(self):
        pass

    def _done(self, ret):
        return ret
