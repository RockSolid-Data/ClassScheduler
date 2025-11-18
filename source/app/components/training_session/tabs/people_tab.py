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
        self.btn_print = None
        self.listeners = Listeners()

    def build(self):
        # Compute page-relative geometry similar to TeachersTab but adapted to this dialog size
        page_width = self.dialog.POS_SIZE[2] - (self.dialog.MARGIN * 2)
        page_height = self.dialog.POS_SIZE[3] - (self.dialog.MARGIN * 3) - self.dialog.BUTTON_HEIGHT + 30
        pad = 5

        # Top-right New Entry and Print buttons
        btn_w, btn_h = 70, 10
        btn_y = 5
        btn_x = page_width - pad - btn_w
        self.btn_new_entry = self.dialog.add_button(
            'BtnAttendeeNewEntry', btn_x, btn_y, btn_w, btn_h,
            callback=self.on_new_entry,
            page=self.page,
            Label='New Entry',
            FontWeight=100,
            FontHeight=12,
        )

        # Print button to the left of New Entry
        print_x = btn_x - (btn_w + 6)
        self.btn_print = self.dialog.add_button(
            'BtnAttendeePrint', print_x, btn_y, btn_w, btn_h,
            callback=self.on_print,
            page=self.page,
            Label='Print',
            FontWeight=100,
            FontHeight=12,
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
        from librepy.app.components.training_session.attendee_entry_dlg import AttendeeEntryDialog
        dlg = AttendeeEntryDialog(self.ctx, self.dialog, self.logger, session_id=self.session_id)
        ret = dlg.execute()
        if ret in (1, 2):
            self.load_data()
            if self.dialog is not None:
                self.dialog.refresh_attendance_tab()

    def on_print(self, ev=None):
        """Print attendees report for this session using Jasper template."""
        try:
            if not self.session_id:
                return
            # Load session details for title parameters
            from librepy.app.data.dao.training_session_dao import TrainingSessionDAO
            dao = TrainingSessionDAO(self.logger)
            rec = dao.get_by_id(self.session_id)
            if rec and not isinstance(rec, dict):
                rec = dao.to_dict(rec)

            session_name = (rec or {}).get('name') or ''
            session_date = (rec or {}).get('session_date')
            session_time = (rec or {}).get('session_time')

            # Delegate to report generator
            from librepy.jasper_report.print_session_attendees import print_session_attendees
            print_session_attendees(
                session_id=self.session_id,
                session_date=session_date,
                session_time=session_time,
                session_name=session_name,
            )
        except Exception as e:
            # Log but avoid raising inside UI callback
            try:
                self.logger.error(f"Failed to print attendees report: {e}")
            except Exception:
                pass

    def on_row_double_click(self, ev=None):
        if ev.Buttons == 1 and ev.ClickCount == 2:
            heading = self.grid_base.active_row_heading()
            if heading is None:
                return
            from librepy.app.components.training_session.attendee_entry_dlg import AttendeeEntryDialog
            dlg = AttendeeEntryDialog(self.ctx, self.dialog, self.logger, attendee_id=heading, session_id=self.session_id)
            ret = dlg.execute()
            if ret in (1, 2):
                self.load_data()
                # Keep Attendance tab in sync with People updates
                if self.dialog is not None:
                    self.dialog.refresh_attendance_tab()

    def load_data(self):
        if not self.session_id:
            self.grid_base.set_data([], heading='id')
            return
        dao = SessionAttendeeDAO(self.logger)
        rows = dao.get_all_for_grid(self.session_id) or []
        self.grid_base.set_data(rows, heading='id')

    def commit(self) -> dict:
        # People grid does not contribute to session save payload currently
        return {}
