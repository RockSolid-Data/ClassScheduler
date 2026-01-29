from librepy.tools.calendar.calendar import Calendar
from librepy.app.data.dao.training_session_dao import TrainingSessionDAO
from librepy.app.components.training_session.training_session_entry_dlg import TrainingSessionEntryDlg
from librepy.app.components.service_appointment.print_list_date_range_dlg import (
    PrintListDateRangeDialog,
)
from datetime import datetime
import traceback


class TrainingSessionsCalendar:
    """
    Calendar specialized for training sessions.

    Uses the new Calendar base class with callback-based architecture
    to display training sessions.
    """

    # Keep the same component name so route/screen stays unchanged
    component_name = 'calendar'

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
                'label': 'New Session',
                'callback': self._on_new_session_clicked,
                'color': 0x2C3E50,
                'text_color': 0xFFFFFF
            },
            {
                'label': 'Print List',
                'callback': self._on_print_list_clicked,
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
            calendar_title="Training Sessions",
            default_view="Month",
            toolbar_offset=self.toolbar_offset,
            background_color=bg_color,
            calendar_grid_bg_color=calendar_grid_bg_color
        )
        
        self.logger.info("TrainingSessionsCalendar initialized")

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
            dao = TrainingSessionDAO(self.logger)
            sessions = dao.get_sessions_between(start_date, end_date)

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
                    'title': s.get('title'),
                    'start_time': dt if isinstance(dt, datetime) else datetime.strptime(date_key, '%Y-%m-%d'),
                    'color': 0x72ab8a,
                }
                grouped.setdefault(date_key, []).append(s_norm)

            return grouped
        except Exception as e:
            self.logger.error(f"Error loading training sessions: {e}")
            self.logger.error(traceback.format_exc())
            return {}
    
    def _get_filter_options(self):
        """Return list of filter options for the filter dropdown."""
        return ["All"]
    
    def _get_item_color(self, item):
        """Determine color based on item properties."""
        return item.get('color', 0x72ab8a)
    
    def _on_item_click(self, item_id, item):
        """Handle item click - open edit dialog for the training session."""
        try:
            if item_id is None:
                return
            
            dlg = TrainingSessionEntryDlg(
                self, self.ctx, self.smgr, self.frame, self.ps, 
                Title="Edit Training Session", 
                session_id=item_id
            )
            ret = dlg.execute()
            if ret == 1 or ret == 2:
                self.refresh_data()
        except Exception as e:
            self.logger.error(f"Failed to open Training Session for edit (id={item_id}): {e}")
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

    def _on_print_list_clicked(self, event):
        """Open a dialog to select date range and print training sessions list."""
        try:
            dlg = PrintListDateRangeDialog(
                self, self.ctx, self.smgr, self.frame, self.ps, 
                Title="Print List"
            )
            ret = dlg.execute()
            if ret == 1:
                start_date = dlg.selected_start_date
                end_date = dlg.selected_end_date
                if not start_date or not end_date:
                    self.logger.warning("Print List: start and end dates are required")
                    return
                    
                from librepy.jasper_report.print_training_sessions_list import (
                    print_training_sessions_list,
                )
                self.logger.info(
                    f"Printing Training Sessions list for date range: start={start_date}, end={end_date}"
                )
                print_training_sessions_list(start_date, end_date)
                self.logger.info("Training Sessions list report invoked")
        except Exception as e:
            self.logger.error(f"Failed opening Print List dialog: {e}")
            self.logger.error(traceback.format_exc())

    def _on_new_session_clicked(self, event):
        """Open dialog to create a new training session and refresh on success."""
        try:
            dlg = TrainingSessionEntryDlg(
                self, self.ctx, self.smgr, self.frame, self.ps, 
                Title="New Training Session"
            )
            ret = dlg.execute()
            if ret == 1:
                self.refresh_data()
                # TODO: Refine in list too
                new_id = getattr(dlg, 'last_saved_id', None)
                if new_id:
                    dlg2 = TrainingSessionEntryDlg(
                        self, self.ctx, self.smgr, self.frame, self.ps, 
                        Title="Edit Training Session", 
                        session_id=new_id
                    )
                    ret2 = dlg2.execute()
                    if ret2 in (1, 2):
                        self.refresh_data()
        except Exception as e:
            self.logger.error(f"Failed to open Training Session dialog: {e}")
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
                self.logger.info("Disposing TrainingSessionsCalendar")
            
            if self.calendar:
                self.calendar.dispose()
                self.calendar = None
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during TrainingSessionsCalendar disposal: {e}")
                self.logger.error(traceback.format_exc())

