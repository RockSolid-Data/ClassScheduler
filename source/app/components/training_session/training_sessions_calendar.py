from librepy.app.components.calendar.calendar_view import Calendar
from librepy.app.data.dao.training_session_dao import TrainingSessionDAO
from librepy.app.components.training_session.training_session_entry_dlg import TrainingSessionEntryDlg
import calendar as py_calendar
import traceback


class TrainingSessionsCalendar(Calendar):
    """
    Calendar specialized for training sessions.

    Implements data loading and entry rendering hooks to display training-session
    pills within the base month grid and scrolling mechanics provided by Calendar.
    """

    # Keep the same component name so route/screen stays unchanged
    component_name = 'calendar'

    def __init__(self, parent, ctx, smgr, frame, ps):
        super().__init__(parent, ctx, smgr, frame, ps, title="Training Sessions")

    # ------------------------------
    # Hook implementations
    # ------------------------------
    def on_print(self, event):
        """Subclass callback for Print button (placeholder)."""
        try:
            self.logger.info("Print Calendar clicked")
            start_date, end_date = self.get_display_date_range()
            if not start_date or not end_date:
                self.logger.warning("No calendar range available to print")
                return
            from librepy.jasper_report.print_calendar import save_calendar_range_as_pdf
            from librepy.app.components.calendar.queries import CALENDAR_EVENTS_QUERY

            query_text = CALENDAR_EVENTS_QUERY
            self.logger.info(f"Invoking PDF export for range {start_date} - {end_date}")
            save_calendar_range_as_pdf(start_date, end_date, query_text)
            self.logger.info("Calendar PDF export invoked successfully")
        except Exception as e:
            self.logger.error(f"Error printing calendar: {e}")
            self.logger.error(traceback.format_exc())

    def on_new_entry(self, event):
        """Open dialog to create a new training session and refresh on success."""
        try:
            dlg = TrainingSessionEntryDlg(self, self.ctx, self.smgr, self.frame, self.ps, Title="New Training Session")
            ret = dlg.execute()
            if ret == 1:
                self._update_calendar()
                #  TODO: Refine in list too
                new_id = getattr(dlg, 'last_saved_id', None)
                if new_id:
                    dlg2 = TrainingSessionEntryDlg(self, self.ctx, self.smgr, self.frame, self.ps, Title="Edit Training Session", session_id=new_id)
                    ret2 = dlg2.execute()
                    if ret2 in (1, 2):
                        self._update_calendar()
        except Exception as e:
            self.logger.error(f"Failed to open Training Session dialog: {e}")
            self.logger.error(traceback.format_exc())

    def on_entry_click(self, ev, entry_id=None):
        """Open dialog to edit an existing training session and refresh on success."""
        try:
            super().on_entry_click(ev, entry_id)
            if entry_id is None:
                return
            dlg = TrainingSessionEntryDlg(self, self.ctx, self.smgr, self.frame, self.ps, Title="Edit Training Session", session_id=entry_id)
            ret = dlg.execute()
            if ret == 1 or ret == 2:
                self._update_calendar()
        except Exception as e:
            self.logger.error(f"Failed to open Training Session for edit (id={entry_id}): {e}")
            self.logger.error(traceback.format_exc())

    def load_calendar_data(self):
        """Load training sessions for the visible month into self.calendar_data.

        Populates: self.calendar_data = { 'YYYY-MM-DD': [ {id, date, title, color}, ... ] }
        """
        try:
            cal = py_calendar.Calendar(6)  # Sunday-first
            dates_iter = list(cal.itermonthdates(self.current_date.year, self.current_date.month))
            if not dates_iter:
                self.calendar_data = {}
                return

            start_day = dates_iter[0]
            end_day = dates_iter[-1]

            dao = TrainingSessionDAO(self.logger)
            sessions = dao.get_sessions_between(start_day, end_day)

            grouped = {}
            for s in sessions or []:
                dt = s.get('date')
                if hasattr(dt, 'strftime'):
                    date_key = dt.strftime('%Y-%m-%d')
                elif isinstance(dt, str):
                    date_key = dt
                else:
                    # Skip invalid
                    continue
                s_norm = {
                    'id': s.get('id'),
                    'date': date_key,
                    'title': s.get('title'),
                    'color': 0x72ab8a,
                }
                grouped.setdefault(date_key, []).append(s_norm)

            self.calendar_data = grouped
        except Exception as e:
            self.logger.error(f"Error loading training sessions: {e}")
            self.logger.error(traceback.format_exc())
            self.calendar_data = {}

