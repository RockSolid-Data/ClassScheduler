from .base_tab import BaseTab
from librepy.app.data.dao.employee_dao import EmployeeDAO
from librepy.pybrex.listeners import Listeners


class EmployeesTab(BaseTab):
    def __init__(self, dialog, page, ctx, smgr, logger):
        super().__init__(dialog, page, ctx, smgr, logger)
        self.grid_base = None
        self.grid = None
        self.btn_new_entry = None
        self.listeners = Listeners()

    def build(self):
        btn_w, btn_h = 70, 12
        btn_x = 10 + 460 - btn_w
        btn_y = 5
        self.btn_new_entry = self.dialog.add_button(
            'BtnEmployeeNewEntry', btn_x, btn_y, btn_w, btn_h,
            callback=self.on_new_entry,
            page=self.page,
            Label='New Entry',
            FontWeight=100,
            FontHeight=12,
            BackgroundColor=0x001F3F,
            TextColor=0xFFFFFF,
        )

        titles = [
            ("ID", "id", 70, 1),
            ("Name", "name", 220, 1),
            ("Email", "email", 220, 1),
        ]
        self.grid_base, self.grid = self.dialog.add_grid(
            'GridEmployees',
            10, 20,
            460, 260,
            titles,
            page=self.page,
            ShowRowHeader=False,
        )
        self.listeners.add_mouse_listener(self.grid, pressed=self.on_row_double_click)
        # Load data initially
        self.load_data()


    def load_data(self):
        try:
            dao = EmployeeDAO(self.logger)
            rows = dao.get_all_for_grid() or []
            self.grid_base.set_data(rows, heading='id')
        except Exception as e:
            self.logger.error(f"EmployeesTab.load_data error: {e}")

    def on_new_entry(self, ev=None):
        try:
            from librepy.app.components.settings.employee_entry_dlg import EmployeeEntryDialog
            dlg = EmployeeEntryDialog(self.ctx, self.dialog, self.logger)
            ret = dlg.execute()
            if ret in (1, 2):
                self.load_data()
        except Exception as e:
            self.logger.error(f"Failed to open EmployeeEntryDialog: {e}")

    def on_row_double_click(self, ev=None):
        if getattr(ev, 'Buttons', None) == 1 and getattr(ev, 'ClickCount', 0) == 2:
            try:
                heading = self.grid_base.active_row_heading()
                if heading is None:
                    return
                from librepy.app.components.settings.employee_entry_dlg import EmployeeEntryDialog
                dlg = EmployeeEntryDialog(self.ctx, self.dialog, self.logger, employee_id=heading)
                ret = dlg.execute()
                if ret in (1, 2):
                    self.load_data()
            except Exception as e:
                self.logger.error(f"EmployeesTab.on_row_double_click error: {e}")
