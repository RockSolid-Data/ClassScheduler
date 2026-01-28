#coding:utf-8
# Author:  Josiah Aguilar
# Purpose: Generic month calendar view that accepts callback functions for data and interactions
# Created: 2025-11-12

from com.sun.star.awt.PosSize import POSSIZE
from librepy.pybrex.ctr_container import Container
from com.sun.star.awt.ScrollBarOrientation import VERTICAL as SB_VERT
import traceback
import calendar
from datetime import datetime, timedelta

# Calendar configuration constants
DEFAULT_WEEK_ROW_HEIGHT = 130  # Fixed height per week row (will become dynamic)

class MonthCalendar(Container):
    """
    Reusable month calendar component that displays items on a calendar grid.
    
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
                'color': 0x3498DB,  # Optional, uses get_item_color_callback if not provided
                'type': 'custom_type'  # Optional metadata
            },
            ...
        ]
    }
    """
    
    def __init__(self, ctx, smgr, window, parent, start_date=None):
        """
        Initialize MonthCalendar view.
        
        Args:
            ctx: Component context
            smgr: Service manager
            window: Parent window for the container
            parent: Calendar instance that manages callbacks and data
            start_date: Optional initial date to display
        """
        self.parent = parent
        self.logger = parent.logger if hasattr(parent, 'logger') else None
        
        if self.logger:
            self.logger.info("MonthCalendar __init__ started")
        
        # Calendar state
        self.current_date = start_date if start_date else datetime.now()
        
        # Get container bounds from parent (we only need width and height)
        x, y, width, height = parent._get_view_container_bounds()
        
        if self.logger:
            self.logger.info(f"View area size: {width}x{height}")
            self.logger.info(f"Parent window visible: {window.isVisible()}")
        
        # Initialize Container at (0, 0) relative to the child window
        # The child window itself is already positioned correctly
        super().__init__(
            ctx=ctx,
            smgr=smgr,
            window=window,
            ps=(0, 0, width, height),
            background_color=0xFFFFFF
        )
        
        if self.logger:
            self.logger.info(f"Container created, visible: {self.container.isVisible()}")
            self.logger.info(f"Container position: {self.container.getPosSize().X}, {self.container.getPosSize().Y}")
            self.logger.info(f"Container size: {self.container.getPosSize().Width}x{self.container.getPosSize().Height}")
        
        # Calendar data storage
        self.calendar_data = {}  # Will store items grouped by date
        self.item_buttons = {}   # Will store item button controls by date
        
        # Enhanced calendar configuration for label + item button layout
        self.calendar_config = {
            'cell_width': 140,           # Will be calculated dynamically based on available width
            'day_label_height': 20,      # Small space for day number
            'item_button_height': 24,    # Height for item buttons
            'item_button_spacing': 3,    # Spacing between item buttons
            'min_cell_height': 20,       # Minimum height (day label + padding)
            'max_items_display': None,   # NO LIMIT - show all items
            'item_font_size': 9,         # Font size for item buttons
            'colors': {
                'border': 0x000000,
                'day_label_bg': 0xF8F8F8,
                'day_label_border': 0xDDDDDD,
                'calendar_bg': 0xFFFFFF,
                'calendar_border': 0xDDDDDD,
                'current_month': 0x000000,
                'other_month': 0x999999,
            }
        }
        
        # Calculate initial cell width based on available space
        self._calculate_cell_width()
        
        # Calendar grid storage
        self.day_headers = {}    # Store day header labels (Sun, Mon, etc.)
        self.day_labels = {}     # Store day label controls
        self.calendar_buttons = {}  # Store all item buttons
        
        # Scrollbar-related properties
        self.scroll_offset = 0
        self.scrollbar = None
        self._base_positions = {}  # Store original positions: name → (x, y, w, h, row_index)
        
        # Row-based scrolling properties
        self.row_heights = []
        self.grid_start_y = 0
        self.visible_rows = 0
        self.current_scroll_row = 0
        
        # Fine-grained row tracking
        self.calendar_rows = []
        self.visible_calendar_rows = 0
        self.scroll_multiplier = 100  # For smooth scrolling
        
        # Create scrollbar and scroll buttons
        self._create_scrollbar()
        
        # Load data and create grid
        self.load_calendar_data()
        self._create_calendar_grid()
        
        # Show the container
        if self.logger:
            self.logger.info(f"About to show container, currently visible: {self.container.isVisible()}")
        
        self.show()
        
        if self.logger:
            self.logger.info(f"After show() call, container visible: {self.container.isVisible()}")
            self.logger.info(f"Parent window still visible: {window.isVisible()}")
            self.logger.info(f"MonthCalendar initialization complete")
    
    def _calculate_cell_width(self):
        """Calculate optimal cell width based on available container width"""
        # Get container width
        _, _, container_width, _ = self.parent._get_view_container_bounds()
        
        # Calculate available width for calendar grid
        scrollbar_space = 25  # Space for scrollbar on the right
        available_width = container_width - scrollbar_space
        
        # Calculate cell width for 7 columns (days of week)
        calculated_width = available_width // 7
        
        # Set minimum cell width (no maximum to use full available space)
        min_cell_width = 120
        
        # Apply constraints
        if calculated_width < min_cell_width:
            cell_width = min_cell_width
        else:
            cell_width = calculated_width
        
        # Update the configuration
        self.calendar_config['cell_width'] = cell_width
        
        if self.logger:
            self.logger.info(f"Calculated cell width: {cell_width}px (available: {available_width}px)")
    
    def _create_scrollbar(self):
        """Create scrollbar and scroll buttons for month calendar"""
        # Get container size
        _, _, container_width, container_height = self.parent._get_view_container_bounds()
        
        # Button configuration
        button_size = 20
        button_spacing = 2
        
        # Calculate scrollbar dimensions with space for buttons
        scrollbar_width = 20
        scrollbar_x = container_width - scrollbar_width  # Right edge
        scrollbar_y = button_size + button_spacing  # Start below up button
        scrollbar_height = container_height - (2 * button_size) - (2 * button_spacing)  # Leave space for buttons
        
        # Create vertical scrollbar (hidden initially)
        self.scrollbar = self.add_scrollbar(
            "scrCalendar",
            scrollbar_x,
            scrollbar_y,
            scrollbar_width,
            scrollbar_height,
            Orientation=SB_VERT,
            Visible=False  # Hidden until needed
        )
        
        # Up scroll button (positioned at top of scrollbar area, INSIDE container)
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
            Visible=False  # Hidden until scrolling is needed
        )
        
        # Down scroll button (positioned at bottom of scrollbar area, INSIDE container)
        self.btn_scroll_down = self.add_button(
            "btnScrollDown",
            scrollbar_x,
            scrollbar_y + scrollbar_height + button_spacing,  # Below scrollbar
            button_size,
            button_size,
            Label="▼",
            callback=self.scroll_down,
            BackgroundColor=0xE0E0E0,
            TextColor=0x333333,
            FontHeight=10,
            FontWeight=150,
            Border=2,
            Visible=False  # Hidden until scrolling is needed
        )
        
        # Add scroll listener
        self.add_adjustment_listener(self.scrollbar, self.on_scroll)
        
        # Add keyboard/mouse wheel support to the container
        try:
            self.add_key_listener(
                self.container,
                pressed=self.on_key_pressed
            )
            if self.logger:
                self.logger.info("Keyboard/mouse wheel support added to calendar container")
        except Exception as e:
            if self.logger:
                self.logger.debug(f"Keyboard/mouse wheel support not available: {e}")
    
    def _create_calendar_grid(self):
        """Create the calendar grid with day headers and item buttons"""
        # Calendar grid starting position (relative to container at 0,0)
        grid_start_x = 0
        grid_start_y = 0
        
        # Enhanced calendar dimensions for item buttons
        cell_width = self.calendar_config['cell_width']
        day_label_height = self.calendar_config['day_label_height']
        item_button_height = self.calendar_config['item_button_height']
        item_button_spacing = self.calendar_config['item_button_spacing']
        
        # Clear existing day headers
        for header_name, header in self.day_headers.items():
            try:
                header.dispose()
            except:
                pass
        self.day_headers.clear()
        
        # Day headers - store them for resizing
        days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        header_y = 5  # Small top margin
        for i, day in enumerate(days):
            header_name = f"lblDayHeader{i}"
            day_header = self.add_label(
                header_name,
                i * cell_width, header_y,
                cell_width, 28,
                Label=day,
                FontHeight=12,
                FontWeight=150,
                BackgroundColor=0xE0E0E0,
                TextColor=0x333333,
                Border=2
            )
            self.day_headers[header_name] = day_header
        
        # Update grid start to be below headers
        grid_start_y = header_y + 28 + 5
        
        # Clear existing day labels and item buttons
        for lbl_name, lbl in self.day_labels.items():
            try:
                lbl.dispose()
            except:
                pass
        self.day_labels.clear()
        
        for btn_name, btn in self.calendar_buttons.items():
            try:
                btn.dispose()
            except:
                pass
        self.calendar_buttons.clear()
        
        # Clear existing item buttons storage
        for date_str, buttons in self.item_buttons.items():
            for button in buttons:
                try:
                    button.dispose()
                except:
                    pass
        self.item_buttons.clear()
        
        # Generate calendar data
        cal = calendar.Calendar(6)  # Start week on Sunday
        month_days = list(cal.itermonthdates(self.current_date.year, self.current_date.month))
        
        # Clear position cache
        self._base_positions.clear()
        
        # Track all horizontal rows in the calendar for fine-grained scrolling
        self.calendar_rows = []
        
        # Dynamic row heights - track actual height needed for each week
        row_heights = [DEFAULT_WEEK_ROW_HEIGHT] * 6  # Start with default, will be updated
        
        # Store row heights for reference
        self.row_heights = row_heights
        self.grid_start_y = grid_start_y
        
        # Create calendar day labels and item buttons
        for week_num in range(6):  # 6 weeks maximum
            # Calculate current row top based on actual heights of previous weeks
            current_week_top = grid_start_y + sum(row_heights[:week_num])
            week_max_height = self.calendar_config['min_cell_height']  # Start with minimum
            
            # Track the maximum number of items in this week
            max_items_in_week = 0
            
            # First pass: create day labels and determine max items for this week
            week_items_data = {}  # day_num -> items_for_day
            for day_num in range(7):  # 7 days per week
                day_index = week_num * 7 + day_num
                if day_index < len(month_days):
                    date = month_days[day_index]
                    date_str = date.strftime('%Y-%m-%d')
                    items_for_day = self.calendar_data.get(date_str, [])
                    week_items_data[day_num] = items_for_day
                    
                    if len(items_for_day) > max_items_in_week:
                        max_items_in_week = len(items_for_day)
            
            # Create day number row for this week
            day_label_y = current_week_top
            self.calendar_rows.append({
                'y': day_label_y,
                'height': day_label_height,
                'week_num': week_num,
                'row_type': 'day_label',
                'item_row_index': -1
            })
            
            # Create day labels
            for day_num in range(7):
                day_index = week_num * 7 + day_num
                if day_index < len(month_days):
                    date = month_days[day_index]
                    x = grid_start_x + (day_num * cell_width)
                    
                    # Determine if this day is in the current month
                    is_current_month = date.month == self.current_date.month
                    text_color = 0x000000 if is_current_month else 0x999999
                    
                    # Create day label
                    day_label_name = f"dayLabel_{date.day}_{date.month}_{date.year}"
                    day_label = self.add_label(
                        day_label_name,
                        x, day_label_y, cell_width, day_label_height,
                        Label=str(date.day),
                        FontHeight=11,
                        FontWeight=150,
                        TextColor=text_color,
                        BackgroundColor=self.calendar_config['colors']['day_label_bg'],
                        Border=1
                    )
                    
                    self.day_labels[day_label_name] = day_label
                    
                    # Cache day label position with row index
                    row_index = len(self.calendar_rows) - 1
                    self._base_positions[day_label_name] = (x, day_label_y, cell_width, day_label_height, row_index)
            
            # Create item button rows for this week
            for item_row_index in range(max_items_in_week):
                item_row_y = day_label_y + day_label_height + 1 + (item_row_index * (item_button_height + item_button_spacing))
                
                # Add this item row to calendar rows
                self.calendar_rows.append({
                    'y': item_row_y,
                    'height': item_button_height,
                    'week_num': week_num,
                    'row_type': 'item_row',
                    'item_row_index': item_row_index
                })
                
                row_index = len(self.calendar_rows) - 1
                
                # Create items for this row across all days
                for day_num in range(7):
                    day_index = week_num * 7 + day_num
                    if day_index < len(month_days):
                        date = month_days[day_index]
                        x = grid_start_x + (day_num * cell_width)
                        
                        # Get items for this day
                        items_for_day = week_items_data.get(day_num, [])
                        
                        # Show item if it exists
                        if item_row_index < len(items_for_day):
                            item = items_for_day[item_row_index]
                            self._create_single_item_button(date, item, x, item_row_y, cell_width, item_button_height, item_row_index, row_index)
            
            # Calculate total height for this week
            week_total_height = day_label_height + 1 + (max_items_in_week * (item_button_height + item_button_spacing))
            if max_items_in_week > 0:
                week_total_height -= item_button_spacing  # Remove last spacing
            
            row_heights[week_num] = max(week_total_height, DEFAULT_WEEK_ROW_HEIGHT)
        
        # Store final row data
        self.row_heights = row_heights
        
        # Add extra empty rows at the end for better scrolling space
        if len(self.calendar_rows) > 0:
            last_row = self.calendar_rows[-1]
            
            # Add 3 extra empty rows for plenty of scrolling space
            for i in range(3):
                extra_row_y = last_row['y'] + last_row['height'] + item_button_spacing + (i * (item_button_height + item_button_spacing))
                
                self.calendar_rows.append({
                    'y': extra_row_y,
                    'height': item_button_height,
                    'week_num': 6 + i,
                    'row_type': 'empty_row',
                    'item_row_index': -1
                })
        
        # Calculate scrollbar settings for row-by-row scrolling
        item_button_height = self.calendar_config['item_button_height']
        item_button_spacing = self.calendar_config['item_button_spacing']
        bottom_whitespace = item_button_height + item_button_spacing
        
        # Get container height for visible area calculation
        _, _, _, container_height = self.parent._get_view_container_bounds()
        visible_height = container_height - bottom_whitespace
        
        # Calculate total content height (actual calendar rows)
        total_content_height = 0
        for row_data in self.calendar_rows:
            total_content_height += row_data['height']
        
        # Calculate minimum expected calendar height (6 weeks at default height)
        # This is the baseline space a calendar should have
        num_weeks = 6  # Maximum weeks in a month view
        minimum_calendar_height = num_weeks * DEFAULT_WEEK_ROW_HEIGHT
        
        # Use the larger of actual content height or minimum expected height
        # This ensures scrollbar appears if the calendar can't show all weeks at default size
        effective_content_height = max(total_content_height, minimum_calendar_height)
        
        # Calculate how many calendar rows can FULLY fit in visible area
        self.visible_calendar_rows = 0
        accumulated_height = 0
        for row_data in self.calendar_rows:
            if accumulated_height + row_data['height'] <= visible_height:
                accumulated_height += row_data['height']
                self.visible_calendar_rows += 1
            else:
                break
        
        # Ensure we can see at least some rows
        if self.visible_calendar_rows == 0 and len(self.calendar_rows) > 0:
            self.visible_calendar_rows = 1
        
        # Calculate maximum scroll based on whether content exceeds visible area
        # Show scrollbar if effective content height is greater than visible height
        # This ensures scrollbar appears when:
        # 1. Actual content doesn't fit
        # 2. Minimum calendar height (6 weeks) doesn't fit in visible area
        if effective_content_height <= visible_height:
            max_scroll_rows = 0
        else:
            max_scroll_rows = len(self.calendar_rows) - self.visible_calendar_rows
            max_scroll_rows += 2
        
        # Configure scrollbar for row-by-row scrolling
        if self.scrollbar:
            scrollbar_model = self.scrollbar.Model
            
            scroll_multiplier = 100
            max_scroll_value = max_scroll_rows * scroll_multiplier
            
            scrollbar_model.ScrollValueMin = 0
            scrollbar_model.ScrollValueMax = max_scroll_value
            scrollbar_model.BlockIncrement = scroll_multiplier
            scrollbar_model.LineIncrement = 20
            scrollbar_model.ScrollValue = 0
            
            if max_scroll_value > 0:
                visible_amount = max_scroll_value // 20
                scrollbar_model.VisibleSize = max(visible_amount, 10)
            else:
                scrollbar_model.VisibleSize = 10
            
            self.scroll_multiplier = scroll_multiplier
            
            scrolling_needed = max_scroll_rows > 0
            self.scrollbar.setVisible(scrolling_needed)
            
            if hasattr(self, 'btn_scroll_up') and self.btn_scroll_up:
                self.btn_scroll_up.setVisible(scrolling_needed)
            if hasattr(self, 'btn_scroll_down') and self.btn_scroll_down:
                self.btn_scroll_down.setVisible(scrolling_needed)
                
            if scrolling_needed:
                self._update_scroll_button_states()
            
            # Log scrollbar status
            if self.logger:
                self.logger.info(f"Created {len(self.calendar_rows)} calendar rows")
                self.logger.info(f"Total content height: {total_content_height}px")
                self.logger.info(f"Minimum calendar height: {minimum_calendar_height}px (6 weeks × {DEFAULT_WEEK_ROW_HEIGHT}px)")
                self.logger.info(f"Effective content height: {effective_content_height}px, Visible height: {visible_height}px")
                self.logger.info(f"Visible calendar rows: {self.visible_calendar_rows}, Max scroll rows: {max_scroll_rows}")
                self.logger.info(f"Scrollbar visible: {scrolling_needed}")
                self.logger.info(f"Cached {len(self._base_positions)} control positions")
        else:
            self.scroll_multiplier = 100
            
        # Reset scroll offset
        self.scroll_offset = 0
        self.current_scroll_row = 0
    
    def _create_single_item_button(self, date, item, x, y, cell_width, item_button_height, item_row_index, row_index):
        """Create a single item button for a specific row and position"""
        try:
            date_str = date.strftime('%Y-%m-%d')
            if date_str not in self.item_buttons:
                self.item_buttons[date_str] = []
            
            # Get item display text
            title = item.get('title', 'Untitled')
            
            # Text formatting
            max_total_length = 18
            
            if len(title) > max_total_length:
                button_text = title[:max_total_length-2] + ".."
            else:
                button_text = title
            
            # Get item color - first check item itself, then use callback
            if 'color' in item:
                item_color = item['color']
            elif self.parent.get_item_color_callback:
                item_color = self.parent.get_item_color_callback(item)
            else:
                item_color = 0x3498DB  # Default blue
            
            # Use lighter text if background is dark
            text_color = 0xFFFFFF if item_color in [0x2C3E50, 0xE74C3C, 0x9B59B6] else 0x000000
            
            item_button_name = f"itemBtn_{date_str}_{item_row_index}"
            
            # Get item ID for callback
            item_id = item.get('id')
            
            # Create individual item button
            item_button = self.add_button(
                item_button_name,
                x + 2, y, cell_width - 4, item_button_height,
                Label=button_text,
                callback=lambda event, iid=item_id, itm=item: self._on_item_button_clicked(iid, itm),
                BackgroundColor=item_color,
                TextColor=text_color,
                FontHeight=self.calendar_config['item_font_size'],
                FontWeight=150,
                Border=0
            )
            
            self.item_buttons[date_str].append(item_button)
            self.calendar_buttons[item_button_name] = item_button
            
            # Cache item button position with row index
            self._base_positions[item_button_name] = (x + 2, y, cell_width - 4, item_button_height, row_index)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error creating item button for {date}: {e}")
                self.logger.error(traceback.format_exc())
    
    def _on_item_button_clicked(self, item_id, item):
        """Handle item button click - calls the callback if provided"""
        if self.parent.on_item_click_callback:
            try:
                self.parent.on_item_click_callback(item_id, item)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error in item click callback: {e}")
                    self.logger.error(traceback.format_exc())
    
    def navigate_to_today(self):
        """Navigate to current month"""
        if self.logger:
            self.logger.info("Navigate to today")
        self.current_date = datetime.now().replace(day=1)
        self.reload_data()
    
    def navigate_prev(self):
        """Navigate to previous month"""
        if self.logger:
            self.logger.info("Navigate to previous month")
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12, day=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1, day=1)
        self.reload_data()
    
    def navigate_next(self):
        """Navigate to next month"""
        if self.logger:
            self.logger.info("Navigate to next month")
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1, day=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1, day=1)
        self.reload_data()
    
    def reload_data(self):
        """Reload calendar data and recreate the grid"""
        # Reload calendar data
        self.load_calendar_data()
        
        # Recreate the calendar grid with new data
        self._create_calendar_grid()
    
    
    def load_calendar_data(self):
        """Load calendar items from callback function"""
        try:
            if not self.parent.get_items_callback:
                self.calendar_data = {}
                return
            
            # Calculate date range for current month
            start_date = self.current_date.replace(day=1)
            
            # Get the last day of the month
            if self.current_date.month == 12:
                end_date = self.current_date.replace(year=self.current_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_date = self.current_date.replace(month=self.current_date.month + 1, day=1) - timedelta(days=1)
            
            # Extend range to include previous/next month days shown in calendar
            cal = calendar.Calendar(6)  # Start week on Sunday
            month_days = list(cal.itermonthdates(self.current_date.year, self.current_date.month))
            if month_days:
                start_date = month_days[0]
                end_date = month_days[-1]
            
            # Call the callback to get items
            self.calendar_data = self.parent.get_items_callback(start_date, end_date, self.parent.selected_filter)
            
            if self.logger:
                self.logger.info(f"Loading calendar data for {start_date} to {end_date}")
                self.logger.info(f"Found {len(self.calendar_data)} days with items")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error loading calendar data: {e}")
                self.logger.error(traceback.format_exc())
            self.calendar_data = {}
    
    
    def on_scroll(self, ev):
        """Handle scrollbar scroll events - smooth row-by-row scrolling"""
        scroll_value = int(ev.Value)
        
        # Convert scroll value to row index (with smooth interpolation)
        scroll_row = scroll_value // self.scroll_multiplier
        scroll_progress = (scroll_value % self.scroll_multiplier) / self.scroll_multiplier
        
        # Clamp to valid range
        scroll_row = max(0, min(scroll_row, len(self.calendar_rows) - 1))
        
        # For responsive scrolling, start showing next row
        if scroll_progress > 0.1:
            scroll_row = min(scroll_row + 1, len(self.calendar_rows) - 1)
        
        if scroll_row == self.current_scroll_row:
            return
            
        old_scroll_row = self.current_scroll_row
        self.current_scroll_row = scroll_row
        
        # Calculate offset for smooth positioning
        offset_y = 0
        if scroll_row > 0 and scroll_row < len(self.calendar_rows):
            target_row_y = self.calendar_rows[scroll_row]['y']
            offset_y = self.grid_start_y - target_row_y
            
            if scroll_progress > 0.1 and scroll_row > 0:
                current_row_y = self.calendar_rows[scroll_row - 1]['y'] if scroll_row > 0 else self.grid_start_y
                next_row_y = self.calendar_rows[scroll_row]['y'] if scroll_row < len(self.calendar_rows) else current_row_y
                
                interpolated_y = current_row_y + (next_row_y - current_row_y) * scroll_progress
                offset_y = self.grid_start_y - interpolated_y
        
        if self.logger:
            self.logger.debug(f"Scroll value: {scroll_value}, row: {scroll_row}, progress: {scroll_progress:.2f}, offset: {offset_y}")
        
        # Calculate which rows should be visible
        visible_row_start = scroll_row
        visible_row_end = min(scroll_row + self.visible_calendar_rows + 3, len(self.calendar_rows))
        
        # Update visibility and position for all controls
        controls_moved = 0
        controls_hidden = 0
        
        # Move day labels
        for label_name in self.day_labels.keys():
            if label_name in self._base_positions:
                x, y, w, h, row_index = self._base_positions[label_name]
                
                if visible_row_start <= row_index < visible_row_end:
                    self.day_labels[label_name].setPosSize(x, y + offset_y, w, h, POSSIZE)
                    self.day_labels[label_name].setVisible(True)
                    controls_moved += 1
                else:
                    self.day_labels[label_name].setVisible(False)
                    controls_hidden += 1
        
        # Move item buttons
        for button_name in self.calendar_buttons.keys():
            if button_name in self._base_positions:
                x, y, w, h, row_index = self._base_positions[button_name]
                
                if visible_row_start <= row_index < visible_row_end:
                    self.calendar_buttons[button_name].setPosSize(x, y + offset_y, w, h, POSSIZE)
                    self.calendar_buttons[button_name].setVisible(True)
                    controls_moved += 1
                else:
                    self.calendar_buttons[button_name].setVisible(False)
                    controls_hidden += 1
        
        if self.logger:
            self.logger.debug(f"Moved {controls_moved} controls, hidden {controls_hidden} controls")
        
        # Update scroll button states
        self._update_scroll_button_states()
        
        # Force redraw
        if hasattr(self, 'container') and self.container.getPeer():
            peer = self.container.getPeer()
            peer.invalidate(0)
    
    def on_key_pressed(self, ev):
        """Handle key presses for calendar scrolling"""
        try:
            if not hasattr(self, 'scrollbar') or not self.scrollbar:
                return
                
            current_value = self.scrollbar.Model.ScrollValue
            max_value = self.scrollbar.Model.ScrollValueMax
            new_value = current_value
            
            # Check key codes for scrolling
            if ev.KeyCode == 1025:  # Up arrow
                new_value = max(0, current_value - self.scroll_multiplier)
            elif ev.KeyCode == 1026:  # Down arrow
                new_value = min(max_value, current_value + self.scroll_multiplier)
            elif ev.KeyCode == 1031:  # Page Up
                new_value = max(0, current_value - (self.scroll_multiplier * 3))
            elif ev.KeyCode == 1032:  # Page Down
                new_value = min(max_value, current_value + (self.scroll_multiplier * 3))
            elif ev.KeyCode == 1029:  # Home
                new_value = 0
            elif ev.KeyCode == 1030:  # End
                new_value = max_value
            else:
                return
                
            # Update scrollbar if value changed
            if new_value != current_value:
                self.scrollbar.Model.ScrollValue = new_value
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in key handler: {e}")
    
    def scroll_up(self, event):
        """Handle up scroll button click"""
        try:
            if not hasattr(self, 'scrollbar') or not self.scrollbar:
                return
            
            try:
                if not self.scrollbar.Model.Visible:
                    return
            except:
                pass
                
            current_value = self.scrollbar.Model.ScrollValue
            min_value = self.scrollbar.Model.ScrollValueMin
            new_value = max(min_value, current_value - self.scroll_multiplier)
            
            if new_value != current_value:
                self.scrollbar.Model.ScrollValue = new_value
                
                class MockScrollEvent:
                    def __init__(self, value):
                        self.Value = value
                
                self.on_scroll(MockScrollEvent(new_value))
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in scroll_up: {e}")
    
    def scroll_down(self, event):
        """Handle down scroll button click"""
        try:
            if not hasattr(self, 'scrollbar') or not self.scrollbar:
                return
            
            try:
                if not self.scrollbar.Model.Visible:
                    return
            except:
                pass
                
            current_value = self.scrollbar.Model.ScrollValue
            max_value = self.scrollbar.Model.ScrollValueMax
            new_value = min(max_value, current_value + self.scroll_multiplier)
            
            if new_value != current_value:
                self.scrollbar.Model.ScrollValue = new_value
                
                class MockScrollEvent:
                    def __init__(self, value):
                        self.Value = value
                
                self.on_scroll(MockScrollEvent(new_value))
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in scroll_down: {e}")
    
    def _update_scroll_button_states(self):
        """Update scroll button enabled/disabled states"""
        try:
            if not hasattr(self, 'scrollbar') or not self.scrollbar:
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
    
    def resize(self, width, height):
        """Handle container resize events - recalculate and recreate calendar grid"""
        try:
            if self.logger:
                self.logger.info(f"Resizing MonthCalendar to {width}x{height}")
            
            # Update container size
            self.container.setPosSize(0, 0, width, height, POSSIZE)
            
            # Recalculate cell widths based on new dimensions
            self._calculate_cell_width()
            
            # Recreate scrollbar with new dimensions
            if self.scrollbar:
                # Get new scrollbar position
                _, _, container_width, container_height = self.parent._get_view_container_bounds()
                
                # Button configuration (must match _create_scrollbar)
                button_size = 20
                button_spacing = 2
                scrollbar_width = 20
                scrollbar_x = container_width - scrollbar_width
                scrollbar_y = button_size + button_spacing
                scrollbar_height = container_height - (2 * button_size) - (2 * button_spacing)
                
                # Update scrollbar size and position
                self.scrollbar.setPosSize(scrollbar_x, scrollbar_y, scrollbar_width, scrollbar_height, POSSIZE)
                
                # Update scroll button positions if they exist
                if hasattr(self, 'btn_scroll_up') and self.btn_scroll_up:
                    self.btn_scroll_up.setPosSize(scrollbar_x, 0, button_size, button_size, POSSIZE)
                
                if hasattr(self, 'btn_scroll_down') and self.btn_scroll_down:
                    self.btn_scroll_down.setPosSize(scrollbar_x, scrollbar_y + scrollbar_height + button_spacing, button_size, button_size, POSSIZE)
            
            # Recreate the calendar grid with new dimensions
            self._create_calendar_grid()
            
            if self.logger:
                self.logger.info("MonthCalendar resize complete")
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during MonthCalendar resize: {e}")
                self.logger.error(traceback.format_exc())
    
    def dispose(self):
        """Clean up internal data structures and container"""
        try:
            if self.logger:
                self.logger.info("Disposing of MonthCalendar")
            
            # Clear internal data structures
            self.day_headers.clear()
            self.day_labels.clear()
            self.item_buttons.clear()
            self.calendar_buttons.clear()
            self.calendar_rows.clear()
            self._base_positions.clear()
            self.calendar_data.clear()
            
            # Call parent dispose to clean up container
            super().dispose()
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during disposal: {e}")
                self.logger.error(traceback.format_exc())
    
    def _get_calendar_month_days(self):
        """Get list of dates for current calendar view"""
        cal = calendar.Calendar(6)  # Sunday start
        return list(cal.itermonthdates(self.current_date.year, self.current_date.month))
    
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
        Generate a Writer document representing the calendar and open print dialog.
        This method can be called directly or used as a button callback.
        """
        try:
            if self.logger:
                self.logger.info("Printing calendar...")
            
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
            title_text = self.current_date.strftime("%B %Y")
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
            
            # Get calendar days
            month_days = self._get_calendar_month_days()
            num_weeks = (len(month_days) + 6) // 7
            
            # Create table (7 columns x weeks+1 rows)
            table = doc.createInstance("com.sun.star.text.TextTable")
            table.initialize(num_weeks + 1, 7)  # +1 for header row
            text.insertTextContent(cursor, table, 0)
            
            # Create border line structure
            import uno
            border_line = uno.createUnoStruct("com.sun.star.table.BorderLine2")
            border_line.LineWidth = 20
            border_line.Color = 0xDDDDDD
            
            # Add day headers
            days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
            for i, day in enumerate(days):
                cell = table.getCellByPosition(i, 0)
                cell_cursor = cell.createTextCursor()
                cell_cursor.CharWeight = 150  # Bold
                cell_cursor.ParaAdjust = 1  # CENTER
                cell.setString(day)
                cell.BackColor = 0xE0E0E0
                
                # Add borders
                cell.TopBorder = border_line
                cell.BottomBorder = border_line
                cell.LeftBorder = border_line
                cell.RightBorder = border_line
            
            # Fill in calendar days
            for week_num in range(num_weeks):
                for day_num in range(7):
                    day_index = week_num * 7 + day_num
                    cell = table.getCellByPosition(day_num, week_num + 1)
                    
                    if day_index < len(month_days):
                        date = month_days[day_index]
                        cell_cursor = cell.createTextCursor()
                        
                        # Determine if this day is in the current month
                        is_current_month = date.month == self.current_date.month
                        
                        # Set day number with styling
                        cell_cursor.CharWeight = 150  # Bold
                        cell_cursor.CharHeight = 11
                        if not is_current_month:
                            cell_cursor.CharColor = 0x999999  # Gray for other months
                        else:
                            cell_cursor.CharColor = 0x000000  # Black for current month
                        
                        cell_text = str(date.day)
                        
                        # Get items for this date
                        date_str = date.strftime('%Y-%m-%d')
                        items = self.calendar_data.get(date_str, [])
                        
                        if items:
                            # Build the cell content with day number first
                            cell.setString(cell_text)
                            
                            # Get cell text object for adding colored items
                            cell_text_obj = cell.getText()
                            cell_cursor.gotoEnd(False)
                            
                            # Add each item with its color
                            for idx, item in enumerate(items):
                                # Add newline before item
                                cell_text_obj.insertString(cell_cursor, "\n", 0)
                                cell_cursor.gotoEnd(False)
                                
                                # Get item color
                                item_color = 0x3498DB  # Default blue
                                if self.parent.get_item_color_callback:
                                    try:
                                        item_color = self.parent.get_item_color_callback(item)
                                    except:
                                        pass
                                
                                # Set formatting for this item
                                cell_cursor.CharWeight = 100  # Normal
                                cell_cursor.CharHeight = 9
                                cell_cursor.CharColor = 0xFFFFFF  # White text
                                
                                # Set background color for the item
                                # Note: We'll use CharBackColor for text highlighting
                                cell_cursor.CharBackColor = item_color
                                
                                # Add item text with bullet
                                item_title = item.get('title', 'Untitled')
                                cell_text_obj.insertString(cell_cursor, f" • {item_title} ", 0)
                                cell_cursor.gotoEnd(False)
                                
                                # Reset background color
                                cell_cursor.CharBackColor = -1  # Transparent
                        else:
                            # Add day number with 3 empty placeholder rows
                            cell_text_with_placeholders = cell_text + "\n\n\n"
                            cell.setString(cell_text_with_placeholders)
                    else:
                        # Empty cell for positions without dates
                        cell.setString("")
                    
                    # Add borders to all cells
                    cell.TopBorder = border_line
                    cell.BottomBorder = border_line
                    cell.LeftBorder = border_line
                    cell.RightBorder = border_line
                    
                    # Set cell vertical alignment to top
                    cell.VertOrient = 0  # TOP
            
            # Set table to use full page width
            try:
                table.setPropertyValue("RelativeWidth", 100)
            except:
                pass
            
            # Set column widths to be equal
            try:
                columns = table.getColumns()
                if columns is not None:
                    for i in range(7):
                        col = columns.getByIndex(i)
                        if col is not None:
                            col.setPropertyValue("RelativeWidth", 1)
            except Exception as col_err:
                if self.logger:
                    self.logger.debug(f"Could not set column widths: {col_err}")
            
            if self.logger:
                self.logger.info("Calendar document created successfully")
            
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
                self.logger.error(f"Error printing calendar: {e}")
                self.logger.error(traceback.format_exc())
            
            # Try to show error message to user
            try:
                from librepy.pybrex.msgbox import msgbox
                msgbox(f"Error printing calendar:\n{str(e)}", "Print Error")
            except:
                pass

