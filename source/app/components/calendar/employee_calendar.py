from librepy.app.components.calendar.calendar_view import Calendar
from librepy.app.data.dao.employee_contract_dao import EmployeeContractDAO
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
        """Subclass callback for Print button (placeholder)."""
        self.logger.info("Print requested (EmployeeCalendar) - not implemented yet")

    def on_new_entry(self, event):
        """Subclass callback for New Entry button (placeholder)."""
        self.logger.info("New Entry requested (EmployeeCalendar) - not implemented yet")

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

    def _render_single_entry(self, entry_name, title, x, y, w, h, row_index, bg_color=None):
        """Create a pill-like label control and cache its base position."""
        pill = self.add_label(
            entry_name,
            x, y, w, h,
            Label=str(title or ''),
            FontHeight=10,
            FontWeight=150,
            TextColor=0x222222,
            BackgroundColor=bg_color,
            Border=0
        )
        self.entry_labels[entry_name] = pill
        self._base_positions[entry_name] = (x, y, w, h, row_index)
        return pill

    def _render_entries_for_day(self, date, x, base_y, cell_width, row_index):
        """Render all contract pills for a specific date."""
        cfg = self.calendar_config
        day_label_height = cfg['day_label_height']
        entry_height = cfg.get('entry_height', 24)
        entry_spacing = cfg.get('entry_spacing', 4)
        entry_margin_x = cfg.get('entry_margin_x', 4)

        date_key = f"{date.year:04d}-{date.month:02d}-{date.day:02d}"
        entries_for_day = self.calendar_data.get(date_key, [])
        for idx, entry in enumerate(entries_for_day):
            pill_name = f"pill_{date.day}{date.month}{date.year}_{entry['id']}"
            pill_x = x + entry_margin_x
            pill_y = base_y + day_label_height + entry_spacing + idx * (entry_height + entry_spacing)
            pill_w = cell_width - 2 * entry_margin_x
            pill_h = entry_height
            self._render_single_entry(
                pill_name,
                entry.get('title'),
                pill_x,
                pill_y,
                pill_w,
                pill_h,
                row_index,
                entry.get('color')
            )
