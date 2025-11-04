from .base_tab import BaseTab
from librepy.app.data.dao.teacher_dao import TeacherDAO


class TeachersTab(BaseTab):
    def __init__(self, dialog, page, ctx, smgr, logger):
        super().__init__(dialog, page, ctx, smgr, logger)
        self.grid_base = None
        self.grid = None
        self.btn_new_entry = None

    def build(self):
        btn_w, btn_h = 70, 10
        btn_x = 10 + 460 - btn_w
        btn_y = 5
        self.btn_new_entry = self.dialog.add_button(
            'BtnTeacherNewEntry', btn_x, btn_y, btn_w, btn_h,
            callback=self.on_new_entry,
            page=self.page,
            Label='New Entry',
            FontWeight=100,
            FontHeight=12,
        )

        titles = [
            ("ID", "id", 70, 1),
            ("Name", "name", 220, 1),
            ("Email", "email", 220, 1),
        ]
        self.grid_base, self.grid = self.dialog.add_grid(
            'GridTeachers',
            10, 20,
            460, 260,
            titles,
            page=self.page,
            ShowRowHeader=False,
        )
        # Load data initially
        self.load_data()

    def on_new_entry(self, ev=None):
        try:
            from librepy.app.components.settings.teacher_entry_dlg import TeacherEntryDialog
            dlg = TeacherEntryDialog(self.ctx, self.dialog, self.logger)
            dlg.execute()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to open TeacherEntryDialog: {e}")

    def load_data(self):
        try:
            dao = TeacherDAO(self.logger)
            rows = dao.get_all_for_grid() or []
            self.grid_base.set_data(rows, heading='id')
        except Exception as e:
            self.logger.error(f"TeachersTab.load_data error: {e}")
