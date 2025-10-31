from librepy.pybrex import ctr_container
from com.sun.star.awt.PosSize import POSSIZE
from librepy.pybrex.frame import create_document
from librepy.pybrex.listeners import Listeners
from com.sun.star.awt.ScrollBarOrientation import VERTICAL as SB_VERT
import traceback
import calendar
from datetime import datetime, timedelta
#Import DAOs here
from librepy.app.data.dao.training_session_dao import TrainingSessionDAO

# Calendar configuration constants
DEFAULT_WEEK_ROW_HEIGHT = 130  # Fixed height per week row (will become dynamic)

class Calendar(ctr_container.Container):
    component_name = 'calendar'

    def __init__(self, parent, ctx, smgr, frame, ps):
        self.parent = parent          
        self.ctx = ctx            
        self.smgr = smgr         
        self.frame = frame        
        self.ps = ps             
        self.listeners = Listeners()
        self.logger = parent.logger
        self.logger.info("Calendar Page initialized")

        # Add toolbar offset
        self.toolbar_offset = 0
        
        # Calendar state
        self.current_date = datetime.now()

        # Calendar data storage
        self.calendar_data = {}  # Will store jobs grouped by date

        # Enhanced calendar configuration for calendar-only rendering (no jobs/events)
        self.calendar_config = {
            'cell_width': 140,           # Will be calculated dynamically based on available width
            'day_label_height': 20,      # Space for day number
            'min_cell_height': 20,       # Minimum height (day label + padding)
            'padding_x': int(ps[2] * 0.02),
            'padding_y': int(ps[3] * 0.02),
            'top_offset': self.toolbar_offset,
            'entry_height': 24,          # Desired height per requirement
            'entry_spacing': 4,          # Vertical spacing between entries
            'entry_margin_x': 4,         # Horizontal margin inside day cell
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
        
        
        # Use available area passed from ComponentManager (accounts for sidebar width)
        container_ps = ps
        
        super().__init__(
            ctx, 
            smgr, 
            frame.window,
            container_ps,
            background_color=0xF2F2F2
        )
        
        # Store initial container size from available area
        self.window_width = ps[2]
        self.window_height = ps[3]
        self.main_container = None
        
        # Calculate initial cell width based on available space
        self._calculate_cell_width()
        
        # Calendar grid storage
        self.day_headers = {}    # Store day header labels (Sun, Mon, etc.)
        self.day_labels = {}     # Store day label controls
        self.session_labels = {} # Store training session label controls
        
        # Scrollbar-related properties
        self.scroll_offset = 0
        self.scrollbar = None
        self._base_positions = {}  # Store original positions: name → (x, y, w, h, week_num)
        
        # Row-based scrolling properties
        self.row_heights = []
        self.grid_start_y = 0
        self.visible_rows = 0
        self.current_scroll_row = 0
        
        # Fine-grained row tracking
        self.calendar_rows = []
        self.visible_calendar_rows = 0
        self.scroll_multiplier = 100  # For smooth scrolling
        
        self._create()
        self.show()

    def _calculate_cell_width(self):
        """Calculate optimal cell width based on available window width"""
        # Calculate available width for calendar grid
        grid_start_x = 40  # Left margin
        grid_end_margin = 50  # Right margin
        available_width = self.window_width - grid_start_x - grid_end_margin
        
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
        
        self.logger.info(f"Calculated cell width: {cell_width}px (available: {available_width}px)")

    def _create(self):
        # Title
        self.lbl_title = self.add_label(
            "lblTitle", 
            40, 20, 200, 40, 
            Label="Calendar", 
            FontHeight=21, 
            FontWeight=150, 
            FontName='Sans-serif'
        )
        
        nav_y = 95
        nav_height = 30
        nav_button_width = 40
        nav_start_x = 40
        
        # Previous month button
        self.btn_prev = self.add_button(
            "btnPrev",
            nav_start_x, nav_y, nav_button_width, nav_height,
            Label="<",
            callback=self.prev_month,
            BackgroundColor=0x2C3E50,
            TextColor=0xFFFFFF,
            FontWeight=150,
            FontHeight=14,
            Border=6
        )
        
        # Next month button
        self.btn_next = self.add_button(
            "btnNext",
            nav_start_x + nav_button_width + 5, nav_y, nav_button_width, nav_height,
            Label=">",
            callback=self.next_month,
            BackgroundColor=0x2C3E50,
            TextColor=0xFFFFFF,
            FontWeight=150,
            FontHeight=14,
            Border=6
        )
        
        # Month/Year display - positioned between nav buttons and right buttons
        month_year_text = self.current_date.strftime("%B %Y")
        month_label_start_x = nav_start_x + (nav_button_width * 2) + 20
        self.lbl_month_year = self.add_label(
            "lblMonthYear",
            month_label_start_x, nav_y, 180, nav_height,
            Label=month_year_text,
            FontHeight=16,
            FontWeight=150,
            FontName='Sans-serif'
        )
        
        # Create vertical scrollbar (hidden initially)
        scrollbar_width = 20
        self.scrollbar = self.add_scrollbar(
            "scrCalendar",
            self.window_width - scrollbar_width - 20,  # Right edge with margin
            200,  # Start below navigation controls
            scrollbar_width,
            self.window_height - 220,  # Height = remaining window space
            Orientation=SB_VERT,
            Visible=False  # Hidden until needed
        )
        
        # Add scroll buttons at top and bottom of scrollbar
        button_size = 18
        scrollbar_x = self.window_width - scrollbar_width - 20
        scrollbar_y = 200
        scrollbar_height = self.window_height - 220
        
        # Up scroll button (positioned just above scrollbar)
        self.btn_scroll_up = self.add_button(
            "btnScrollUp",
            scrollbar_x + 1,  # Center horizontally with scrollbar
            scrollbar_y - button_size - 2,  # Just above scrollbar
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
        
        # Down scroll button (positioned just below scrollbar)
        self.btn_scroll_down = self.add_button(
            "btnScrollDown",
            scrollbar_x + 1,  # Center horizontally with scrollbar
            scrollbar_y + scrollbar_height + 2,  # Just below scrollbar
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
        self.listeners.add_adjustment_listener(self.scrollbar, self.on_scroll)
        
        # Add keyboard/mouse wheel support to the main container
        try:
            self.listeners.add_key_listener(
                self.container,
                pressed=self.on_key_pressed
            )
            self.logger.info("Keyboard/mouse wheel support added to calendar container")
        except Exception as e:
            self.logger.debug(f"Keyboard/mouse wheel support not available: {e}")
        
        # Create calendar grid
        self._create_calendar_grid()

    def _create_calendar_grid(self):
        # Calendar grid starting position
        grid_start_x = 40
        grid_start_y = 200
        
        # Calendar dimensions
        cell_width = self.calendar_config['cell_width']
        day_label_height = self.calendar_config['day_label_height']
        
        # Clear existing day headers
        for header_name, header in self.day_headers.items():
            try:
                header.dispose()
            except:
                pass
        self.day_headers.clear()
        
        # Day headers - store them for resizing
        days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        for i, day in enumerate(days):
            header_name = f"lblDayHeader{i}"
            day_header = self.add_label(
                header_name,
                grid_start_x + (i * cell_width), grid_start_y - 32,
                cell_width, 28,
                Label=day,
                FontHeight=12,
                FontWeight=150,
                BackgroundColor=0xE0E0E0,  # Slightly darker for better contrast
                TextColor=0x333333,       # Darker text for better readability
                Border=2
            )
            self.day_headers[header_name] = day_header
        
        # Clear existing day labels
        for lbl_name, lbl in self.day_labels.items():
            try:
                lbl.dispose()
            except:
                pass
        self.day_labels.clear()
        self._clear_entries()

        # Generate calendar data
        cal = calendar.Calendar(6)  # Start week on Sunday
        month_days = list(cal.itermonthdates(self.current_date.year, self.current_date.month))
        
        # Clear position cache
        self._base_positions.clear()
        
        # Track all horizontal rows in the calendar for fine-grained scrolling
        self.calendar_rows = []  # Each item: {'y': y_position, 'height': row_height, 'week_num': week, 'row_type': 'day_label'|'job_row', 'job_row_index': index}
        
        # Dynamic row heights - track actual height needed for each week
        row_heights = [DEFAULT_WEEK_ROW_HEIGHT] * 6  # Start with default, will be updated
        
        # Store row heights for reference
        self.row_heights = row_heights
        self.grid_start_y = grid_start_y
        
        # Create calendar day labels and job buttons
        for week_num in range(6):  # 6 weeks maximum
            # Calculate current row top based on actual heights of previous weeks
            current_week_top = grid_start_y + sum(row_heights[:week_num])
            week_max_height = self.calendar_config['min_cell_height']  # Start with minimum
            
            for day_num in range(7):  # 7 days per week
                day_index = week_num * 7 + day_num
                if day_index < len(month_days):
                    date = month_days[day_index]

            day_label_y = current_week_top
            self.calendar_rows.append({
                'y': day_label_y,
                'height': day_label_height,
                'week_num': week_num,
                'row_type': 'day_label',
                'job_row_index': -1
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

                    self._render_entries_for_day(date, x, day_label_y, cell_width, row_index)
            
            row_heights[week_num] = max(day_label_height, DEFAULT_WEEK_ROW_HEIGHT)
        
        # Store final row data
        self.row_heights = row_heights
        
        # Add extra empty rows at the end for better scrolling space
        if len(self.calendar_rows) > 0:
            last_row = self.calendar_rows[-1]
            for i in range(3):
                extra_row_y = last_row['y'] + last_row['height'] + (i * day_label_height)
                self.calendar_rows.append({
                    'y': extra_row_y,
                    'height': day_label_height,
                    'week_num': 6 + i,  # Beyond normal weeks
                    'row_type': 'empty_row',
                    'job_row_index': -1
                })
        
        bottom_whitespace = self.calendar_config['day_label_height']
        visible_height = self.window_height - grid_start_y - 20 - bottom_whitespace
        
        # Calculate how many calendar rows can fit in visible area
        self.visible_calendar_rows = 0
        accumulated_height = 0
        for row_data in self.calendar_rows:
            # Use a more generous threshold to allow more content to be considered "visible"
            if accumulated_height + (row_data['height'] * 0.5) <= visible_height:  # 50% visible threshold
                accumulated_height += row_data['height']
                self.visible_calendar_rows += 1
            else:
                break
        
        # Ensure we can see at least some rows
        if self.visible_calendar_rows == 0 and len(self.calendar_rows) > 0:
            self.visible_calendar_rows = 1
        
        # Calculate maximum scroll based on whether content actually exceeds visible area
        # Only allow scrolling if there are more rows than can fit in the visible space
        if len(self.calendar_rows) <= self.visible_calendar_rows:
            # All content fits in visible area - no scrolling needed
            max_scroll_rows = 0
        else:
            # Content exceeds visible area - allow scrolling to show all rows
            max_scroll_rows = len(self.calendar_rows) - self.visible_calendar_rows
            # Add small buffer to ensure last rows are fully visible
            max_scroll_rows += 2
        
        # Configure scrollbar for row-by-row scrolling
        if self.scrollbar:
            scrollbar_model = self.scrollbar.Model
            
            # Use a larger range for smoother scrolling
            # Each row gets 100 units, making scrolling much more responsive
            scroll_multiplier = 100
            max_scroll_value = max_scroll_rows * scroll_multiplier
            
            scrollbar_model.ScrollValueMin = 0
            scrollbar_model.ScrollValueMax = max_scroll_value
            scrollbar_model.BlockIncrement = scroll_multiplier  # Page scroll = 1 row worth
            scrollbar_model.LineIncrement = 20  # Increase for more responsive scrolling
            scrollbar_model.ScrollValue = 0     # Reset to top
            
            # Set visible amount (thumb size) - make it smaller for better scroll range
            if max_scroll_value > 0:
                # Use a much smaller visible size to allow full range scrolling
                # The thumb size should be minimal to maximize scroll range
                # In LibreOffice, max draggable position = ScrollValueMax - VisibleSize
                # So we need VisibleSize to be very small to reach the full range
                visible_amount = max_scroll_value // 20  # Much smaller: 1/20th of total range
                # Set minimum thumb size to be very small
                scrollbar_model.VisibleSize = max(visible_amount, 10)  # Minimum thumb size very small
            else:
                scrollbar_model.VisibleSize = 10
            
            # Store the multiplier for use in scroll event
            self.scroll_multiplier = scroll_multiplier
            
            # Show scrollbar only if scrolling is needed
            scrolling_needed = max_scroll_rows > 0
            self.scrollbar.setVisible(scrolling_needed)
            
            # Show/hide scroll buttons based on scrollbar visibility
            if hasattr(self, 'btn_scroll_up') and self.btn_scroll_up:
                self.btn_scroll_up.setVisible(scrolling_needed)
            if hasattr(self, 'btn_scroll_down') and self.btn_scroll_down:
                self.btn_scroll_down.setVisible(scrolling_needed)
                
            # Update button states if scrolling is enabled
            if scrolling_needed:
                self._update_scroll_button_states()
        else:
            self.scroll_multiplier = 100
            
        # Reset scroll offset
        self.scroll_offset = 0
        self.current_scroll_row = 0
            
        self.logger.info(f"Created {len(self.calendar_rows)} calendar rows")
        self.logger.info(f"Visible calendar rows: {self.visible_calendar_rows}, Max scroll rows: {max_scroll_rows}")
        self.logger.info(f"Scrollbar range: 0 to {max_scroll_value if 'max_scroll_value' in locals() else 0}")
        self.logger.info(f"Cached {len(self._base_positions)} control positions")

    def prev_month(self, event):
        """Navigate to previous month"""
        self.logger.info("Previous month clicked")
        if self.current_date.month == 1:
            # Go to December of previous year, always use day 1 to avoid day-out-of-range errors
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12, day=1)
        else:
            # Go to previous month, always use day 1 to avoid day-out-of-range errors
            self.current_date = self.current_date.replace(month=self.current_date.month - 1, day=1)
        self._update_calendar()

    def next_month(self, event):
        """Navigate to next month"""
        self.logger.info("Next month clicked")
        if self.current_date.month == 12:
            # Go to January of next year, always use day 1 to avoid day-out-of-range errors
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1, day=1)
        else:
            # Go to next month, always use day 1 to avoid day-out-of-range errors
            self.current_date = self.current_date.replace(month=self.current_date.month + 1, day=1)
        self._update_calendar()

    def _update_calendar(self):
        """Update the calendar display"""
        # Update month/year label
        month_year_text = self.current_date.strftime("%B %Y")
        self.lbl_month_year.Model.Label = month_year_text
        
        # Reload calendar data for new month
        self.load_calendar_data()
        
        # Recreate the calendar grid with new data
        self._create_calendar_grid()

    def load_calendar_data(self):
        """Load calendar training sessions from database and group by date string."""
        try:
            # Build visible date range for the current month
            cal = calendar.Calendar(6)
            dates_iter = list(cal.itermonthdates(self.current_date.year, self.current_date.month))
            if not dates_iter:
                self.calendar_data = {}
                return
            start_day = dates_iter[0]
            end_day = dates_iter[-1]

            # Fetch sessions within range
            dao = TrainingSessionDAO(self.logger)
            sessions = dao.get_sessions_between(start_day, end_day)

            # Normalize and group by YYYY-MM-DD
            grouped = {}
            for s in sessions or []:
                dt = s.get('date')
                if hasattr(dt, 'strftime'):
                    date_key = dt.strftime('%Y-%m-%d')
                elif isinstance(dt, str):
                    date_key = dt
                else:
                    # Fallback: skip invalid
                    continue
                # Ensure normalized date string saved back
                s_norm = {
                    'id': s.get('id'),
                    'date': date_key,
                    'title': s.get('title'),
                    'status': s.get('status')
                }
                grouped.setdefault(date_key, []).append(s_norm)

            self.calendar_data = grouped
        except Exception as e:
            self.logger.error(f"Error loading calendar data: {e}")
            self.logger.error(traceback.format_exc())
            self.calendar_data = {}

    def _clear_entries(self):
        """Dispose and clear all rendered training session entry controls."""
        try:
            for name, ctrl in list(self.session_labels.items()):
                try:
                    ctrl.dispose()
                except Exception:
                    pass
                # Remove cached position for this entry if present
                if name in self._base_positions:
                    try:
                        del self._base_positions[name]
                    except Exception:
                        pass
        finally:
            self.session_labels.clear()

    def _render_single_entry(self, pill_name, title, x, y, w, h, row_index):
        """Create a single entry control and register/cache it."""
        pill = self.add_label(
            pill_name,
            x, y, w, h,
            Label=str(title or ''),
            FontHeight=10,
            FontWeight=150,
            TextColor=0x222222,
            BackgroundColor=0x72ab8a,
            Border=0
        )
        self.session_labels[pill_name] = pill
        self._base_positions[pill_name] = (x, y, w, h, row_index)
        return pill

    def _render_entries_for_day(self, date, x, base_y, cell_width, row_index):
        """Render all entries for a given date below the day label."""
        cfg = self.calendar_config
        day_label_height = cfg['day_label_height']
        entry_height = cfg.get('entry_height', 24)
        entry_spacing = cfg.get('entry_spacing', 4)
        entry_margin_x = cfg.get('entry_margin_x', 4)
        date_key = f"{date.year:04d}-{date.month:02d}-{date.day:02d}"
        sessions_for_day = self.calendar_data.get(date_key, [])
        for idx, session in enumerate(sessions_for_day):
            pill_name = f"pill_{date.day}{date.month}{date.year}_{session['id']}"
            pill_x = x + entry_margin_x
            pill_y = base_y + day_label_height + entry_spacing + idx * (entry_height + entry_spacing)
            pill_w = cell_width - 2 * entry_margin_x
            pill_h = entry_height
            self._render_single_entry(pill_name, session.get('title'), pill_x, pill_y, pill_w, pill_h, row_index)

    def _move_entries_in_view(self, visible_row_start, visible_row_end, offset_y):
        """Relocate/show/hide entries for scrolling based on cached positions."""
        controls_moved = 0
        controls_hidden = 0
        for ctrl_name, ctrl in self.session_labels.items():
            if ctrl_name in self._base_positions:
                x, y, w, h, row_index = self._base_positions[ctrl_name]
                if visible_row_start <= row_index < visible_row_end:
                    ctrl.setPosSize(x, y + offset_y, w, h, POSSIZE)
                    ctrl.setVisible(True)
                    controls_moved += 1
                else:
                    ctrl.setVisible(False)
                    controls_hidden += 1
        return controls_moved, controls_hidden

    def show(self):
        # Load calendar data first
        self.load_calendar_data()
        super().show()
        self.resize(self.window_width, self.window_height)

    def hide(self):
        super().hide()

    def resize(self, width, height):
        """Handle window resize events"""
        try:
            # Update stored dimensions
            self.window_width = width
            self.window_height = height - self.toolbar_offset
            
            # Recalculate cell width based on new window size
            self._calculate_cell_width()
            
            # Update configuration (keep enhanced layout settings)
            self.calendar_config.update({
                'padding_x': int(width * 0.02),
                'padding_y': int((height - self.toolbar_offset) * 0.02),
            })
        
            sidebar_width = getattr(self.parent, 'sidebar_width', 0)
            
            # Resize the main container (preserve sidebar offset for X position)
            self.container.setPosSize(
                sidebar_width,  # Start after sidebar, not at 0
                self.toolbar_offset,
                width, 
                height - self.toolbar_offset,
                POSSIZE
            )
            
            # Calculate positions for all components
            pos = self._calculate_positions()
            
            # Update top row buttons with horizontal layout
            # (Create Event and Print Calendar buttons removed)
            
            # Update calendar grid (recreate with new dimensions)
            self._create_calendar_grid()
            
            # Update scrollbar position and size
            if hasattr(self, 'scrollbar') and self.scrollbar:
                scrollbar_width = 20
                scrollbar_x = width - scrollbar_width - 20
                scrollbar_y = 200
                scrollbar_height = height - self.toolbar_offset - 220
                
                self.scrollbar.setPosSize(
                    scrollbar_x,  # Right edge with margin
                    scrollbar_y,  # Start below navigation controls
                    scrollbar_width,
                    scrollbar_height,  # Adjust for toolbar offset
                    POSSIZE
                )
                
                # Update scroll button positions
                button_size = 18
                if hasattr(self, 'btn_scroll_up') and self.btn_scroll_up:
                    self.btn_scroll_up.setPosSize(
                        scrollbar_x + 1,  # Center horizontally with scrollbar
                        scrollbar_y - button_size - 2,  # Just above scrollbar
                        button_size,
                        button_size,
                        POSSIZE
                    )
                    
                if hasattr(self, 'btn_scroll_down') and self.btn_scroll_down:
                    self.btn_scroll_down.setPosSize(
                        scrollbar_x + 1,  # Center horizontally with scrollbar
                        scrollbar_y + scrollbar_height + 2,  # Just below scrollbar
                        button_size,
                        button_size,
                        POSSIZE
                    )
                
            # Force redraw
            if hasattr(self, 'container') and self.container.getPeer():
                peer = self.container.getPeer()
                peer.invalidate(0)
                
        except Exception as e:
            self.logger.error(f"Error during resize: {e}")
            self.logger.error(traceback.format_exc())

    def dispose(self):
        """Dispose of all controls and calendar components"""
        try:
            self.logger.info("Disposing of Calendar page")
            
            # Dispose day headers
            for header_name, header in self.day_headers.items():
                try:
                    header.dispose()
                except:
                    pass
            self.day_headers.clear()
            
            # Dispose day labels
            for lbl_name, lbl in self.day_labels.items():
                try:
                    lbl.dispose()
                except:
                    pass
            self.day_labels.clear()
            self._clear_entries()
            
            # Dispose scroll buttons
            if hasattr(self, 'btn_scroll_up') and self.btn_scroll_up is not None:
                try:
                    self.btn_scroll_up.dispose()
                except Exception as scroll_up_error:
                    self.logger.error(f"Error disposing scroll up button: {str(scroll_up_error)}")
                finally:
                    self.btn_scroll_up = None
                    
            if hasattr(self, 'btn_scroll_down') and self.btn_scroll_down is not None:
                try:
                    self.btn_scroll_down.dispose()
                except Exception as scroll_down_error:
                    self.logger.error(f"Error disposing scroll down button: {str(scroll_down_error)}")
                finally:
                    self.btn_scroll_down = None
            
            # Dispose scrollbar
            if hasattr(self, 'scrollbar') and self.scrollbar is not None:
                try:
                    self.scrollbar.dispose()
                except Exception as scrollbar_error:
                    self.logger.error(f"Error disposing scrollbar: {str(scrollbar_error)}")
                finally:
                    self.scrollbar = None
            
            # Dispose of main container
            if hasattr(self, 'container') and self.container is not None:
                try:
                    # Make sure the container window is hidden
                    try:
                        self.container.getPeer().setVisible(False)
                    except:
                        pass
                    
                    # Then dispose the container
                    self.container.dispose()
                except Exception as container_error:
                    self.logger.error(f"Error disposing container: {str(container_error)}")
                finally:
                    self.container = None
            
        except Exception as e:
            self.logger.error(f"Error during disposal: {e}")
            self.logger.error(traceback.format_exc())

    def _calculate_positions(self):
        """Calculate positions for UI components based on current window size"""
        # Top row buttons - arranged horizontally
        top_button_width = 140
        top_button_height = 30
        top_button_y = 20
        button_spacing = 10
        right_margin = 50
        
        # Calculate positions for horizontal layout (right to left)
        logout_x = self.window_width - (top_button_width + right_margin)
        create_job_x = logout_x - (top_button_width + button_spacing)
        
        return {
            'logout_x': logout_x,
            'create_job_x': create_job_x,
            'top_button_y': top_button_y,
            'top_button_width': top_button_width,
            'top_button_height': top_button_height,
        }


    def on_scroll(self, ev):
        """Handle scrollbar scroll events - smooth row-by-row scrolling"""
        scroll_value = int(ev.Value)  # Raw scrollbar value (0 to max_scroll_rows * 100)
        
        # Convert scroll value to row index (with smooth interpolation)
        scroll_row = scroll_value // self.scroll_multiplier
        scroll_progress = (scroll_value % self.scroll_multiplier) / self.scroll_multiplier
        
        # Clamp to valid range
        scroll_row = max(0, min(scroll_row, len(self.calendar_rows) - 1))
        
        # For very responsive scrolling, start showing next row as soon as user moves scrollbar
        if scroll_progress > 0.1:  # 10% threshold for immediate response
            scroll_row = min(scroll_row + 1, len(self.calendar_rows) - 1)
        
        if scroll_row == self.current_scroll_row:
            return  # No change needed
            
        old_scroll_row = self.current_scroll_row
        self.current_scroll_row = scroll_row
        
        # Calculate offset for smooth positioning
        offset_y = 0
        if scroll_row > 0 and scroll_row < len(self.calendar_rows):
            target_row_y = self.calendar_rows[scroll_row]['y']
            offset_y = self.grid_start_y - target_row_y
            
            # Add smooth sub-row positioning if we're between rows
            if scroll_progress > 0.1 and scroll_row > 0:
                # Interpolate between current and next row position
                current_row_y = self.calendar_rows[scroll_row - 1]['y'] if scroll_row > 0 else self.grid_start_y
                next_row_y = self.calendar_rows[scroll_row]['y'] if scroll_row < len(self.calendar_rows) else current_row_y
                
                # Smooth interpolation
                interpolated_y = current_row_y + (next_row_y - current_row_y) * scroll_progress
                offset_y = self.grid_start_y - interpolated_y
        
        self.logger.debug(f"Scroll value: {scroll_value}, row: {scroll_row}, progress: {scroll_progress:.2f}, offset: {offset_y}")
        
        # Calculate which rows should be visible
        visible_row_start = scroll_row
        # Allow for more rows beyond calculated visible range to show more content at bottom
        visible_row_end = min(scroll_row + self.visible_calendar_rows + 3, len(self.calendar_rows))  # Increased buffer from 1 to 3
        
        # Update visibility and position for all controls
        controls_moved = 0
        controls_hidden = 0
        
        # Move day labels
        for label_name in self.day_labels.keys():
            if label_name in self._base_positions:
                x, y, w, h, row_index = self._base_positions[label_name]
                
                if visible_row_start <= row_index < visible_row_end:
                    # Row is visible
                    self.day_labels[label_name].setPosSize(x, y + offset_y, w, h, POSSIZE)
                    self.day_labels[label_name].setVisible(True)
                    controls_moved += 1
                else:
                    # Row is hidden
                    self.day_labels[label_name].setVisible(False)
                    controls_hidden += 1

        moved, hidden = self._move_entries_in_view(visible_row_start, visible_row_end, offset_y)
        controls_moved += moved
        controls_hidden += hidden
        
        self.logger.debug(f"Moved {controls_moved} controls, hidden {controls_hidden} controls")
        
        # Update scroll button states based on new scroll position
        self._update_scroll_button_states()
        
        # Force redraw for smoother visual updates
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
                self.logger.debug("Up arrow pressed")
            elif ev.KeyCode == 1026:  # Down arrow  
                new_value = min(max_value, current_value + self.scroll_multiplier)
                self.logger.debug("Down arrow pressed")
            elif ev.KeyCode == 1031:  # Page Up
                new_value = max(0, current_value - (self.scroll_multiplier * 3))
                self.logger.debug("Page Up pressed")
            elif ev.KeyCode == 1032:  # Page Down
                new_value = min(max_value, current_value + (self.scroll_multiplier * 3))
                self.logger.debug("Page Down pressed")
            elif ev.KeyCode == 1029:  # Home
                new_value = 0
                self.logger.debug("Home pressed")
            elif ev.KeyCode == 1030:  # End
                new_value = max_value
                self.logger.debug("End pressed")
            else:
                # Log unknown key codes for debugging
                self.logger.debug(f"Key pressed: {ev.KeyCode}")
                return
                
            # Update scrollbar if value changed
            if new_value != current_value:
                self.scrollbar.Model.ScrollValue = new_value
                self.logger.debug(f"Keyboard scroll: {current_value} -> {new_value}")
                
        except Exception as e:
            self.logger.error(f"Error in key handler: {e}")

    def scroll_up(self, event):
        """Handle up scroll button click - scroll up by one row"""
        try:
            if not hasattr(self, 'scrollbar') or not self.scrollbar:
                return
            
            # Check if scrollbar is visible using Model.Visible
            try:
                if not self.scrollbar.Model.Visible:
                    return
            except:
                # If Model.Visible doesn't work, just proceed
                pass
                
            current_value = self.scrollbar.Model.ScrollValue
            min_value = self.scrollbar.Model.ScrollValueMin
            new_value = max(min_value, current_value - self.scroll_multiplier)
            
            if new_value != current_value:
                self.scrollbar.Model.ScrollValue = new_value
                self.logger.debug(f"Up button scroll: {current_value} -> {new_value}")
                
                # Manually trigger scroll event to update calendar display
                class MockScrollEvent:
                    def __init__(self, value):
                        self.Value = value
                
                self.on_scroll(MockScrollEvent(new_value))
                
        except Exception as e:
            self.logger.error(f"Error in scroll_up: {e}")

    def scroll_down(self, event):
        """Handle down scroll button click - scroll down by one row"""
        try:
            if not hasattr(self, 'scrollbar') or not self.scrollbar:
                return
            
            # Check if scrollbar is visible using Model.Visible
            try:
                if not self.scrollbar.Model.Visible:
                    return
            except:
                # If Model.Visible doesn't work, just proceed
                pass
                
            current_value = self.scrollbar.Model.ScrollValue
            max_value = self.scrollbar.Model.ScrollValueMax
            new_value = min(max_value, current_value + self.scroll_multiplier)
            
            if new_value != current_value:
                self.scrollbar.Model.ScrollValue = new_value
                self.logger.debug(f"Down button scroll: {current_value} -> {new_value}")
                
                # Manually trigger scroll event to update calendar display
                class MockScrollEvent:
                    def __init__(self, value):
                        self.Value = value
                
                self.on_scroll(MockScrollEvent(new_value))
                
        except Exception as e:
            self.logger.error(f"Error in scroll_down: {e}")

    def _update_scroll_button_states(self):
        """Update scroll button enabled/disabled states based on scrollbar position"""
        try:
            if not hasattr(self, 'scrollbar') or not self.scrollbar:
                return
                
            current_value = self.scrollbar.Model.ScrollValue
            min_value = self.scrollbar.Model.ScrollValueMin
            max_value = self.scrollbar.Model.ScrollValueMax
            
            # Update up button state
            if hasattr(self, 'btn_scroll_up') and self.btn_scroll_up:
                # Disable if at minimum, enable otherwise
                up_enabled = current_value > min_value
                self.btn_scroll_up.Model.Enabled = up_enabled
                # Visual feedback - lighter color when disabled
                if up_enabled:
                    self.btn_scroll_up.Model.BackgroundColor = 0xE0E0E0
                    self.btn_scroll_up.Model.TextColor = 0x333333
                else:
                    self.btn_scroll_up.Model.BackgroundColor = 0xF0F0F0
                    self.btn_scroll_up.Model.TextColor = 0x999999
            
            # Update down button state
            if hasattr(self, 'btn_scroll_down') and self.btn_scroll_down:
                # Disable if at maximum, enable otherwise
                down_enabled = current_value < max_value
                self.btn_scroll_down.Model.Enabled = down_enabled
                # Visual feedback - lighter color when disabled
                if down_enabled:
                    self.btn_scroll_down.Model.BackgroundColor = 0xE0E0E0
                    self.btn_scroll_down.Model.TextColor = 0x333333
                else:
                    self.btn_scroll_down.Model.BackgroundColor = 0xF0F0F0
                    self.btn_scroll_down.Model.TextColor = 0x999999
                    
        except Exception as e:
            self.logger.error(f"Error updating scroll button states: {e}")
