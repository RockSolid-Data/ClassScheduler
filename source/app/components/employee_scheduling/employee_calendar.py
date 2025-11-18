from librepy.app.components.calendar.calendar_view import Calendar
from librepy.app.data.dao.employee_contract_dao import EmployeeContractDAO
from librepy.app.components.employee_scheduling.employee_contract_dlg import EmployeeContractDialog
import calendar as py_calendar
import traceback
from datetime import timedelta
import colorsys


class EmployeeCalendar(Calendar):
    """
    Employee Calendar component.

    Displays employee contract spans as daily entries within the month grid.
    Each contract generates one entry per day between its start and end date (inclusive).
    """

    # Unique component name used for routing/navigation
    component_name = 'employee_calendar'

    def __init__(self, parent, ctx, smgr, frame, ps):
        super().__init__(parent, ctx, smgr, frame, ps, title="Employee Contracts")

    # ------------------------------
    # Hook implementations
    # ------------------------------
    def on_print(self, event):
        """Generate a PDF calendar for the visible date range using JasperReports."""
        try:
            start_date, end_date = self.get_display_date_range()
            if not start_date or not end_date:
                self.logger.warning("EmployeeCalendar: no date range to print")
                return
            from librepy.jasper_report.print_calendar import save_calendar_range_as_pdf
            from librepy.app.components.calendar.queries import EMPLOYEE_CONTRACTS_QUERY

            query_text = EMPLOYEE_CONTRACTS_QUERY
            self.logger.info(f"Printing Employee Contracts calendar: {start_date} - {end_date}")
            save_calendar_range_as_pdf(start_date, end_date, query_text)
            self.logger.info("Employee Contracts calendar PDF export invoked")
        except Exception as e:
            self.logger.error(f"Failed to print Employee Contracts calendar: {e}")
            self.logger.error(traceback.format_exc())

    def on_new_entry(self, event):
        """Open the Employee Contract dialog and refresh calendar on successful save."""
        try:
            dlg = EmployeeContractDialog(self, self.ctx, self.smgr, self.frame, self.ps, Title="New Employee Contract")
            ret = dlg.execute()
            if ret == 1:
                self._update_calendar()
        except Exception as e:
            self.logger.error(f"Failed to open Employee Contract dialog: {e}")
            self.logger.error(traceback.format_exc())

    def on_entry_click(self, ev, entry_id=None):
        """Open Employee Contract dialog in edit mode when clicking an entry; refresh on save/delete."""
        try:
            super().on_entry_click(ev, entry_id)
            if entry_id is None:
                return
            dlg = EmployeeContractDialog(self, self.ctx, self.smgr, self.frame, self.ps, Title="Edit Employee Contract", contract_id=entry_id)
            ret = dlg.execute()
            if ret == 1 or ret == 2:
                self._update_calendar()
        except Exception as e:
            self.logger.error(f"Failed to open Employee Contract for edit (id={entry_id}): {e}")
            self.logger.error(traceback.format_exc())

    def load_calendar_data(self):
        """Load employee contracts overlapping the visible month and expand to daily entries.

        Populates: self.calendar_data = { 'YYYY-MM-DD': [ {id, date, title, status, color}, ... ] }
        """
        try:
            cal = py_calendar.Calendar(6)  # Sunday-first
            dates_iter = list(cal.itermonthdates(self.current_date.year, self.current_date.month))
            if not dates_iter:
                self.calendar_data = {}
                return

            visible_start = dates_iter[0]
            visible_end = dates_iter[-1]

            dao = EmployeeContractDAO(self.logger)
            contracts = dao.get_contracts_between(visible_start, visible_end)

            # Build distinct contract id list
            distinct_ids = []
            for c in contracts or []:
                cid = c.get('id')
                if cid is not None and cid not in distinct_ids:
                    distinct_ids.append(cid)

            # Generate a simple HSL palette sized to distinct contracts
            # Constrain saturation and lightness to produce light pastel colors that work with dark text
            def hsl_color(i, n, s=0.45, l=0.82):
                if n <= 0:
                    return 0xD6EAF8
                h = (i % n) / float(n)
                r, g, b = colorsys.hls_to_rgb(h, l, s)  # note: colorsys uses HLS
                R = int(round(r * 255))
                G = int(round(g * 255))
                B = int(round(b * 255))
                # Ensure sufficient brightness for dark (current) font
                luma = 0.2126 * R + 0.7152 * G + 0.0722 * B
                if luma < 150:  # too dark for 0x222222 text; lighten it
                    r2, g2, b2 = colorsys.hls_to_rgb(h, 0.88, s)
                    R = int(round(r2 * 255))
                    G = int(round(g2 * 255))
                    B = int(round(b2 * 255))
                return (R << 16) | (G << 8) | B

            n = len(distinct_ids)
            color_map = {cid: hsl_color(idx, n) for idx, cid in enumerate(distinct_ids)}

            grouped = {}
            for c in contracts or []:
                c_start = c.get('start_date')
                c_end = c.get('end_date')
                if not c_start or not c_end:
                    continue
                # Clip contract span to the visible range
                start_day = max(visible_start, c_start)
                end_day = min(visible_end, c_end)
                if end_day < start_day:
                    continue

                # Compose a friendly title: Employee Name [HH:MM-HH:MM]
                title_parts = []
                name = c.get('employee_name')
                if name:
                    title_parts.append(name)
                time_in = c.get('time_in')
                time_out = c.get('time_out')
                if time_in or time_out:
                    try:
                        tin = time_in.strftime('%H:%M') if hasattr(time_in, 'strftime') else str(time_in)
                        tout = time_out.strftime('%H:%M') if hasattr(time_out, 'strftime') else str(time_out)
                        title_parts.append(f"{tin or ''}-{tout or ''}")
                    except Exception:
                        pass
                title = ' '.join(filter(None, title_parts)) or c.get('title') or 'Contract'

                contract_id = c.get('id')
                bg_color = color_map.get(contract_id, 0xD6EAF8)

                # Emit one entry per day
                current = start_day
                while current <= end_day:
                    date_key = f"{current.year:04d}-{current.month:02d}-{current.day:02d}"
                    grouped.setdefault(date_key, []).append({
                        'id': contract_id,
                        'date': date_key,
                        'title': title,
                        'status': c.get('status', 'active'),
                        'color': bg_color,
                    })
                    current += timedelta(days=1)

            self.calendar_data = grouped
        except Exception as e:
            self.logger.error(f"Error loading employee contracts: {e}")
            self.logger.error(traceback.format_exc())
            self.calendar_data = {}

