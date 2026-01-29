
#coding:utf-8
# Author:  Josiah Aguilar
# Purpose: Calendar component using the reusable Calendar base class with working days support
# Created: 2025-12-23

from librepy.tools.calendar.calendar import Calendar as BaseCalendar
#from librepy.app.service.working_days_config import WorkingDaysConfigService
from datetime import datetime, timedelta
import traceback
import calendar as cal_module


class CalendarView:
    """
    Calendar component that wraps the reusable Calendar class.
    
    Provides:
    - Month/Week/Day view switching via the base Calendar
    - Working days configuration (locked weekdays are disabled)
    - Data loading callbacks for your application
    
    Usage:
        calendar = CalendarView(parent, ctx, smgr, frame, ps)
        calendar.show()
    """
    
    component_name = 'calendar'
    
    def __init__(self, parent, ctx, smgr, frame, ps, title="Calendar"):
        self.parent = parent
        self.ctx = ctx
        self.smgr = smgr
        self.frame = frame
        self.ps = ps
        self.logger = parent.logger
        self._title_text = title
        
        # Toolbar offset (if any)
        self.toolbar_offset = getattr(parent, 'toolbar_offset', 0)
        
        # Working days configuration
        # locked_weekdays: set of weekday indices (Mon=0..Sun=6) that are locked/disabled
        self.locked_weekdays = set()
        self._load_locked_days()
        
        # Calendar data storage - items keyed by 'YYYY-MM-DD'
        self.calendar_data = {}
        
        # Define action buttons for the calendar header
        # Buttons are rendered right-to-left, so Print (rightmost) is listed last
        action_buttons = [
            {
                'label': 'New Job',
                'callback': self._on_new_job_clicked,
                'color': 0x2C3E50,
                'text_color': 0xFFFFFF
            },
            {
                'label': 'New Event',
                'callback': self._on_new_event_clicked,
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
        
        # Create the calendar using the reusable Calendar base class
        self.calendar = BaseCalendar(
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
            calendar_title=title,
            default_view="Month",
            toolbar_offset=self.toolbar_offset
        )
        
        # Store reference to locked_weekdays on calendar instance so views can access it
        self.calendar.locked_weekdays = self.locked_weekdays
        
        self.logger.info(f"CalendarView initialized with title: {title}")
    
    def _load_locked_days(self):
        """Load working days config and compute locked weekdays set.
        
        The WorkingDaysConfigService returns a list of 7 flags (Mon..Sun).
        A value of 1 means the day is locked/disabled, 0 means it's a working day.
        """
        try:
            service = WorkingDaysConfigService(self.logger)
            flags = service.load_working_days()  # list of 7 ints Mon..Sun
            
            if not isinstance(flags, (list, tuple)) or len(flags) != 7:
                self.locked_weekdays = set()
                return
            
            # Build set of locked weekday indices (1 means locked, 0 means allowed)
            locked = {idx for idx, v in enumerate(flags) if v}
            self.locked_weekdays = locked
            
            if self.logger:
                self.logger.info(f"Locked weekdays loaded: {sorted(list(self.locked_weekdays))}")
                
        except Exception as e:
            self.locked_weekdays = set()
            if self.logger:
                self.logger.debug(f"Failed to load locked weekdays: {e}")
    
    def reload_locked_days(self):
        """Reload locked days configuration and refresh the calendar.
        
        Call this when working days settings may have changed.
        """
        self._load_locked_days()
        
        # Update the calendar's reference
        if self.calendar:
            self.calendar.locked_weekdays = self.locked_weekdays
            
            # Reload the current view to reflect changes
            if self.calendar.current_view and hasattr(self.calendar.current_view, 'reload_data'):
                self.calendar.current_view.reload_data()
    
    def _is_day_locked(self, date):
        """Check if a given date falls on a locked weekday.
        
        Args:
            date: datetime or date object
            
        Returns:
            bool: True if the day is locked, False otherwise
        """
        if not self.locked_weekdays:
            return False
        
        try:
            # date.weekday() returns Mon=0..Sun=6
            return date.weekday() in self.locked_weekdays
        except Exception:
            return False
    
    # =========================================================================
    # CALLBACK METHODS - Override these in subclasses for your application
    # =========================================================================
    
    def _get_items(self, start_date, end_date, filter_value):
        """Load and return calendar items for the date range.
        
        This is the main data loading callback. Override this method in subclasses
        to load items from your data source (database, API, etc.).
        
        Items on locked weekdays are automatically filtered out.
        
        Args:
            start_date (datetime): Start of date range
            end_date (datetime): End of date range
            filter_value (str): Current filter selection (e.g., "All", or a specific filter)
        
        Returns:
            dict: Items grouped by date string 'YYYY-MM-DD'
                {
                    '2025-01-15': [
                        {
                            'id': 'item_123',
                            'title': 'Item Title',
                            'start_time': datetime(2025, 1, 15, 9, 0),
                            'color': 0x3498DB,  # Optional
                            'type': 'event',    # Optional, for color coding
                            ...  # Your custom fields
                        },
                        ...
                    ]
                }
        """
        try:
            # Load your calendar data here
            # This base implementation returns empty data - override in subclasses
            self.load_calendar_data(start_date, end_date, filter_value)
            
            # Filter out items on locked weekdays
            filtered_data = {}
            for date_str, items in self.calendar_data.items():
                try:
                    # Parse date string
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    # Skip locked days
                    if self._is_day_locked(date):
                        if self.logger:
                            self.logger.debug(f"Skipping items for locked day: {date_str}")
                        continue
                    
                    filtered_data[date_str] = items
                    
                except ValueError:
                    # If date parsing fails, include it anyway
                    filtered_data[date_str] = items
            
            return filtered_data
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in _get_items: {e}")
                self.logger.error(traceback.format_exc())
            return {}
    
    def load_calendar_data(self, start_date, end_date, filter_value):
        """Hook: Load calendar data for the specified date range.
        
        Override this method in subclasses to load data from your data source.
        Populate self.calendar_data as a dict keyed by 'YYYY-MM-DD' -> list of items.
        
        Args:
            start_date: Start of date range
            end_date: End of date range  
            filter_value: Current filter selection
            
        Base implementation: no-op, leaves self.calendar_data unchanged.
        """
        pass
    
    def _get_filter_options(self):
        """Return list of filter options for the filter dropdown.
        
        Override this method in subclasses to provide filter options.
        
        Returns:
            list: List of filter option strings
            
        Example:
            return ["All", "Type A", "Type B", "Completed"]
        """
        return ["All"]
    
    def _get_item_color(self, item):
        """Determine color based on item properties.
        
        Override this method in subclasses to customize item colors.
        
        Args:
            item (dict): The item dict containing properties
            
        Returns:
            int: Color as hex integer (e.g., 0x3498DB for blue)
        """
        # Default color scheme based on 'type' field if present
        type_colors = {
            'event': 0x3498DB,      # Blue
            'meeting': 0x9B59B6,    # Purple
            'deadline': 0xE74C3C,   # Red
            'task': 0x27AE60,       # Green
            'reminder': 0xF39C12,   # Orange
        }
        
        item_type = item.get('type', '').lower()
        return type_colors.get(item_type, 0x3498DB)  # Default blue
    
    def _on_item_click(self, item_id, item):
        """Handle item click - called when user clicks on a calendar item.
        
        Override this method in subclasses to handle item clicks
        (e.g., open an editor dialog, show details, etc.).
        
        Args:
            item_id: The item's unique identifier
            item (dict): The full item dict
        """
        if self.logger:
            self.logger.info(f"Calendar item clicked: id={item_id}, title={item.get('title', 'Unknown')}")
    
    def _on_print_clicked(self, event):
        """Handle print button click - delegates to the current view's print method.
        
        Override this method in subclasses for custom print behavior.
        """
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
    
    def _on_new_job_clicked(self, event):
        """Handle New Job button click - opens job creation dialog.
        
        Override this method in subclasses for custom job creation behavior.
        """
        if self.logger:
            self.logger.info("New Job button clicked")
        
        # Default implementation - override in subclasses to open your JobDialog
        # Example:
        # from librepy.app.components.dashboard.dialogs.job import JobDialog
        # from librepy.app.service.jobs import JobsService
        # svc = JobsService(self.logger)
        # dlg = JobDialog(self.parent, self.ctx, self.smgr, self.frame, self.ps, service=svc)
        # dlg.execute()
        # self.refresh_data()
    
    def _on_new_event_clicked(self, event):
        """Handle New Event button click - opens event creation dialog.
        
        Override this method in subclasses for custom event creation behavior.
        """
        if self.logger:
            self.logger.info("New Event button clicked")
        
        # Default implementation - override in subclasses to open your EventDialog
        # Example:
        # from librepy.app.components.job_calendar.dialogs.event import EventDialog
        # dlg = EventDialog(self.parent, self.ctx, self.smgr, self.frame, self.ps)
        # dlg.execute()
        # self.refresh_data()
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def get_display_date_range(self):
        """Return the inclusive date range currently displayed in the calendar.
        
        Uses the same logic as the month view (calendar.itermonthdates with Sunday start).
        
        Returns:
            tuple: (start_date, end_date) or (None, None) on error
        """
        try:
            if not self.calendar:
                return None, None
            
            current_date = self.calendar.current_date
            cal = cal_module.Calendar(6)  # Start week on Sunday
            month_days = list(cal.itermonthdates(current_date.year, current_date.month))
            
            if not month_days:
                return None, None
            
            start_date, end_date = month_days[0], month_days[-1]
            
            if self.logger:
                self.logger.info(f"Display date range: {start_date} - {end_date}")
            
            return start_date, end_date
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error computing display date range: {e}")
                self.logger.error(traceback.format_exc())
            return None, None
    
    def refresh_data(self):
        """Refresh the calendar data and redraw.
        
        Call this method when underlying data has changed.
        """
        if self.calendar and self.calendar.current_view:
            if hasattr(self.calendar.current_view, 'reload_data'):
                self.calendar.current_view.reload_data()
    
    def navigate_to_date(self, date):
        """Navigate the calendar to a specific date.
        
        Args:
            date: datetime or date object to navigate to
        """
        if self.calendar:
            self.calendar.current_date = date
            if self.calendar.current_view and hasattr(self.calendar.current_view, 'reload_data'):
                self.calendar.current_view.current_date = date
                self.calendar.current_view.reload_data()
            self.calendar.update_date_label()
    
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
        """Handle window resize events.
        
        Args:
            width: New width
            height: New height
        """
        if self.calendar:
            self.calendar.resize(width, height)
    
    def dispose(self):
        """Dispose of the calendar and clean up resources."""
        try:
            if self.logger:
                self.logger.info("Disposing CalendarView")
            
            if self.calendar:
                self.calendar.dispose()
                self.calendar = None
            
            self.calendar_data.clear()
            self.locked_weekdays.clear()
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during CalendarView disposal: {e}")
                self.logger.error(traceback.format_exc())


# Alias for backwards compatibility with existing imports
Calendar = CalendarView
