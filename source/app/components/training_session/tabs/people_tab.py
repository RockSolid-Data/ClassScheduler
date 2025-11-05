from librepy.app.components.settings.tabs.base_tab import BaseTab
from librepy.pybrex.listeners import Listeners
from librepy.app.data.dao.session_attendee_dao import SessionAttendeeDAO


class PeopleTab(BaseTab):
    """People tab: shows attendees for the selected session in a grid.

    Replicates the TeachersTab pattern from Staff dialog: a New Entry button,
    a data grid, double-click to edit, and data loader. The entry/edit dialog is
    optional; if not present, actions are safely logged.
    """

    def __init__(self, dialog, page, ctx, smgr, logger, session_id=None):
        super().__init__(dialog, page, ctx, smgr, logger)
        self.session_id = session_id
        self.grid_base = None
        self.grid = None
        self.btn_new_entry = None
        self.listeners = Listeners()

    def build(self):
        # Compute page-relative geometry similar to TeachersTab but adapted to this dialog size
        page_width = self.dialog.POS_SIZE[2] - (self.dialog.MARGIN * 2)
        page_height = self.dialog.POS_SIZE[3] - (self.dialog.MARGIN * 3) - self.dialog.BUTTON_HEIGHT + 30
        pad = 10

        # Top-right New Entry button
        btn_w, btn_h = 100, 12
        btn_x = page_width - btn_w
        btn_y = 4
        self.btn_new_entry = self.dialog.add_button(
            'BtnAttendeeNewEntry', btn_x, btn_y, btn_w, btn_h,
            callback=self.on_new_entry,
            page=self.page,
            Label='New Entry',
            FontWeight=100,
            FontHeight=11,
        )

        # Grid title spec
        titles = [
            ("ID", "id", 50, 1),
            ("Name", "name", 100, 1),
            ("Email", "email", 120, 1),
            ("Phone", "phone", 100, 1),
            ("Paid", "paid", 80, 1),
        ]

        grid_x = pad
        grid_y = btn_y + btn_h + 6
        grid_w = page_width - (pad * 2)
        grid_h = max(120, page_height - grid_y - pad)

        self.grid_base, self.grid = self.dialog.add_grid(
            'GridSessionAttendees',
            grid_x, grid_y,
            grid_w, grid_h,
            titles,
            page=self.page,
            ShowRowHeader=False,
        )
        self.listeners.add_mouse_listener(self.grid, pressed=self.on_row_double_click)

        # Initial load
        self.load_data()

    def on_new_entry(self, ev=None):
        # Optional: open an attendee entry dialog if available
        try:
            from librepy.app.components.training_session.attendee_entry_dlg import AttendeeEntryDialog
            dlg = AttendeeEntryDialog(self.ctx, self.dialog, self.logger, session_id=self.session_id)
            ret = dlg.execute()
            if ret in (1, 2):
                self.load_data()
        except Exception as e:
            # Dialog not implemented yet or failed; just log and keep grid usable
            self.logger.info(f"Attendee new-entry dialog not available or failed: {e}")

    def on_row_double_click(self, ev=None):
        if getattr(ev, 'Buttons', None) == 1 and getattr(ev, 'ClickCount', 0) == 2:
            try:
                heading = self.grid_base.active_row_heading()
                if heading is None:
                    return
                from librepy.app.components.training_session.attendee_entry_dlg import AttendeeEntryDialog
                dlg = AttendeeEntryDialog(self.ctx, self.dialog, self.logger, attendee_id=heading, session_id=self.session_id)
                ret = dlg.execute()
                if ret in (1, 2):
                    self.load_data()
            except Exception as e:
                self.logger.info(f"Attendee edit dialog not available or failed: {e}")

    def load_data(self):
        try:
            if not self.session_id:
                self.grid_base.set_data([], heading='id')
                return
            dao = SessionAttendeeDAO(self.logger)
            rows = dao.get_all_for_grid(self.session_id) or []
            self.grid_base.set_data(rows, heading='id')
        except Exception as e:
            self.logger.error(f"PeopleTab.load_data error: {e}")

    def commit(self) -> dict:
        # People grid does not contribute to session save payload currently
        return {}
