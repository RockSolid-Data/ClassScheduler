#coding:utf-8
# Author:  Josiah Aguilar
# Purpose: Main calendar class that manages header UI and view switching
# Created: 2025-11-13

from librepy.pybrex import ctr_container
from com.sun.star.awt.PosSize import POSSIZE
from librepy.pybrex.listeners import Listeners
from com.sun.star.awt.WindowClass import SIMPLE
from com.sun.star.awt.VclWindowPeerAttribute import CLIPCHILDREN
from com.sun.star.awt.WindowAttribute import SHOW
import traceback
from datetime import datetime

class Calendar(ctr_container.Container):
    """
    Base Calendar class that manages header UI and view switching.
    
    Developers can inherit from this class and only provide data callbacks.
    The header (title, filter, action buttons, view selector, navigation) is 
    managed automatically, and view switching happens seamlessly.
    
    Views (Month/Week/Day) are created on demand and properly disposed when switching.
    
    ============================================================================
    USAGE EXAMPLE
    ============================================================================
    
    Basic Implementation:
    ---------------------
    
    from librepy.tools.calendar.calendar import Calendar
    from datetime import datetime, timedelta
    
    class MyCalendarComponent:
        def __init__(self, parent, ctx, smgr, frame, ps):
            # Define optional action buttons
            action_buttons = [
                {
                    'label': '+ Create Event',
                    'callback': self.create_event,
                    'color': 0x2C3E50
                }
            ]
            
            # Initialize calendar
            self.calendar = Calendar(
                parent=parent,
                ctx=ctx,
                smgr=smgr,
                frame=frame,
                ps=ps,
                get_items_callback=self._get_items,
                get_filter_options_callback=self._get_filters,
                get_item_color_callback=self._get_item_color,
                on_item_click_callback=self._on_item_click,
                filter_label="Team",
                action_buttons=action_buttons,
                calendar_title="Team Calendar",
                default_view="Month",
                toolbar_offset=0
            )
        
        def _get_items(self, start_date, end_date, filter_value):
            '''
            Load and return calendar items for the date range.
            
            Args:
                start_date (datetime): Start of date range
                end_date (datetime): End of date range
                filter_value (str): Current filter selection (e.g., "All", "Team A")
            
            Returns:
                dict: {
                    '2025-01-15': [
                        {
                            'id': 'meeting_123',
                            'title': 'Team Standup',
                            'start_time': datetime(2025, 1, 15, 9, 0),
                            'end_time': datetime(2025, 1, 15, 10, 0),
                            'duration_hours': 1.0,
                            'color': 0x3498DB,  # Optional
                            'type': 'meeting',   # Your custom fields
                        },
                        ...
                    ]
                }
            '''
            items_by_date = {}
            
            # Example: Load from database
            # events = self.database.get_events(start_date, end_date, filter_value)
            
            # Example: Generate test data
            current = start_date
            while current <= end_date:
                date_str = current.strftime('%Y-%m-%d')
                items_by_date[date_str] = [
                    {
                        'id': f'event_{date_str}',
                        'title': 'Sample Event',
                        'start_time': current.replace(hour=9, minute=0),
                        'duration_hours': 2.0,
                        'type': 'meeting'
                    }
                ]
                current += timedelta(days=1)
            
            return items_by_date
        
        def _get_filters(self):
            '''Return list of filter options for dropdown'''
            return ["All", "Team A", "Team B", "Events"]
        
        def _get_item_color(self, item):
            '''Determine color based on item properties'''
            type_colors = {
                'meeting': 0x3498DB,   # Blue
                'deadline': 0xE74C3C,  # Red
                'event': 0x9B59B6      # Purple
            }
            return type_colors.get(item.get('type'), 0x95A5A6)
        
        def _on_item_click(self, item_id, item):
            '''Handle item click - open editor, show details, etc.'''
            print(f"Clicked: {item['title']}")
            # self.open_editor(item_id)
        
        def create_event(self, event):
            '''Handle create event button'''
            # Open your event creation dialog
            pass
    
    ============================================================================
    
    Advanced Example - Multi-Day Events:
    ------------------------------------
    
    def _get_items(self, start_date, end_date, filter_value):
        items_by_date = {}
        
        # Get multi-day events from database
        events = self.db.get_events(start_date, end_date)
        
        for event in events:
            # Span event across multiple days
            current_date = event.start_date
            while current_date <= event.end_date:
                date_str = current_date.strftime('%Y-%m-%d')
                
                if date_str not in items_by_date:
                    items_by_date[date_str] = []
                
                # Adjust start_time for subsequent days
                if current_date == event.start_date:
                    start_time = event.start_time
                else:
                    start_time = datetime.combine(current_date, datetime.min.time())
                
                items_by_date[date_str].append({
                    'id': event.id,
                    'title': event.title,
                    'start_time': start_time,
                    'color': event.color
                })
                
                current_date += timedelta(days=1)
        
        return items_by_date
    
    ============================================================================
    
    Item Data Structure:
    -------------------
    
    Required Fields:
        - id (str): Unique identifier
        - title (str): Display text
        - start_time (datetime): Event start (with time for Week/Day views)
    
    Optional Fields:
        - end_time (datetime): Event end
        - duration_hours (float): Duration in hours
        - color (int): Color override (hex, e.g., 0x3498DB)
        - Any custom fields your app needs (preserved in callbacks)
    
    Example Item:
    {
        'id': 'evt_123',
        'title': 'Project Review',
        'start_time': datetime(2025, 1, 15, 14, 0),
        'end_time': datetime(2025, 1, 15, 16, 0),
        'duration_hours': 2.0,
        'color': 0x3498DB,
        'type': 'meeting',
        'location': 'Room 401',
        'attendees': ['user1', 'user2']
    }
    
    ============================================================================
    
    View Configuration:
    ------------------
    
    Week/Day View Time Range (edit in week_calendar.py or day_calendar.py):
    
    self.week_config = {
        'start_hour': 6,       # 6 AM
        'end_hour': 21,        # 9 PM
        'hour_height': 80,     # Height per hour in pixels
        'time_label_width': 70,
        'colors': {
            'header_bg': 0xE0E0E0,
            'today_header_bg': 0x3498DB,
            'item_default': 0x3498DB
        }
    }
    
    Month View Settings (edit in month_calendar.py):
    
    self.calendar_config = {
        'day_label_height': 25,
        'item_button_height': 20,
        'item_button_spacing': 2,
        'item_font_size': 9,
        'colors': {
            'day_label_bg': 0xF8F8F8,
            'today_bg': 0xFFE5E5
        }
    }
    
    ============================================================================
    """
    
    def __init__(self, parent, ctx, smgr, frame, ps,
                 get_items_callback=None,
                 get_filter_options_callback=None,
                 get_item_color_callback=None,
                 on_item_click_callback=None,
                 filter_label="Filter",
                 action_buttons=None,
                 calendar_title="Calendar",
                 default_view="Month",
                 toolbar_offset=0,
                 **kwargs):
        
        self.parent = parent
        self.ctx = ctx
        self.smgr = smgr
        self.frame = frame
        self.ps = ps
        self.listeners = Listeners()
        self.logger = parent.logger if hasattr(parent, 'logger') else None
        
        # Callback functions - these will be passed to views
        self.get_items_callback = get_items_callback
        self.get_filter_options_callback = get_filter_options_callback
        self.get_item_color_callback = get_item_color_callback
        self.on_item_click_callback = on_item_click_callback
        
        # Configuration
        self.filter_label = filter_label
        self.action_buttons = action_buttons or []
        self.calendar_title = calendar_title
        self.toolbar_offset = toolbar_offset
        self.default_view = default_view
        
        # State
        self.current_date = datetime.now()
        self.selected_filter = None
        self.current_view_type = default_view
        self.current_view = None  # Will hold MonthCalendar/WeekCalendar/DayCalendar instance
        self.current_view_window = None  # Will hold the child container window for the view
        
        # UI elements
        self.view_selector = None
        self.filter_dropdown = None
        self.lbl_date = None
        self.lbl_filter = None
        self.action_button_controls = []
        
        # Store layout constants for resize calculations
        self.layout_constants = {
            'left_margin': 40,
            'right_margin': 50,
            'button_spacing': 10,
            'view_selector_width': 140,
            'action_button_width': 140,
            'filter_width': 200,
            'nav_height': 30,
            'top_height': 30
        }
        
        # Use available area passed from parent
        container_ps = ps
        # Get background color from kwargs or use default
        self.background_color = kwargs.get('background_color', 0xF4F5F7)
        # Get calendar grid background color from kwargs or use default
        self.calendar_grid_bg_color = kwargs.get('calendar_grid_bg_color', 0xFFFFFF)
        super().__init__(
            ctx, 
            smgr, 
            frame.window,
            container_ps,
            background_color=self.background_color
        )
        
        # Store initial container size
        self.window_width = ps[2]
        self.window_height = ps[3]
        
        # Create header UI
        self._create_header()
        
        # Create initial view
        self.switch_view(default_view)
        
        self.show()
    
    def _create_header(self):
        """Create the common header UI (view selector, filter, action buttons, title, navigation)"""
        top_y = 20
        
        # Use layout constants
        left_margin = self.layout_constants['left_margin']
        right_margin = self.layout_constants['right_margin']
        button_spacing = self.layout_constants['button_spacing']
        top_height = self.layout_constants['top_height']
        
        # View selector dropdown (top right corner)
        view_selector_width = self.layout_constants['view_selector_width']
        view_selector_y = 10
        view_selector_x = self.window_width - view_selector_width - right_margin
        nav_height = self.layout_constants['nav_height']
        
        self.view_selector = self.add_combo(
            "cmbViewSelector",
            view_selector_x, view_selector_y, view_selector_width, nav_height,
            BackgroundColor=0xFFFFFF,
            FontHeight=11,
            Dropdown=True
        )
        
        # Populate view options
        self.view_selector.Model.StringItemList = ("Month", "Week", "Day")
        self.view_selector.setText(self.default_view)
        
        # Add listener for view changes
        self.listeners.add_item_listener(self.view_selector, self.on_view_changed)
        
        # Navigation controls
        nav_start_x = left_margin
        title_y = 15
        nav_y = title_y + 35
        nav_button_width = 50
        today_button_width = 70
        date_label_width = 300
        nav_spacing = 10
        
        # Calculate positions from right to left for action buttons
        action_button_width = self.layout_constants['action_button_width']
        filter_width = self.layout_constants['filter_width']
        
        # Separate print button from other action buttons
        print_button = None
        other_buttons = []
        
        for button_config in self.action_buttons:
            if 'print' in button_config.get('label', '').lower():
                print_button = button_config
            else:
                other_buttons.append(button_config)
        
        # Start from the right edge and work backwards
        current_x = self.window_width - right_margin
        
        # Print button (far right)
        if print_button:
            current_x -= action_button_width
            btn_name = "btnPrint"
            btn = self.add_button(
                btn_name,
                current_x, nav_y, action_button_width, top_height,
                Label=print_button.get('label', 'Print'),
                callback=print_button.get('callback', None),
                BackgroundColor=print_button.get('color', 0x2C3E50),
                TextColor=print_button.get('text_color', 0xFFFFFF),
                FontWeight=150,
                FontHeight=11,
                Border=6
            )
            self.action_button_controls.append(btn)
            current_x -= button_spacing
        
        # Other action buttons
        for i, button_config in enumerate(reversed(other_buttons)):
            current_x -= action_button_width
            btn_name = f"btnAction{i}"
            btn = self.add_button(
                btn_name,
                current_x, nav_y, action_button_width, top_height,
                Label=button_config.get('label', 'Button'),
                callback=button_config.get('callback', None),
                BackgroundColor=button_config.get('color', 0x2C3E50),
                TextColor=button_config.get('text_color', 0xFFFFFF),
                FontWeight=150,
                FontHeight=11,
                Border=6
            )
            self.action_button_controls.append(btn)
            current_x -= button_spacing
        
        # Filter dropdown (leftmost in the top row group)
        if self.get_filter_options_callback:
            current_x -= filter_width
            
            # Filter label above dropdown
            self.lbl_filter = self.add_label(
                "lblFilter",
                current_x, nav_y - 25, filter_width, 20,
                Label=self.filter_label + ":",
                FontHeight=11,
                FontWeight=150,
                BackgroundColor=self.background_color,
                TextColor=0x2D3748,
                FontName='DejaVu Sans'
            )
            
            self.filter_dropdown = self.add_combo(
                "cmbFilter",
                current_x, nav_y, filter_width, nav_height,
                BackgroundColor=0xFFFFFF,
                FontHeight=11,
                Dropdown=True
            )
            
            # Add the listener
            self.listeners.add_item_listener(self.filter_dropdown, self.on_filter_changed)
            
            # Set filter dropdown items
            self._update_filter_dropdown()
        
        # Title
        title_width = today_button_width + nav_spacing + nav_button_width + nav_button_width + nav_spacing + date_label_width
        title_x = left_margin
        
        self.lbl_title = self.add_label(
            "lblTitle", 
            title_x, title_y, title_width, 35, 
            Label=self.calendar_title, 
            BackgroundColor=self.background_color,
            TextColor=0x2D3748,
            FontHeight=16, 
            FontWeight=150, 
            FontName='DejaVu Sans',
            Align=0
        )
        
        # Today button (leftmost)
        self.btn_today = self.add_button(
            "btnToday",
            nav_start_x, nav_y, today_button_width, nav_height,
            Label="Today",
            callback=self.go_to_today,
            BackgroundColor=0x2C3E50,
            TextColor=0xFFFFFF,
            FontWeight=150,
            FontHeight=11,
            Border=6
        )
        
        # Previous period button
        prev_x = nav_start_x + today_button_width + nav_spacing + 25
        self.btn_prev = self.add_button(
            "btnPrev",
            prev_x, nav_y, nav_button_width, nav_height,
            Label="<",
            callback=self.prev_period,
            BackgroundColor=0x2C3E50,
            TextColor=0xFFFFFF,
            FontWeight=150,
            FontHeight=14,
            Border=6
        )
        
        # Next period button
        next_x = prev_x + nav_button_width + 3
        self.btn_next = self.add_button(
            "btnNext",
            next_x, nav_y, nav_button_width, nav_height,
            Label=">",
            callback=self.next_period,
            BackgroundColor=0x2C3E50,
            TextColor=0xFFFFFF,
            FontWeight=150,
            FontHeight=14,
            Border=6
        )
        
        # Date label (changes based on view)
        date_x = next_x + nav_button_width + 25
        date_text = self.current_date.strftime("%B %Y")
        
        self.lbl_date = self.add_label(
            "lblDate",
            date_x, nav_y, date_label_width, nav_height,
            Label=date_text,
            FontHeight=22,
            BackgroundColor=self.background_color,
            TextColor=0x2D3748,
            FontWeight=150,
            FontName='DejaVu Sans',
            Align=0
        )
        
        if self.logger:
            self.logger.info("Calendar header created successfully")
    
    def _update_filter_dropdown(self):
        """Update filter dropdown with options from callback"""
        try:
            if not self.get_filter_options_callback or not hasattr(self, 'filter_dropdown'):
                return
            
            filter_options = self.get_filter_options_callback()
            self.filter_dropdown.Model.StringItemList = tuple(filter_options)
            
            # Set initial selection
            if filter_options and len(filter_options) > 0:
                self.selected_filter = filter_options[0]
                self.filter_dropdown.setText(self.selected_filter)
            
            if self.logger:
                self.logger.info(f"Updated filter dropdown with {len(filter_options)} options")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error updating filter dropdown: {e}")
    
    def _get_view_container_bounds(self):
        """Return (x, y, width, height) for the view rendering area"""
        x = 40
        y = 100
        width = self.window_width - 90
        height = self.window_height - 130
        return (x, y, width, height)
    
    def create_view_child_window(self, ps):
        """Create a child window within the calendar container.
        
        This creates a child window that is a child of the calendar's container,
        not a sibling. This ensures proper z-order and hierarchy.
        
        Args:
            ps (tuple): Position and size (x, y, width, height)
            
        Returns:
            Window: Created UNO window instance
        """
        from com.sun.star.awt import WindowDescriptor, Rectangle
        
        toolkit = self.smgr.createInstanceWithContext("com.sun.star.awt.Toolkit", self.ctx)
        descriptor = WindowDescriptor()
        descriptor.Type = SIMPLE
        descriptor.WindowServiceName = 'dockingwindow'
        descriptor.Parent = self.container.getPeer()  # Use the peer (XWindowPeer interface)!
        descriptor.ParentIndex = -1  # Append as last child (on top)
        descriptor.Bounds = Rectangle(*ps)
        descriptor.WindowAttributes = CLIPCHILDREN | SHOW
        
        window = toolkit.createWindow(descriptor)
        
        if self.logger:
            self.logger.info(f"Created child window within calendar container at {ps}")
        
        return window
    
    def switch_view(self, view_type):
        """Switch between Month, Week, Day views with proper cleanup"""
        try:
            if self.logger:
                self.logger.info(f"Switching to {view_type} view")
            
            # Dispose current view
            self._dispose_current_view()
            
            # Set current view type BEFORE updating UI to prevent listener from triggering duplicate switch
            self.current_view_type = view_type
            
            # Update view selector
            if self.view_selector:
                self.view_selector.setText(view_type)
            
            # Create new view
            if view_type == "Month":
                self.current_view = self._create_month_view()
            elif view_type == "Week":
                self.current_view = self._create_week_view()
            elif view_type == "Day":
                self.current_view = self._create_day_view()
            else:
                if self.logger:
                    self.logger.error(f"Unknown view type: {view_type}")
                return
            
            # Update date label format based on view
            self.update_date_label()
            
            if self.logger:
                self.logger.info(f"Successfully switched to {view_type} view")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error switching view: {e}")
                self.logger.error(traceback.format_exc())
    
    def _dispose_current_view(self):
        """Properly dispose the current view's UI elements"""
        if self.current_view:
            try:
                if self.logger:
                    self.logger.info(f"Disposing {self.current_view_type} view")
                
                # Call view's dispose method first
                if hasattr(self.current_view, 'dispose'):
                    self.current_view.dispose()
                
                # Clear view reference
                self.current_view = None
                
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error disposing view: {e}")
                    self.logger.error(traceback.format_exc())
        
        # Dispose the child container window (this removes all controls at once)
        if self.current_view_window:
            try:
                self.current_view_window.dispose()
                self.current_view_window = None
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error disposing view window: {e}")
    
    def _create_month_view(self):
        """Create and return MonthCalendar view"""
        from librepy.tools.calendar.month_calendar import MonthCalendar
        
        if self.logger:
            self.logger.info("Creating Month view")
        
        # Get view area bounds
        x, y, width, height = self._get_view_container_bounds()
        
        # Create child window using our method (parent is calendar.container)
        view_window = self.create_view_child_window((x, y, width, height))
        
        # Make sure the child window is visible
        view_window.setVisible(True)
        
        if self.logger:
            self.logger.info(f"Created child window at ({x}, {y}) size {width}x{height}, visible: {view_window.isVisible()}")
        
        # Create view with its own container
        view = MonthCalendar(
            ctx=self.ctx,
            smgr=self.smgr,
            window=view_window,
            parent=self,
            start_date=self.current_date
        )
        
        self.current_view_window = view_window
        return view
    
    def _create_week_view(self):
        """Create and return WeekCalendar view"""
        from librepy.tools.calendar.week_calendar import WeekCalendar
        
        if self.logger:
            self.logger.info("Creating Week view")
        
        # Get view area bounds
        x, y, width, height = self._get_view_container_bounds()
        
        # Create child window using our method (parent is calendar.container)
        view_window = self.create_view_child_window((x, y, width, height))
        
        # Create view with its own container
        view = WeekCalendar(
            ctx=self.ctx,
            smgr=self.smgr,
            window=view_window,
            parent=self,
            start_date=self.current_date
        )
        
        self.current_view_window = view_window
        return view
    
    def _create_day_view(self):
        """Create and return DayCalendar view"""
        from librepy.tools.calendar.day_calendar import DayCalendar
        
        if self.logger:
            self.logger.info("Creating Day view")
        
        # Get view area bounds
        x, y, width, height = self._get_view_container_bounds()
        
        # Create child window using our method (parent is calendar.container)
        view_window = self.create_view_child_window((x, y, width, height))
        
        # Create view with its own container
        view = DayCalendar(
            ctx=self.ctx,
            smgr=self.smgr,
            window=view_window,
            parent=self,
            start_date=self.current_date
        )
        
        self.current_view_window = view_window
        return view
    
    def on_view_changed(self, event):
        """Handle view selector dropdown change"""
        try:
            selected_view = self.view_selector.getText()
            
            if selected_view == self.current_view_type:
                return
            
            self.switch_view(selected_view)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in view change handler: {e}")
                self.logger.error(traceback.format_exc())
    
    def on_filter_changed(self, event):
        """Handle filter change - reload current view with new filter"""
        try:
            if hasattr(self, 'filter_dropdown'):
                selected_text = self.filter_dropdown.getText()
                if self.logger:
                    self.logger.info(f"Filter changed to: {selected_text}")
                self.selected_filter = selected_text
                
                # Reload current view with new filter
                if self.current_view and hasattr(self.current_view, 'reload_data'):
                    self.current_view.selected_filter = selected_text
                    self.current_view.reload_data()
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in filter change handler: {e}")
                self.logger.error(traceback.format_exc())
    
    def prev_period(self, event):
        """Navigate backward (month/week/day depending on view)"""
        try:
            if self.current_view and hasattr(self.current_view, 'navigate_prev'):
                self.current_view.navigate_prev()
                self.current_date = self.current_view.current_date
                self.update_date_label()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error navigating to previous period: {e}")
    
    def next_period(self, event):
        """Navigate forward (month/week/day depending on view)"""
        try:
            if self.current_view and hasattr(self.current_view, 'navigate_next'):
                self.current_view.navigate_next()
                self.current_date = self.current_view.current_date
                self.update_date_label()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error navigating to next period: {e}")
    
    def go_to_today(self, event):
        """Navigate to current period"""
        try:
            if self.current_view and hasattr(self.current_view, 'navigate_to_today'):
                self.current_view.navigate_to_today()
                self.current_date = self.current_view.current_date
                self.update_date_label()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error navigating to today: {e}")
    
    def update_date_label(self, custom_text=None):
        """Update the date label based on current view and date"""
        try:
            if not self.lbl_date:
                return
            
            if custom_text:
                self.lbl_date.Model.Label = custom_text
                return
            
            # Format based on view type
            if self.current_view_type == "Month":
                date_text = self.current_date.strftime("%B %Y")
            elif self.current_view_type == "Week":
                # Get week range from view if available
                if hasattr(self.current_view, '_get_week_range'):
                    week_start, week_end = self.current_view._get_week_range()
                    
                    # Check if week spans one or two months
                    if week_start.month == week_end.month:
                        # Same month: "November 2025"
                        date_text = week_start.strftime("%B %Y")
                    else:
                        # Different months: "Nov - Dec 2025"
                        date_text = f"{week_start.strftime('%b')} - {week_end.strftime('%b %Y')}"
                else:
                    date_text = self.current_date.strftime("%B %Y")
            elif self.current_view_type == "Day":
                # Format: "November 13, 2025"
                date_text = self.current_date.strftime("%B %d, %Y")
            else:
                date_text = self.current_date.strftime("%B %Y")
            
            self.lbl_date.Model.Label = date_text
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error updating date label: {e}")
    
    def _reposition_header_controls(self):
        """Reposition right-aligned header controls based on current window width"""
        try:
            right_margin = self.layout_constants['right_margin']
            button_spacing = self.layout_constants['button_spacing']
            action_button_width = self.layout_constants['action_button_width']
            filter_width = self.layout_constants['filter_width']
            view_selector_width = self.layout_constants['view_selector_width']
            top_height = self.layout_constants['top_height']
            nav_y = 50  # title_y (15) + 35
            
            # Reposition view selector (top right corner)
            if self.view_selector:
                view_selector_x = self.window_width - view_selector_width - right_margin
                self.view_selector.setPosSize(view_selector_x, 10, view_selector_width, 25, POSSIZE)
            
            # Start from the right edge and work backwards for action buttons
            current_x = self.window_width - right_margin
            
            # Reposition action buttons (working right to left, print button first)
            # action_button_controls is ordered: [print_button, other_buttons...]
            # So iterate normally to place print button furthest right
            for btn in self.action_button_controls:
                current_x -= action_button_width
                btn.setPosSize(current_x, nav_y, action_button_width, top_height, POSSIZE)
                current_x -= button_spacing
            
            # Reposition filter dropdown and label (leftmost of the right-aligned group)
            if self.filter_dropdown:
                current_x -= filter_width
                self.filter_dropdown.setPosSize(current_x, nav_y, filter_width, top_height, POSSIZE)
                
                if self.lbl_filter:
                    self.lbl_filter.setPosSize(current_x, nav_y - 25, filter_width, 20, POSSIZE)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error repositioning header controls: {e}")
                self.logger.error(traceback.format_exc())
    
    def resize(self, width, height):
        """Handle window resize events"""
        try:
            # Update stored dimensions
            self.window_width = width
            self.window_height = height - self.toolbar_offset
            
            # Resize the main container
            sidebar_width = getattr(self.parent, 'sidebar_width', 0)
            
            self.container.setPosSize(
                sidebar_width,
                self.toolbar_offset,
                width, 
                height - self.toolbar_offset,
                POSSIZE
            )
            
            # Reposition right-aligned header controls
            self._reposition_header_controls()
            
            # Resize the child window if it exists
            if self.current_view_window:
                x, y, view_width, view_height = self._get_view_container_bounds()
                self.current_view_window.setPosSize(x, y, view_width, view_height, POSSIZE)
                
                if self.logger:
                    self.logger.debug(f"Resized view window to {view_width}x{view_height}")
                
                # Notify the current view to resize its contents
                if self.current_view and hasattr(self.current_view, 'resize'):
                    self.current_view.resize(view_width, view_height)
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during resize: {e}")
                self.logger.error(traceback.format_exc())
    
    def dispose(self):
        """Dispose of all controls and calendar components"""
        try:
            if self.logger:
                self.logger.info("Disposing of Calendar")
            
            # Dispose current view
            self._dispose_current_view()
            
            # Dispose container
            if hasattr(self, 'container') and self.container is not None:
                try:
                    self.container.dispose()
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error disposing container: {str(e)}")
                finally:
                    self.container = None
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during disposal: {e}")
                self.logger.error(traceback.format_exc())

