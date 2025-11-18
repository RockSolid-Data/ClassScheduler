from librepy.app.components.calendar.calendar_view import Calendar
from librepy.app.data.dao.service_appointment_dao import ServiceAppointmentDAO
from librepy.app.components.service_appointment.service_appt_dlg import ServiceAppointmentDialog
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
        """Generate a PDF calendar for the visible date range using JasperReports."""
        try:
            start_date, end_date = self.get_display_date_range()
            if not start_date or not end_date:
                self.logger.warning("AppointmentCalendar: no date range to print")
                return
            from librepy.jasper_report.print_calendar import save_calendar_range_as_pdf
            from librepy.app.components.calendar.queries import SERVICE_APPOINTMENTS_QUERY

            query_text = SERVICE_APPOINTMENTS_QUERY
            self.logger.info(f"Printing Service Appointments calendar: {start_date} - {end_date}")
            save_calendar_range_as_pdf(start_date, end_date, query_text)
            self.logger.info("Service Appointments calendar PDF export invoked")
        except Exception as e:
            self.logger.error(f"Failed to print Service Appointments calendar: {e}")
            self.logger.error(traceback.format_exc())

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

    def on_entry_click(self, ev, entry_id=None):
        """Handle clicks on an appointment entry: log id then open edit dialog.

        Calls the base handler to log the id, then opens the ServiceAppointmentDialog
        in edit mode by passing the id. Refreshes the calendar after a successful save.
        """
        try:
            super().on_entry_click(ev, entry_id)
            if entry_id is None:
                return
            dlg = ServiceAppointmentDialog(self, self.ctx, self.smgr, self.frame, self.ps, Title="Edit Service Appointment", service_apt_id=entry_id)
            ret = dlg.execute()
            if ret == 1 or ret == 2:
                self._update_calendar()
        except Exception as e:
            self.logger.error(f"Failed to open Service Appointment for edit (id={entry_id}): {e}")
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
