from librepy.app.components.calendar.calendar_view import Calendar
from librepy.app.data.dao.service_appointment_dao import ServiceAppointmentDAO
import calendar as py_calendar
import traceback


class AppointmentCalendar(Calendar):
    """
    Appointment Calendar component.

    Implements data loading and entry rendering hooks to display
    service-appointment pills within the base month grid provided by Calendar.
    """

    # Unique component name used for routing/navigation
    component_name = 'appointment_calendar'

    def __init__(self, parent, ctx, smgr, frame, ps):
        super().__init__(parent, ctx, smgr, frame, ps, title="Service Appointments")

    # ------------------------------
    # Hook implementations
    # ------------------------------
    def on_print(self, event):
        """Subclass callback for Print button (placeholder)."""
        self.logger.info("Print requested (AppointmentCalendar) - not implemented yet")

    def on_new_entry(self, event):
        """Subclass callback for New Entry button (placeholder)."""
        self.logger.info("New Entry requested (AppointmentCalendar) - not implemented yet")

    def load_calendar_data(self):
        """Load service appointments for the visible month into self.calendar_data.

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

            dao = ServiceAppointmentDAO(self.logger)
            appts = dao.get_appointments_between(start_day, end_day)

            grouped = {}
            for a in appts or []:
                dt = a.get('date')
                if hasattr(dt, 'strftime'):
                    date_key = dt.strftime('%Y-%m-%d')
                elif isinstance(dt, str):
                    date_key = dt
                else:
                    # Skip invalid
                    continue
                a_norm = {
                    'id': a.get('id'),
                    'date': date_key,
                    'title': a.get('title'),
                    'status': a.get('status')
                }
                grouped.setdefault(date_key, []).append(a_norm)

            self.calendar_data = grouped
        except Exception as e:
            self.logger.error(f"Error loading service appointments: {e}")
            self.logger.error(traceback.format_exc())
            self.calendar_data = {}

    def _render_single_entry(self, entry_name, title, x, y, w, h, row_index):
        """Create a pill-like label control and cache its base position."""
        pill = self.add_label(
            entry_name,
            x, y, w, h,
            Label=str(title or ''),
            FontHeight=10,
            FontWeight=150,
            TextColor=0x222222,
            BackgroundColor=0xebf056,
            Border=0
        )
        self.entry_labels[entry_name] = pill
        self._base_positions[entry_name] = (x, y, w, h, row_index)
        return pill

    def _render_entries_for_day(self, date, x, base_y, cell_width, row_index):
        """Render all appointment pills for a specific date."""
        cfg = self.calendar_config
        day_label_height = cfg['day_label_height']
        entry_height = cfg.get('entry_height', 24)
        entry_spacing = cfg.get('entry_spacing', 4)
        entry_margin_x = cfg.get('entry_margin_x', 4)

        date_key = f"{date.year:04d}-{date.month:02d}-{date.day:02d}"
        appts_for_day = self.calendar_data.get(date_key, [])
        for idx, appt in enumerate(appts_for_day):
            pill_name = f"pill_{date.day}{date.month}{date.year}_{appt['id']}"
            pill_x = x + entry_margin_x
            pill_y = base_y + day_label_height + entry_spacing + idx * (entry_height + entry_spacing)
            pill_w = cell_width - 2 * entry_margin_x
            pill_h = entry_height
            self._render_single_entry(pill_name, appt.get('title'), pill_x, pill_y, pill_w, pill_h, row_index)
