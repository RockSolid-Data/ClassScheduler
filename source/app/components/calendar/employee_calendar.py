from librepy.app.components.calendar.calendar_view import Calendar


class EmployeeCalendar(Calendar):
    """
    Employee Calendar component.

    For now, this is an empty calendar that inherits the base month grid and
    scrolling mechanics from Calendar but does not load or render any entries.
    """

    # Unique component name used for routing/navigation
    component_name = 'employee_calendar'

    def __init__(self, parent, ctx, smgr, frame, ps):
        super().__init__(parent, ctx, smgr, frame, ps)

    # ------------------------------
    # Hook implementations (no-op)
    # ------------------------------
    def load_calendar_data(self):
        """No-op: Do not load any data for now."""
        # Ensure the expected attribute exists even if empty
        try:
            self.calendar_data = {}
        except Exception:
            # calendar_view already guards against missing data, but keep safe
            pass
        return

    def _render_single_entry(self, entry_name, title, x, y, w, h, row_index):
        """No-op: Intentionally do not render any entries."""
        return None

    def _render_entries_for_day(self, date, x, base_y, cell_width, row_index):
        """No-op: Intentionally do not render any entries for any day."""
        return
