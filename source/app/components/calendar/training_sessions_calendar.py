from librepy.app.components.calendar.calendar_view import Calendar
from librepy.app.data.dao.training_session_dao import TrainingSessionDAO
from com.sun.star.awt.PosSize import POSSIZE
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
        super().__init__(parent, ctx, smgr, frame, ps)

    # ------------------------------
    # Hook implementations
    # ------------------------------

    def load_calendar_data(self):
        """Load training sessions for the visible month into self.calendar_data.

        Populates: self.calendar_data = { 'YYYY-MM-DD': [ {id, date, title, status}, ... ] }
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
                    'status': s.get('status')
                }
                grouped.setdefault(date_key, []).append(s_norm)

            self.calendar_data = grouped
        except Exception as e:
            self.logger.error(f"Error loading training sessions: {e}")
            self.logger.error(traceback.format_exc())
            self.calendar_data = {}

    def _clear_entries(self):
        """Dispose and clear all rendered training session controls/pills."""
        try:
            for name, ctrl in list(self.entry_labels.items()):
                try:
                    ctrl.dispose()
                except Exception:
                    pass
                if name in self._base_positions:
                    try:
                        del self._base_positions[name]
                    except Exception:
                        pass
        finally:
            self.entry_labels.clear()

    def _render_single_entry(self, entry_name, title, x, y, w, h, row_index):
        """Create a pill-like label control and cache its base position."""
        pill = self.add_label(
            entry_name,
            x, y, w, h,
            Label=str(title or ''),
            FontHeight=10,
            FontWeight=150,
            TextColor=0x222222,
            BackgroundColor=0x72ab8a,
            Border=0
        )
        self.entry_labels[entry_name] = pill
        self._base_positions[entry_name] = (x, y, w, h, row_index)
        return pill

    def _render_entries_for_day(self, date, x, base_y, cell_width, row_index):
        """Render all training session pills for a specific date."""
        cfg = self.calendar_config
        day_label_height = cfg['day_label_height']
        entry_height = cfg.get('entry_height', 24)
        entry_spacing = cfg.get('entry_spacing', 4)
        entry_margin_x = cfg.get('entry_margin_x', 4)

        date_key = f"{date.year:04d}-{date.month:02d}-{date.day:02d}"
        sessions_for_day = self.calendar_data.get(date_key, [])
        for idx, session in enumerate(sessions_for_day):
            pill_name = f"pill_{date.day}{date.month}{date.year}_{session['id']}"
            pill_x = x + entry_margin_x
            pill_y = base_y + day_label_height + entry_spacing + idx * (entry_height + entry_spacing)
            pill_w = cell_width - 2 * entry_margin_x
            pill_h = entry_height
            self._render_single_entry(pill_name, session.get('title'), pill_x, pill_y, pill_w, pill_h, row_index)

    def _move_entries_in_view(self, visible_row_start, visible_row_end, offset_y):
        """Relocate/show/hide entry pills according to scrolling window."""
        controls_moved = 0
        controls_hidden = 0
        for ctrl_name, ctrl in self.entry_labels.items():
            if ctrl_name in self._base_positions:
                x, y, w, h, row_index = self._base_positions[ctrl_name]
                if visible_row_start <= row_index < visible_row_end:
                    ctrl.setPosSize(x, y + offset_y, w, h, POSSIZE)
                    ctrl.setVisible(True)
                    controls_moved += 1
                else:
                    ctrl.setVisible(False)
                    controls_hidden += 1
        return controls_moved, controls_hidden
