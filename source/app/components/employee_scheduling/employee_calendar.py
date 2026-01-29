from librepy.tools.calendar.calendar import Calendar
from librepy.app.data.dao.employee_contract_dao import EmployeeContractDAO
from librepy.app.components.employee_scheduling.employee_contract_dlg import EmployeeContractDialog
from librepy.app.utils.utils import is_allowed
from datetime import datetime, timedelta
import traceback
import colorsys


class EmployeeCalendar:
    """
    Employee Calendar component.

    Uses the new Calendar base class with callback-based architecture
    to display employee contract spans as daily entries.
    """

    # Unique component name used for routing/navigation
    component_name = 'employee_calendar'

    def __init__(self, parent, ctx, smgr, frame, ps):
        self.parent = parent
        self.ctx = ctx
        self.smgr = smgr
        self.frame = frame
        self.ps = ps
        self.logger = parent.logger
        
        # Toolbar offset (if any)
        self.toolbar_offset = getattr(parent, 'toolbar_offset', 0)
        
        # Define action buttons for the calendar header
        action_buttons = [
            {
                'label': 'New Contract',
                'callback': self._on_new_contract_clicked,
                'color': 0x2C3E50,
                'text_color': 0xFFFFFF
            },
            {
                'label': 'Print',
                'callback': self._on_print_clicked,
                'color': 0x2C3E50,
                'text_color': 0xFFFFFF
            }
        ]
        
        # Get background colors from theme
        bg_color = 0xF4F5F7  # Default container background
        calendar_grid_bg_color = 0xFFFFFF  # Default calendar grid background
        if hasattr(parent, 'theme_config'):
            bg_color = parent.theme_config.get_main_bg_color_int()
            calendar_grid_bg_color = parent.theme_config.get_calendar_grid_bg_color_int()
        
        # Create the calendar using the new Calendar base class
        self.calendar = Calendar(
            parent=parent,
            ctx=ctx,
            smgr=smgr,
            frame=frame,
            ps=ps,
            get_items_callback=self._get_items,
            get_filter_options_callback=self._get_filter_options,
            get_item_color_callback=self._get_item_color,
            on_item_click_callback=self._on_item_click,
            filter_label="Filter",
            action_buttons=action_buttons,
            calendar_title="Employee Contracts",
            default_view="Month",
            toolbar_offset=self.toolbar_offset,
            background_color=bg_color,
            calendar_grid_bg_color=calendar_grid_bg_color
        )
        
        self.logger.info("EmployeeCalendar initialized")

    # =========================================================================
    # CALLBACK METHODS - Required by the new Calendar base class
    # =========================================================================
    
    def _get_items(self, start_date, end_date, filter_value):
        """Load and return calendar items for the date range.
        
        Args:
            start_date (datetime): Start of date range
            end_date (datetime): End of date range
            filter_value (str): Current filter selection
        
        Returns:
            dict: Items grouped by date string 'YYYY-MM-DD'
        """
        try:
            dao = EmployeeContractDAO(self.logger)
            contracts = dao.get_contracts_between(start_date, end_date)

            # Build distinct contract id list for color mapping
            distinct_ids = []
            for c in contracts or []:
                cid = c.get('id')
                if cid is not None and cid not in distinct_ids:
                    distinct_ids.append(cid)

            # Generate a simple HSL palette sized to distinct contracts
            def hsl_color(i, n, s=0.45, l=0.82):
                if n <= 0:
                    return 0xD6EAF8
                h = (i % n) / float(n)
                r, g, b = colorsys.hls_to_rgb(h, l, s)
                R = int(round(r * 255))
                G = int(round(g * 255))
                B = int(round(b * 255))
                # Ensure sufficient brightness for dark text
                luma = 0.2126 * R + 0.7152 * G + 0.0722 * B
                if luma < 150:
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
                start_day = max(start_date.date() if hasattr(start_date, 'date') else start_date, c_start)
                end_day = min(end_date.date() if hasattr(end_date, 'date') else end_date, c_end)
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
                working_days = c.get('working_days')

                # Emit one entry per day
                current = start_day
                while current <= end_day:
                    # Check if this day is allowed by working_days mask
                    weekday_idx = current.weekday()  # Mon=0..Sun=6
                    if working_days is not None and not is_allowed(weekday_idx, int(working_days)):
                        current += timedelta(days=1)
                        continue
                    
                    date_key = f"{current.year:04d}-{current.month:02d}-{current.day:02d}"
                    
                    # Create start_time for this day
                    if time_in and hasattr(time_in, 'hour'):
                        start_time = datetime.combine(current, time_in.time() if hasattr(time_in, 'time') else time_in)
                    else:
                        start_time = datetime.combine(current, datetime.min.time())
                    
                    grouped.setdefault(date_key, []).append({
                        'id': contract_id,
                        'title': title,
                        'start_time': start_time,
                        'status': c.get('status', 'active'),
                        'color': bg_color,
                        'working_days': working_days,
                    })
                    current += timedelta(days=1)

            return grouped
        except Exception as e:
            self.logger.error(f"Error loading employee contracts: {e}")
            self.logger.error(traceback.format_exc())
            return {}
    
    def _get_filter_options(self):
        """Return list of filter options for the filter dropdown."""
        return ["All"]
    
    def _get_item_color(self, item):
        """Determine color based on item properties."""
        return item.get('color', 0xD6EAF8)
    
    def _on_item_click(self, item_id, item):
        """Handle item click - open edit dialog for the contract."""
        try:
            if item_id is None:
                return
            
            dlg = EmployeeContractDialog(
                self, self.ctx, self.smgr, self.frame, self.ps, 
                Title="Edit Employee Contract", 
                contract_id=item_id
            )
            ret = dlg.execute()
            if ret == 1 or ret == 2:
                self.refresh_data()
        except Exception as e:
            self.logger.error(f"Failed to open Employee Contract for edit (id={item_id}): {e}")
            self.logger.error(traceback.format_exc())
    
    # =========================================================================
    # ACTION BUTTON CALLBACKS
    # =========================================================================
    
    def _on_print_clicked(self, event):
        """Handle print button click - delegates to the current view's print method."""
        try:
            if self.calendar and self.calendar.current_view:
                if hasattr(self.calendar.current_view, 'print_calendar'):
                    self.calendar.current_view.print_calendar(event)
                else:
                    if self.logger:
                        self.logger.warning("Current view does not support printing")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in print callback: {e}")
                self.logger.error(traceback.format_exc())

    def _on_new_contract_clicked(self, event):
        """Open the Employee Contract dialog and refresh calendar on successful save."""
        try:
            dlg = EmployeeContractDialog(
                self, self.ctx, self.smgr, self.frame, self.ps, 
                Title="New Employee Contract"
            )
            ret = dlg.execute()
            if ret == 1:
                self.refresh_data()
        except Exception as e:
            self.logger.error(f"Failed to open Employee Contract dialog: {e}")
            self.logger.error(traceback.format_exc())
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _get_display_date_range(self):
        """Return the inclusive date range currently displayed in the calendar."""
        try:
            if not self.calendar:
                return None, None
            
            import calendar as cal_module
            current_date = self.calendar.current_date
            cal = cal_module.Calendar(6)  # Start week on Sunday
            month_days = list(cal.itermonthdates(current_date.year, current_date.month))
            
            if not month_days:
                return None, None
            
            return month_days[0], month_days[-1]
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error computing display date range: {e}")
                self.logger.error(traceback.format_exc())
            return None, None
    
    def refresh_data(self):
        """Refresh the calendar data and redraw."""
        if self.calendar and self.calendar.current_view:
            if hasattr(self.calendar.current_view, 'reload_data'):
                self.calendar.current_view.reload_data()
    
    # =========================================================================
    # COMPONENT LIFECYCLE METHODS
    # =========================================================================
    
    def show(self):
        """Show the calendar component."""
        if self.calendar:
            self.calendar.show()
    
    def hide(self):
        """Hide the calendar component."""
        if self.calendar:
            self.calendar.hide()
    
    def resize(self, width, height):
        """Handle window resize events."""
        if self.calendar:
            self.calendar.resize(width, height)
    
    def dispose(self):
        """Dispose of the calendar and clean up resources."""
        try:
            if self.logger:
                self.logger.info("Disposing EmployeeCalendar")
            
            if self.calendar:
                self.calendar.dispose()
                self.calendar = None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during EmployeeCalendar disposal: {e}")
                self.logger.error(traceback.format_exc())

