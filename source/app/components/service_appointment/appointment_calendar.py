from librepy.app.components.calendar.calendar_view import Calendar
from librepy.app.data.dao.service_appointment_dao import ServiceAppointmentDAO
import calendar as py_calendar
import traceback
from .service_appt_dlg import ServiceAppointmentDialog


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
        """Open the Service Appointment dialog and refresh calendar on successful save."""
        try:
            dlg = ServiceAppointmentDialog(self, self.ctx, self.smgr, self.frame, self.ps, Title="New Service Appointment")
            ret = dlg.execute()
            if ret == 1:
                self._update_calendar()
        except Exception as e:
            self.logger.error(f"Failed to open Service Appointment dialog: {e}")
            self.logger.error(traceback.format_exc())

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
                    'status': a.get('status'),
                    'color': 0xebb056,
                }
                grouped.setdefault(date_key, []).append(a_norm)

            self.calendar_data = grouped
        except Exception as e:
            self.logger.error(f"Error loading service appointments: {e}")
            self.logger.error(traceback.format_exc())
            self.calendar_data = {}
