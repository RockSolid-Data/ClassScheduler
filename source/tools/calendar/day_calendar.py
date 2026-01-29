#coding:utf-8
# Author:  Josiah Aguilar
# Purpose: Day calendar view with single day column and hourly time slots
# Created: 2025-11-13

from com.sun.star.awt.PosSize import POSSIZE
from librepy.pybrex.ctr_container import Container
from com.sun.star.awt.ScrollBarOrientation import VERTICAL as SB_VERT
from datetime import datetime, timedelta
import traceback

class DayCalendar(Container):
    """
    Day calendar component that displays a single day with hourly time slots.
    
    Accepts callback functions for:
    - Loading calendar items
    - Getting filter options
    - Determining item colors
    - Handling item clicks
    
    Data format expected from get_items_callback:
    {
        '2025-01-15': [
            {
                'id': 'unique_id',
                'title': 'Display text',
                'start_time': datetime_obj,  # Full datetime with time
                'end_time': datetime_obj,    # Optional end time
                'duration_hours': 2.0,       # Optional duration
                'color': 0x3498DB            # Optional
            },
            ...
        ]
    }
    """
    
    def __init__(self, ctx, smgr, window, parent, start_date=None):
        """
        Initialize DayCalendar view.
        
        Args:
            ctx: Component context
            smgr: Service manager
            window: Parent window for the container
            parent: Calendar instance that manages callbacks and data
            start_date: Optional initial date to display
        """
        self.parent = parent
        self.logger = parent.logger if hasattr(parent, 'logger') else None
        
        # Day state
        self.current_date = start_date if start_date else datetime.now()
        
        # Get container bounds from parent (we only need width and height)
        x, y, width, height = parent._get_view_container_bounds()
        
        # Get calendar grid background color from parent or use default
        calendar_grid_bg = getattr(parent, 'calendar_grid_bg_color', 0xFFFFFF)
        
        # Initialize Container at (0, 0) relative to the child window
        # The child window itself is already positioned correctly
        super().__init__(
            ctx=ctx,
            smgr=smgr,
            window=window,
            ps=(0, 0, width, height),
            background_color=calendar_grid_bg
        )
        
        # Calendar data storage
        self.calendar_data = {}  # Will store items grouped by date
        self.item_buttons = {}   # Will store item button controls by date
        self.item_button_controls = {}  # Will store item button controls by name (for scrolling)
        self.day_header = None   # Store day header label
        self.time_labels = {}    # Store time labels
        self.slot_backgrounds = {}  # Store grid lines (horizontal and vertical)
        
        # Day configuration
        self.day_config = {
            'start_hour': 6,      # Start at 6 AM
            'end_hour': 21,       # End at 9 PM
            'hour_height': 80,    # Height per hour slot (same as week view)
            'time_label_width': 70,
            'header_height': 28,
            'colors': {
                'header_bg': 0xE0E0E0,
                'today_header_bg': 0x3498DB,
                'time_slot_bg': 0xFFFFFF,
                'time_slot_border': 0xDDDDDD,
                'item_default': 0x3498DB
            }
        }
        
        # Scrollbar-related properties
        self.scroll_offset = 0
        self.scrollbar = None
        self._base_positions = {}  # Store original positions: name → (x, y, w, h)
        self.hour_positions = {}  # Store dynamic hour positions: hour → (y_start, row_height)
        
        # Create scrollbar and scroll buttons
        self._create_scrollbar()
        
        # Load data and create grid
        self.load_day_data()
        self._create_day_grid()
        
        # Show the container
        self.show()
    
    def _create_scrollbar(self):
        """Create scrollbar and scroll buttons for day calendar"""
        # Get container size
        _, _, container_width, container_height = self.parent._get_view_container_bounds()
        
        # Button configuration
        button_size = 20
        button_spacing = 2
        
        # Calculate scrollbar dimensions with space for buttons
        scrollbar_width = 20
        scrollbar_x = container_width - scrollbar_width  # Right edge
        scrollbar_y = button_size + button_spacing  # Start below up button
        scrollbar_height = container_height - (2 * button_size) - (2 * button_spacing)
        
        # Create vertical scrollbar (hidden initially)
        self.scrollbar = self.add_scrollbar(
            "scrDayCalendar",
            scrollbar_x,
            scrollbar_y,
            scrollbar_width,
            scrollbar_height,
            Orientation=SB_VERT,
            Visible=False  # Hidden until needed
        )
        
        # Up scroll button
        self.btn_scroll_up = self.add_button(
            "btnScrollUp",
            scrollbar_x,
            0,  # At the very top of container
            button_size,
            button_size,
            Label="▲",
            callback=self.scroll_up,
            BackgroundColor=0xE0E0E0,
            TextColor=0x333333,
            FontHeight=10,
            FontWeight=150,
            Border=2,
            Visible=False
        )
        
        # Down scroll button
        self.btn_scroll_down = self.add_button(
            "btnScrollDown",
            scrollbar_x,
            scrollbar_y + scrollbar_height + button_spacing,
            button_size,
            button_size,
            Label="▼",
            callback=self.scroll_down,
            BackgroundColor=0xE0E0E0,
            TextColor=0x333333,
            FontHeight=10,
            FontWeight=150,
            Border=2,
            Visible=False
        )
        
        # Add scroll listener
        self.add_adjustment_listener(self.scrollbar, self.on_scroll)
    
    def _create_day_grid(self):
        """Create the day grid with time slots"""
        # Clear existing controls
        if self.day_header:
            try:
                self.day_header.dispose()
            except:
                pass
        self.day_header = None
        
        for time_name, time_label in self.time_labels.items():
            try:
                time_label.dispose()
            except:
                pass
        self.time_labels.clear()
        
        for line_name, line in self.slot_backgrounds.items():
            try:
                line.dispose()
            except:
                pass
        self.slot_backgrounds.clear()
        
        for date_str, buttons in self.item_buttons.items():
            for button in buttons:
                try:
                    button.dispose()
                except:
                    pass
        self.item_buttons.clear()
        self.item_button_controls.clear()
        
        self._base_positions.clear()
        
        # Get configuration
        time_label_width = self.day_config['time_label_width']
        hour_height = self.day_config['hour_height']
        start_hour = self.day_config['start_hour']
        end_hour = self.day_config['end_hour']
        
        # Calculate available width for day column (span entire width)
        _, _, container_width, _ = self.parent._get_view_container_bounds()
        scrollbar_space = 25
        day_column_width = container_width - time_label_width - scrollbar_space
        
        # Layout parameters
        grid_start_x = 0
        grid_start_y = 5
        
        # Create day header - TWO ROWS (day name + date number, like week view)
        header_row1_y = grid_start_y
        header_row1_height = 20
        header_row2_y = header_row1_y + header_row1_height
        header_row2_height = 20
        total_header_height = header_row1_height + header_row2_height
        
        # Create corner header (top-left, covers time column) - FROZEN
        corner_header = self.add_label(
            "lblCornerHeader",
            grid_start_x, header_row1_y,
            time_label_width, total_header_height,
            Label="Time",
            FontHeight=11,
            FontWeight=150,
            BackgroundColor=0xE0E0E0,
            TextColor=0x333333,
            FontName='DejaVu Sans',
            Align=1,
            Border=2
        )
        
        # Get day info
        day_name = self.current_date.strftime("%a")  # Short day name
        day_number = self.current_date.strftime("%d")
        
        # Highlight today
        is_today = self.current_date.date() == datetime.now().date()
        bg_color = self.day_config['colors']['today_header_bg'] if is_today else self.day_config['colors']['header_bg']
        text_color = 0xFFFFFF if is_today else 0x333333
        
        header_x = time_label_width
        
        # Row 1: Day name
        header_row1 = self.add_label(
            "lblDayName",
            header_x, header_row1_y, day_column_width, header_row1_height,
            Label=day_name,
            FontHeight=11,
            FontWeight=150,
            BackgroundColor=bg_color,
            TextColor=text_color,
            FontName='DejaVu Sans',
            Align=1,
            Border=2
        )
        
        # Row 2: Date number
        header_row2 = self.add_label(
            "lblDayDate",
            header_x, header_row2_y, day_column_width, header_row2_height,
            Label=day_number,
            FontHeight=12,
            FontWeight=150,
            BackgroundColor=bg_color,
            TextColor=text_color,
            FontName='DejaVu Sans',
            Align=1,
            Border=2
        )
        
        # Store headers (not in _base_positions so they stay frozen)
        self.day_header = (corner_header, header_row1, header_row2)
        
        # Time slots grid starts below both header rows
        time_slot_start_y = header_row2_y + header_row2_height + 2
        
        # STEP 1: Analyze hour overlaps to determine dynamic row heights
        item_height = 20  # Fixed height for each event
        item_spacing = 2  # Spacing between stacked events
        hour_overlaps = self._analyze_hour_overlaps(start_hour, end_hour)
        
        # Calculate Y position and height for each hour based on overlaps
        hour_positions = {}  # {hour: (y_start, row_height)}
        current_y = time_slot_start_y
        
        for hour in range(start_hour, end_hour + 1):
            overlaps = hour_overlaps.get(hour, 0)
            
            # Base hour height + space for overlapping items
            if overlaps > 0:
                row_height = hour_height + ((overlaps - 1) * (item_height + item_spacing))
            else:
                row_height = hour_height
            
            hour_positions[hour] = (current_y, row_height)
            current_y += row_height
        
        # Store for later use in item positioning and scrolling
        self.hour_positions = hour_positions
        
        # STEP 2: Create time labels and grid lines based on dynamic positions
        for hour in range(start_hour, end_hour + 1):
            slot_y, row_height = hour_positions[hour]
            
            # Time label (left column)
            time_str = f"{hour:02d}:00"
            time_label_name = f"lblTime{hour}"
            time_label = self.add_label(
                time_label_name,
                grid_start_x, slot_y,
                time_label_width, row_height,
                Label=time_str,
                FontHeight=11,
                FontWeight=100,
                TextColor=0x666666,
                FontName='DejaVu Sans',
                Align=2,  # Right align
                VerticalAlign=0,  # Top align
                Border=1
            )
            self.time_labels[time_label_name] = time_label
            self._base_positions[time_label_name] = (grid_start_x, slot_y, time_label_width, row_height)
            
            # Create horizontal line below this time slot (creates grid rows)
            line_name = f"lineHoriz{hour}"
            line_y = slot_y + row_height
            grid_width = time_label_width + day_column_width
            
            horiz_line = self.add_line(
                line_name,
                grid_start_x, line_y,
                grid_width, 1,
                LineColor=0xDDDDDD,
                Orientation=0  # Horizontal
            )
            self.slot_backgrounds[line_name] = horiz_line
            self._base_positions[line_name] = (grid_start_x, line_y, grid_width, 1)
        
        # Calculate total grid height based on dynamic hour positions
        total_grid_height = current_y - time_slot_start_y
        
        # Create vertical lines for day column borders (left and right edges)
        for idx in range(2):  # 2 lines for 1 column (left and right edges)
            line_x = time_label_width if idx == 0 else time_label_width + day_column_width
            vert_line_name = f"lineVert{idx}"
            
            # Vertical lines extend through all time slots
            vert_line = self.add_line(
                vert_line_name,
                line_x, time_slot_start_y,
                1, total_grid_height,
                LineColor=0xDDDDDD,
                Orientation=1  # Vertical
            )
            self.slot_backgrounds[vert_line_name] = vert_line
            self._base_positions[vert_line_name] = (line_x, time_slot_start_y, 1, total_grid_height)
        
        # STEP 3: Position items in time slots (uses pre-calculated hour_positions)
        self._position_items_in_timeslots(time_label_width, day_column_width, 
                                         time_slot_start_y, start_hour)
        
        # Configure scrollbar based on actual content height
        total_content_height = total_grid_height  # Use actual calculated height with expanded rows
        _, _, _, container_height = self.parent._get_view_container_bounds()
        
        # Calculate visible height accounting for the frozen header area
        # header_boundary is where scrollable content starts
        header_boundary = 47  # Must match the value in on_scroll()
        visible_height = container_height - header_boundary
        
        # Add padding at the bottom (extra space below last hour)
        bottom_padding = 50  # Padding at the bottom
        
        if self.scrollbar:
            scrollbar_model = self.scrollbar.Model
            
            # Only enable scrollbar if content exceeds visible area
            if total_content_height > visible_height:
                # Calculate max scroll - simple pixel-based scrolling with dynamic row heights
                max_scroll = total_content_height + bottom_padding - visible_height
                scrollbar_model.ScrollValueMin = 0
                scrollbar_model.ScrollValueMax = max_scroll
                scrollbar_model.BlockIncrement = 50  # Scroll by ~50px per block
                scrollbar_model.LineIncrement = 20  # Scroll by 20px per line
                scrollbar_model.ScrollValue = 0
                scrollbar_model.VisibleSize = max(int(visible_height * 0.1), 10)
                
                self.scrollbar.setVisible(True)
                if hasattr(self, 'btn_scroll_up'):
                    self.btn_scroll_up.setVisible(True)
                if hasattr(self, 'btn_scroll_down'):
                    self.btn_scroll_down.setVisible(True)
                    
                self._update_scroll_button_states()
                
                if self.logger:
                    self.logger.info(f"Day scrollbar enabled: content {total_content_height}px, visible {visible_height}px")
                    self.logger.info(f"  Max scroll: {max_scroll}px")
            else:
                # Content fits, disable scrolling
                scrollbar_model.ScrollValueMin = 0
                scrollbar_model.ScrollValueMax = 0
                scrollbar_model.ScrollValue = 0
                self.scrollbar.setVisible(False)
                if hasattr(self, 'btn_scroll_up'):
                    self.btn_scroll_up.setVisible(False)
                if hasattr(self, 'btn_scroll_down'):
                    self.btn_scroll_down.setVisible(False)
        
        self.scroll_offset = 0
    
    def _analyze_hour_overlaps(self, start_hour, end_hour):
        """
        Analyze how many events overlap in each hour slot.
        Returns dict: {hour: max_overlaps_count}
        """
        hour_overlaps = {}
        date_str = self.current_date.strftime("%Y-%m-%d")
        
        if date_str not in self.calendar_data:
            return hour_overlaps
        
        items = self.calendar_data[date_str]
        
        for hour in range(start_hour, end_hour + 1):
            overlaps_in_this_slot = 0
            
            # Count items that fall in this hour
            for item in items:
                start_time = item.get('start_time')
                
                # Handle missing or invalid time - default to start_hour
                if not start_time:
                    item_hour = start_hour
                elif isinstance(start_time, datetime):
                    item_hour = start_time.hour
                else:
                    # If it's a date object without time, default to start_hour
                    item_hour = start_hour
                
                # Skip items outside our time range
                if item_hour < start_hour or item_hour > end_hour:
                    continue
                
                # Item belongs to this hour slot
                if item_hour == hour:
                    overlaps_in_this_slot += 1
            
            hour_overlaps[hour] = overlaps_in_this_slot
        
        return hour_overlaps
    
    def _position_items_in_timeslots(self, time_label_width, day_column_width, 
                                    time_slot_start_y, start_hour):
        """Position items in their respective time slots with fixed height and row-based layout"""
        if not self.calendar_data:
            return
        
        end_hour = self.day_config['end_hour']
        item_height = 20  # Fixed height for each event (same as week/month view)
        item_spacing = 2  # Spacing between stacked events
        
        # hour_positions is already calculated in _create_day_grid
        
        date_str = self.current_date.strftime("%Y-%m-%d")
        
        if date_str not in self.calendar_data:
            return
        
        items = self.calendar_data[date_str]
        slot_x = time_label_width
        
        # Group items by hour for this day
        items_by_hour = {}
        for item in items:
            start_time = item.get('start_time')
            
            # Handle missing or invalid time - default to start_hour
            if not start_time:
                hour = start_hour
            elif isinstance(start_time, datetime):
                hour = start_time.hour
            else:
                # If it's a date object without time, default to start_hour
                hour = start_hour
            
            # Skip items outside our time range
            if hour < start_hour or hour > end_hour:
                continue
            
            if hour not in items_by_hour:
                items_by_hour[hour] = []
            items_by_hour[hour].append(item)
        
        # Create buttons for each item, stacking them vertically within their hour
        for hour, items_in_hour in items_by_hour.items():
            hour_y, hour_height = self.hour_positions[hour]
            
            # Stack items vertically within this hour slot
            for item_idx, item in enumerate(items_in_hour):
                # Calculate Y position for this item (stacked)
                item_y = hour_y + 2 + (item_idx * (item_height + item_spacing))
                
                # Get item color
                item_color = self.day_config['colors']['item_default']
                if 'color' in item:
                    item_color = item['color']
                elif self.parent.get_item_color_callback:
                    try:
                        item_color = self.parent.get_item_color_callback(item)
                    except:
                        pass
                
                # Create item button
                item_id = item.get('id', f"item_{hour}_{item_idx}")
                btn_name = f"btnItem_{date_str}_{item_id}"
                
                # Truncate title for display if needed
                title = item.get('title', 'Untitled')
                # Day view has more width, allow longer titles
                max_length = 50
                display_title = title[:max_length-2] + ".." if len(title) > max_length else title
                
                try:
                    btn = self.add_button(
                        btn_name,
                        slot_x + 2, int(item_y), day_column_width - 4, item_height,
                        Label=display_title,
                        callback=lambda e, itm=item: self.on_item_clicked(e, itm),
                        BackgroundColor=item_color,
                        TextColor=0xFFFFFF,
                        FontWeight=150,
                        FontHeight=9,
                        Border=0
                    )
                    
                    if date_str not in self.item_buttons:
                        self.item_buttons[date_str] = []
                    self.item_buttons[date_str].append(btn)
                    
                    # Store button by name for fast scrolling access
                    self.item_button_controls[btn_name] = btn
                    
                    # Cache position for scrolling
                    self._base_positions[btn_name] = (slot_x + 2, int(item_y), day_column_width - 4, item_height)
                    
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error creating item button: {e}")
    
    def on_item_clicked(self, event, item):
        """Handle item button clicks"""
        if self.parent.on_item_click_callback:
            try:
                item_id = item.get('id')
                self.parent.on_item_click_callback(item_id, item)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error in item click callback: {e}")
                    self.logger.error(traceback.format_exc())
    
    def on_scroll(self, ev):
        """Handle scrollbar scroll events"""
        scroll_value = int(ev.Value)
        
        # Clamp scroll value to valid range to prevent scrolling beyond limits
        min_value = self.scrollbar.Model.ScrollValueMin
        max_value = self.scrollbar.Model.ScrollValueMax
        scroll_value = max(min_value, min(scroll_value, max_value))
        
        if scroll_value == self.scroll_offset:
            return
        
        old_offset = self.scroll_offset
        self.scroll_offset = scroll_value
        
        # Calculate the header boundary (controls should not appear above this)
        header_boundary = 47  # grid_start_y (5) + header heights (40) + spacing (2)
        
        # Get container height to check bottom boundary
        _, _, _, container_height = self.parent._get_view_container_bounds()
        
        # Update positions of all scrollable controls
        # NOTE: Headers are NOT in _base_positions, so they stay frozen at the top
        for control_name, (base_x, base_y, width, height) in self._base_positions.items():
            new_y = base_y - scroll_value
            
            # Control is visible if it's in the viewable area
            # Top of control must be at or below header, and control must be above bottom of container
            is_visible = (new_y >= header_boundary) and (new_y < container_height)
            
            # Update time labels
            if control_name in self.time_labels:
                self.time_labels[control_name].setPosSize(base_x, new_y, width, height, POSSIZE)
                self.time_labels[control_name].setVisible(is_visible)
            
            # Update grid lines (horizontal and vertical)
            elif control_name in self.slot_backgrounds:
                self.slot_backgrounds[control_name].setPosSize(base_x, new_y, width, height, POSSIZE)
                self.slot_backgrounds[control_name].setVisible(is_visible)
            
            # Update item buttons using the control name dictionary
            elif control_name in self.item_button_controls:
                self.item_button_controls[control_name].setPosSize(base_x, new_y, width, height, POSSIZE)
                self.item_button_controls[control_name].setVisible(is_visible)
        
        # Update scroll button states
        self._update_scroll_button_states()
    
    def scroll_up(self, event):
        """Handle up scroll button click"""
        try:
            if not self.scrollbar:
                return
            
            # Check if scrollbar is visible using the control's isVisible method
            try:
                if not self.scrollbar.isVisible():
                    return
            except:
                pass
            
            current_value = self.scrollbar.Model.ScrollValue
            min_value = self.scrollbar.Model.ScrollValueMin
            
            # Don't scroll if already at min
            if current_value <= min_value:
                return
            
            new_value = max(min_value, current_value - self.day_config['hour_height'])
            
            if new_value != current_value:
                self.scrollbar.Model.ScrollValue = new_value
                
                class MockScrollEvent:
                    def __init__(self, value):
                        self.Value = value
                
                self.on_scroll(MockScrollEvent(new_value))
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in scroll_up: {e}")
                self.logger.error(traceback.format_exc())
    
    def scroll_down(self, event):
        """Handle down scroll button click"""
        try:
            if not self.scrollbar:
                return
            
            # Check if scrollbar is visible using the control's isVisible method
            try:
                if not self.scrollbar.isVisible():
                    return
            except:
                pass
            
            current_value = self.scrollbar.Model.ScrollValue
            max_value = self.scrollbar.Model.ScrollValueMax
            
            # Don't scroll if already at max
            if current_value >= max_value:
                return
            
            new_value = min(max_value, current_value + self.day_config['hour_height'])
            
            if new_value != current_value:
                self.scrollbar.Model.ScrollValue = new_value
                
                class MockScrollEvent:
                    def __init__(self, value):
                        self.Value = value
                
                self.on_scroll(MockScrollEvent(new_value))
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in scroll_down: {e}")
                self.logger.error(traceback.format_exc())
    
    def _update_scroll_button_states(self):
        """Update scroll button enabled/disabled states"""
        try:
            if not self.scrollbar:
                return
            
            current_value = self.scrollbar.Model.ScrollValue
            min_value = self.scrollbar.Model.ScrollValueMin
            max_value = self.scrollbar.Model.ScrollValueMax
            
            # Update up button state
            if hasattr(self, 'btn_scroll_up') and self.btn_scroll_up:
                up_enabled = current_value > min_value
                self.btn_scroll_up.Model.Enabled = up_enabled
                if up_enabled:
                    self.btn_scroll_up.Model.BackgroundColor = 0xE0E0E0
                    self.btn_scroll_up.Model.TextColor = 0x333333
                else:
                    self.btn_scroll_up.Model.BackgroundColor = 0xF0F0F0
                    self.btn_scroll_up.Model.TextColor = 0x999999
            
            # Update down button state
            if hasattr(self, 'btn_scroll_down') and self.btn_scroll_down:
                down_enabled = current_value < max_value
                self.btn_scroll_down.Model.Enabled = down_enabled
                if down_enabled:
                    self.btn_scroll_down.Model.BackgroundColor = 0xE0E0E0
                    self.btn_scroll_down.Model.TextColor = 0x333333
                else:
                    self.btn_scroll_down.Model.BackgroundColor = 0xF0F0F0
                    self.btn_scroll_down.Model.TextColor = 0x999999
                    
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error updating scroll button states: {e}")
    
    def navigate_to_today(self):
        """Navigate to current day"""
        if self.logger:
            self.logger.info("Navigate to today")
        self.current_date = datetime.now()
        self.reload_data()
    
    def navigate_prev(self):
        """Navigate to previous day"""
        if self.logger:
            self.logger.info("Navigate to previous day")
        self.current_date = self.current_date - timedelta(days=1)
        self.reload_data()
    
    def navigate_next(self):
        """Navigate to next day"""
        if self.logger:
            self.logger.info("Navigate to next day")
        self.current_date = self.current_date + timedelta(days=1)
        self.reload_data()
    
    def reload_data(self):
        """Reload day data and recreate the grid"""
        # Reload day data
        self.load_day_data()
        
        # Recreate the day grid
        self._create_day_grid()
    
    def load_day_data(self):
        """Load calendar items for the current day"""
        try:
            if not self.parent.get_items_callback:
                self.calendar_data = {}
                return
            
            # Get items for just this day
            day_start = self.current_date.replace(hour=0, minute=0, second=0)
            day_end = self.current_date.replace(hour=23, minute=59, second=59)
            
            # Call the callback to get items
            self.calendar_data = self.parent.get_items_callback(day_start, day_end, self.parent.selected_filter)
            
            if self.logger:
                self.logger.info(f"Loading day data for {self.current_date.strftime('%Y-%m-%d')}")
                if self.calendar_data:
                    self.logger.info(f"Found {len(self.calendar_data)} days with items")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error loading day data: {e}")
                self.logger.error(traceback.format_exc())
            self.calendar_data = {}
    
    def resize(self, width, height):
        """Handle container resize events - recalculate and recreate day grid"""
        try:
            if self.logger:
                self.logger.info(f"Resizing DayCalendar to {width}x{height}")
            
            # Update container size
            self.container.setPosSize(0, 0, width, height, POSSIZE)
            
            # Recreate scrollbar with new dimensions
            if self.scrollbar:
                _, _, container_width, container_height = self.parent._get_view_container_bounds()
                
                button_size = 20
                button_spacing = 2
                scrollbar_width = 20
                scrollbar_x = container_width - scrollbar_width
                scrollbar_y = button_size + button_spacing
                scrollbar_height = container_height - (2 * button_size) - (2 * button_spacing)
                
                self.scrollbar.setPosSize(scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height, POSSIZE)
                
                if hasattr(self, 'btn_scroll_up') and self.btn_scroll_up:
                    self.btn_scroll_up.setPosSize(scrollbar_x, 0, button_size, button_size, POSSIZE)
                
                if hasattr(self, 'btn_scroll_down') and self.btn_scroll_down:
                    self.btn_scroll_down.setPosSize(scrollbar_x, scrollbar_y + scrollbar_height + button_spacing, 
                                                   button_size, button_size, POSSIZE)
            
            # Recreate the day grid with new dimensions
            self._create_day_grid()
            
            if self.logger:
                self.logger.info("DayCalendar resize complete")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during DayCalendar resize: {e}")
                self.logger.error(traceback.format_exc())
    
    def _create_print_document(self):
        """Create and return a new Writer document (hidden)"""
        try:
            import uno
            from com.sun.star.beans import PropertyValue
            
            desktop = self.parent.smgr.createInstanceWithContext("com.sun.star.frame.Desktop", self.parent.ctx)
            
            # Create property to hide the document
            hidden_prop = PropertyValue()
            hidden_prop.Name = "Hidden"
            hidden_prop.Value = True
            
            # Load document hidden
            doc = desktop.loadComponentFromURL("private:factory/swriter", "_blank", 0, (hidden_prop,))
            return doc
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error creating print document: {e}")
                self.logger.error(traceback.format_exc())
            return None
    
    def print_calendar(self, event=None):
        """
        Generate a Writer document representing the day calendar and open print dialog.
        This method can be called directly or used as a button callback.
        """
        try:
            if self.logger:
                self.logger.info("Printing day calendar...")
            
            # Create new Writer document
            doc = self._create_print_document()
            if not doc:
                return
            
            # Get text and cursor
            text = doc.Text
            cursor = text.createTextCursor()
            
            # Add calendar title
            cursor.CharHeight = 18
            cursor.CharWeight = 150  # Bold
            cursor.ParaAdjust = 1  # CENTER
            
            # Format title with day name and full date
            day_name = self.current_date.strftime("%A")  # Full day name
            date_str = self.current_date.strftime("%B %d, %Y")
            title_text = f"{day_name}, {date_str}"
            text.insertString(cursor, title_text, 0)
            cursor.gotoEnd(False)
            
            # Add filter information if applicable
            if self.parent.selected_filter:
                cursor.gotoEnd(False)
                text.insertString(cursor, "\n", 0)
                cursor.gotoEnd(False)
                cursor.CharHeight = 11
                cursor.CharWeight = 100  # Normal
                cursor.ParaAdjust = 1  # CENTER
                filter_text = f"Showing: {self.parent.selected_filter}"
                text.insertString(cursor, filter_text, 0)
                cursor.gotoEnd(False)
            
            # Add spacing before table
            text.insertString(cursor, "\n\n", 0)
            cursor.gotoEnd(False)
            
            # Reset formatting for table
            cursor.CharHeight = 10
            cursor.CharWeight = 100
            cursor.ParaAdjust = 0  # LEFT
            
            # Get configuration
            start_hour = self.day_config['start_hour']
            end_hour = self.day_config['end_hour']
            num_hours = end_hour - start_hour + 1
            
            # Create table (2 columns: time + events, hours + 1 header row)
            table = doc.createInstance("com.sun.star.text.TextTable")
            table.initialize(num_hours + 1, 2)  # +1 for header row, 2 columns
            text.insertTextContent(cursor, table, 0)
            
            # Create border line structure
            import uno
            border_line = uno.createUnoStruct("com.sun.star.table.BorderLine2")
            border_line.LineWidth = 20
            border_line.Color = 0xDDDDDD
            
            # Add header row
            headers = ['Time', 'Events']
            for col_idx, header in enumerate(headers):
                cell = table.getCellByPosition(col_idx, 0)
                cell_cursor = cell.createTextCursor()
                cell_cursor.CharWeight = 150  # Bold
                cell_cursor.ParaAdjust = 1  # CENTER
                cell_cursor.CharHeight = 11
                cell.setString(header)
                cell.BackColor = 0xE0E0E0
                
                # Add borders
                cell.TopBorder = border_line
                cell.BottomBorder = border_line
                cell.LeftBorder = border_line
                cell.RightBorder = border_line
            
            # Get items for this day
            date_key = self.current_date.strftime('%Y-%m-%d')
            items = self.calendar_data.get(date_key, [])
            
            # Group items by hour
            items_by_hour = {}
            for item in items:
                start_time = item.get('start_time')
                if start_time and isinstance(start_time, datetime):
                    hour = start_time.hour
                    if start_hour <= hour <= end_hour:
                        if hour not in items_by_hour:
                            items_by_hour[hour] = []
                        items_by_hour[hour].append(item)
            
            # Fill in time slots and items
            for hour_idx in range(num_hours):
                hour = start_hour + hour_idx
                row_num = hour_idx + 1
                
                # Time column
                time_cell = table.getCellByPosition(0, row_num)
                time_cursor = time_cell.createTextCursor()
                time_cursor.CharWeight = 150
                time_cursor.ParaAdjust = 1  # CENTER
                time_cell.setString(f"{hour:02d}:00")
                time_cell.BackColor = 0xF8F8F8
                
                # Add borders
                time_cell.TopBorder = border_line
                time_cell.BottomBorder = border_line
                time_cell.LeftBorder = border_line
                time_cell.RightBorder = border_line
                
                # Events column
                events_cell = table.getCellByPosition(1, row_num)
                
                # Get items for this hour
                hour_items = items_by_hour.get(hour, [])
                
                # Add items to cell
                if hour_items:
                    cell_text_obj = events_cell.getText()
                    cell_cursor = events_cell.createTextCursor()
                    
                    for idx, item in enumerate(hour_items):
                        if idx > 0:
                            # Add spacing between items
                            cell_text_obj.insertString(cell_cursor, "\n", 0)
                            cell_cursor.gotoEnd(False)
                        
                        # Get item color
                        item_color = 0x3498DB  # Default blue
                        if 'color' in item:
                            item_color = item['color']
                        elif self.parent.get_item_color_callback:
                            try:
                                item_color = self.parent.get_item_color_callback(item)
                            except:
                                pass
                        
                        # Set formatting for this item
                        cell_cursor.CharWeight = 100  # Normal
                        cell_cursor.CharHeight = 9
                        cell_cursor.CharColor = 0xFFFFFF  # White text
                        cell_cursor.CharBackColor = item_color
                        
                        # Add item text with time and title
                        item_title = item.get('title', 'Untitled')
                        start_time = item.get('start_time')
                        time_str = start_time.strftime('%H:%M') if start_time else ''
                        cell_text_obj.insertString(cell_cursor, f" {time_str} {item_title} ", 0)
                        cell_cursor.gotoEnd(False)
                        
                        # Reset background color
                        cell_cursor.CharBackColor = -1  # Transparent
                else:
                    # Empty cell
                    events_cell.setString("")
                
                # Add borders to events cell
                events_cell.TopBorder = border_line
                events_cell.BottomBorder = border_line
                events_cell.LeftBorder = border_line
                events_cell.RightBorder = border_line
                
                # Set cell vertical alignment to top
                events_cell.VertOrient = 0  # TOP
            
            # Set table to use full page width
            try:
                table.setPropertyValue("RelativeWidth", 100)
            except:
                pass
            
            # Set column widths (time column narrower than events column)
            try:
                columns = table.getColumns()
                if columns is not None:
                    # Time column gets 1 unit, events column gets 4 units
                    time_col = columns.getByIndex(0)
                    if time_col is not None:
                        time_col.setPropertyValue("RelativeWidth", 1)
                    
                    events_col = columns.getByIndex(1)
                    if events_col is not None:
                        events_col.setPropertyValue("RelativeWidth", 4)
            except Exception as col_err:
                if self.logger:
                    self.logger.debug(f"Could not set column widths: {col_err}")
            
            if self.logger:
                self.logger.info("Day calendar document created successfully")
            
            # Open print dialog directly without showing document
            frame = doc.getCurrentController().getFrame()
            dispatcher = self.parent.smgr.createInstanceWithContext("com.sun.star.frame.DispatchHelper", self.parent.ctx)
            
            # Execute print command
            dispatcher.executeDispatch(frame, ".uno:Print", "", 0, ())
            
            if self.logger:
                self.logger.info("Print dialog opened")
            
            # Note: Document will be disposed when print dialog is closed/cancelled
            # LibreOffice handles cleanup of hidden documents automatically
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error printing day calendar: {e}")
                self.logger.error(traceback.format_exc())
            
            # Try to show error message to user
            try:
                from librepy.pybrex.msgbox import msgbox
                msgbox(f"Error printing day calendar:\n{str(e)}", "Print Error")
            except:
                pass
    
    def dispose(self):
        """Clean up internal data structures and container"""
        try:
            if self.logger:
                self.logger.info("Disposing of DayCalendar")
            
            # Clear internal data structures
            self.calendar_data.clear()
            self.item_buttons.clear()
            self.item_button_controls.clear()
            self.time_labels.clear()
            self.slot_backgrounds.clear()
            self._base_positions.clear()
            
            # Call parent dispose to clean up container
            super().dispose()
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during disposal: {e}")
                self.logger.error(traceback.format_exc())

