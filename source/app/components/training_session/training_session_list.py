import traceback
import time as _time
from librepy.pybrex import ctr_container
from librepy.pybrex.values import pybrex_logger
from com.sun.star.awt.PosSize import POSSIZE
from librepy.pybrex.values import GRID_HEADER_BG_COLOR
from librepy.app.data.dao.training_session_dao import TrainingSessionDAO

class TrainingSessionList(ctr_container.Container):
    component_name = 'training_session_list'

    def __init__(self, parent, ctx, smgr, frame, ps):
        self.logger = getattr(parent, 'logger', pybrex_logger(__name__))
        self.parent = parent
        self.ctx = ctx
        self.smgr = smgr
        self.frame = frame
        self.ps = ps

        # UI state
        self._all_rows = []
        self._search_text = ''
        self._debounce_handle = None
        self._debounce_last = 0
        self._debounce_ms = 300

        # Toolbar offset (if parent adds one)
        self.toolbar_offset = 0

        # Container config
        self.container_config = {
            'padding_x': int(ps[2] * 0.02),
            'padding_y': int(ps[3] * 0.02),
            'top_offset': self.toolbar_offset,
        }

        # Get background color from theme
        bg_color = 0xF2F2F2  # Default
        if hasattr(parent, 'theme_config'):
            bg_color = parent.theme_config.get_main_bg_color_int()

        # Initialize base container
        super().__init__(ctx, smgr, frame.window, ps, background_color=bg_color)

        # Store current size
        self.window_width = ps[2]
        self.window_height = ps[3]

        self._create()
        self.logger.info("TrainingSessionList initialized")
        self.show()

    def _create(self):
        pos = self._calculate_positions()

        # Title
        self.lbl_title = self.add_label(
            'lbl_title',
            pos['title_x'], pos['title_y'], pos['title_w'], pos['title_h'],
            Label='Training Sessions', FontHeight=21, FontWeight=150
        )

        self.btn_new_entry = self.add_button(
            'btn_new_entry',
            pos['new_entry_x'], pos['top_button_y'], pos['top_button_width'], pos['top_button_height'],
            Label='New Entry',
            callback=self.on_new_entry,
            BackgroundColor=0x2C3E50,
            TextColor=0xFFFFFF,
            FontWeight=150,
            FontHeight=12,
            Border=6
        )

        # Add a "Print List" button with the same flow as calendars
        try:
            print_list_x = pos['new_entry_x'] - (pos['top_button_width'] + 10)
            self.btn_print_list = self.add_button(
                'btn_print_list',
                print_list_x, pos['top_button_y'], pos['top_button_width'], pos['top_button_height'],
                Label='Print List',
                callback=self.on_print_list,
                BackgroundColor=0x2C3E50,
                TextColor=0xFFFFFF,
                FontWeight=150,
                FontHeight=12,
                Border=6
            )
        except Exception:
            # Non-fatal: UI will still work without the extra button
            self.btn_print_list = None

        # Search controls
        self.lbl_search = self.add_label(
            'lbl_search', pos['search_label_x'], pos['search_y'], 60, 20, Label='Search:'
        )
        self.txt_search = self.add_edit(
            'txt_search', pos['search_x'], pos['search_y'], pos['search_w'], 20
        )
        self.add_text_listener(self.txt_search, self._on_search_text_changed)
        self.add_key_listener(self.txt_search, pressed=self._on_search_key_pressed)

        # Grid
        titles = [
            ("Class", "name", 200, 1),
            ("Teacher", "teacher_name", 200, 1),
            ("Date", "session_date", 140, 1),
            ("Time", "session_time", 120, 1),
            ("Price", "price", 100, 1),
        ]
        self.grid_base, self.grid = self.add_grid(
            'grid_sessions', pos['grid_x'], pos['grid_y'], pos['grid_w'], pos['grid_h'], titles,
            ShowRowHeader=False, HeaderBackgroundColor=GRID_HEADER_BG_COLOR
        )
        # Wire double-click via mouse listener (replicate TeachersTab)
        self.add_mouse_listener(self.grid, pressed=self.on_row_double_click)

    def load_data(self, search_query=None):
        try:
            dao = TrainingSessionDAO(self.logger)
            data = dao.get_training_sessions() or []

            # Client-side filter
            sq = (search_query if search_query is not None else self._search_text or '').strip().lower()
            if sq:
                def contains(s):
                    return sq in (str(s or '')).lower()
                filtered = []
                for r in data:
                    if contains(r.get('name')) or contains(r.get('teacher_name')) or contains(r.get('session_date')) or contains(r.get('session_time')):
                        filtered.append(r)
                data = filtered

            # Guarantee id/heading
            for r in data:
                if not r.get('id'):
                    # Build composite heading
                    r['id'] = f"{r.get('name','')}|{r.get('session_date','')}|{r.get('session_time','')}"
                p = r.get('price', None)
                if p is None or p == '':
                    r['price'] = ''
                else:
                    # Convert to float then format with 2 decimals
                    r['price'] = f"${float(p):.2f}"
            self._all_rows = data

            # Set to grid
            self.grid_base.set_data(data, heading='id')
        except Exception as e:
            self.logger.error(f"Failed loading sessions: {e}")
            self.logger.error(traceback.format_exc())

    def refresh_entries(self, event=None):
        self.load_data()

    def search_data(self, event=None):
        # Use current text field, trigger load
        try:
            self._search_text = self.txt_search.getText()
        except Exception:
            pass
        self.load_data()

    def _on_search_text_changed(self, ev=None):
        # Debounced handler
        now = _time.time()
        self._search_text = self.txt_search.getText()
        self._debounce_last = now

        def do_after_delay():
            try:
                # Only act if no newer input occurred within debounce window
                if (now == self._debounce_last) or ((_time.time() - now) * 1000 >= self._debounce_ms and self._debounce_last == now):
                    self.load_data()
            except Exception:
                pass
        # There is no built-in timer here; rely on user pressing Enter or Search.
        # Still call immediate filter for responsiveness
        self.load_data()

    def _on_search_key_pressed(self, ev):
        try:
            # Enter key
            if getattr(ev, 'KeyCode', None) == 1280:  # LibreOffice Enter key code (approx); handle broadly
                self.search_data()
        except Exception:
            pass

    def on_row_double_click(self, ev=None):
        try:
            if getattr(ev, 'Buttons', None) == 1 and getattr(ev, 'ClickCount', 0) == 2:
                heading = self.grid_base.active_row_heading()
                if heading is None:
                    return
                from librepy.app.components.training_session.training_session_entry_dlg import TrainingSessionEntryDlg
                dlg = TrainingSessionEntryDlg(self, self.ctx, self.smgr, self.frame, self.ps, Title="Edit Training Session", session_id=heading)
                ret = dlg.execute()
                if ret in (1, 2):
                    self.load_data()
        except Exception as e:
            self.logger.error(f"TrainingSessionList.on_row_double_click error: {e}")

    def on_new_entry(self, ev=None):
        try:
            from librepy.app.components.training_session.training_session_entry_dlg import TrainingSessionEntryDlg
            dlg = TrainingSessionEntryDlg(self, self.ctx, self.smgr, self.frame, self.ps, Title="New Training Session")
            ret = dlg.execute()
            if ret == 1:
                self.load_data()
                new_id = getattr(dlg, 'last_saved_id', None)
                if new_id:
                    dlg2 = TrainingSessionEntryDlg(self, self.ctx, self.smgr, self.frame, self.ps, Title="Edit Training Session", session_id=new_id)
                    ret2 = dlg2.execute()
                    if ret2 in (1, 2):
                        self.load_data()
        except Exception as e:
            self.logger.error(f"TrainingSessionList failed to open new entry dialog: {e}")

    def on_print_list(self, ev=None):
        """Open date range dialog and print the Training Sessions list report."""
        try:
            from librepy.app.components.service_appointment.print_list_date_range_dlg import (
                PrintListDateRangeDialog,
            )
            dlg = PrintListDateRangeDialog(self, self.ctx, self.smgr, self.frame, self.ps, Title="Print List")
            ret = dlg.execute()
            if ret == 1:
                start_date = getattr(dlg, 'selected_start_date', None)
                end_date = getattr(dlg, 'selected_end_date', None)
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
                self.logger.info("Training Sessions list report invoked from list view")
        except Exception as e:
            self.logger.error(f"Failed to print Training Sessions list: {e}")

    def show(self):
        super().show()
        self.load_data()
        self.resize(self.window_width, self.window_height)

    def hide(self):
        super().hide()

    def resize(self, width, height):
        try:
            self.window_width = width
            self.window_height = height - self.toolbar_offset

            # Get sidebar offset if present
            sidebar_width = getattr(self.parent, 'sidebar_width', 0)

            # Resize main container
            self.container.setPosSize(sidebar_width, self.toolbar_offset, width, height - self.toolbar_offset, POSSIZE)

            pos = self._calculate_positions()

            # Reposition controls
            if hasattr(self, 'lbl_title'):
                self.lbl_title.setPosSize(pos['title_x'], pos['title_y'], pos['title_w'], pos['title_h'], POSSIZE)
            if hasattr(self, 'lbl_search'):
                self.lbl_search.setPosSize(pos['search_label_x'], pos['search_y'], 60, 20, POSSIZE)
            if hasattr(self, 'txt_search'):
                self.txt_search.setPosSize(pos['search_x'], pos['search_y'], pos['search_w'], 20, POSSIZE)
            if hasattr(self, 'btn_new_entry'):
                self.btn_new_entry.setPosSize(pos['new_entry_x'], pos['top_button_y'], pos['top_button_width'], pos['top_button_height'], POSSIZE)
            if hasattr(self, 'btn_print_list') and self.btn_print_list is not None:
                print_list_x = pos['new_entry_x'] - (pos['top_button_width'] + 10)
                self.btn_print_list.setPosSize(print_list_x, pos['top_button_y'], pos['top_button_width'], pos['top_button_height'], POSSIZE)
            if hasattr(self, 'grid'):
                self.grid.setPosSize(pos['grid_x'], pos['grid_y'], pos['grid_w'], pos['grid_h'], POSSIZE)

            # Redraw
            if hasattr(self, 'container') and self.container.getPeer():
                self.container.getPeer().invalidate(0)
        except Exception as e:
            self.logger.error(f"Error during resize: {e}")
            self.logger.error(traceback.format_exc())

    def _calculate_positions(self):
        pad_x = int(self.window_width * 0.02)
        pad_y = int(self.window_height * 0.02)
        
        # Title - align Y with calendar component (calendar title Y = 20)
        title_h = 40
        title_w = min(360, self.window_width - 2 * pad_x)
        title_x = pad_x
        title_y = 20
        
        # Action buttons and search controls - positioned above the grid at same Y level
        top_button_width = 140
        top_button_height = 30
        button_spacing = 10
        right_margin = 50
        new_entry_x = self.window_width - (top_button_width + right_margin)
        # Position buttons below title with some spacing
        top_button_y = 95
        
        # Search controls - align with buttons
        search_y = top_button_y + (top_button_height - 20) // 2  # Center vertically with buttons
        search_label_x = pad_x
        search_x = search_label_x + 60 + 6
        # Cap the search field width so it doesn't span the whole screen
        max_search_w = 360
        available_w = max(120, self.window_width - pad_x - search_x - pad_x)
        search_w = min(max_search_w, available_w)
        
        # Grid occupies the rest
        grid_x = pad_x
        grid_y = top_button_y + top_button_height + 10  # Below buttons with 10px spacing
        grid_w = self.window_width - 2 * pad_x
        grid_h = self.window_height - grid_y - pad_y
        
        return {
            'title_x': title_x, 'title_y': title_y, 'title_w': title_w, 'title_h': title_h,
            'search_label_x': search_label_x, 'search_y': search_y,
            'search_x': search_x, 'search_w': search_w,
            'grid_x': grid_x, 'grid_y': grid_y, 'grid_w': grid_w, 'grid_h': grid_h,
            'new_entry_x': new_entry_x, 'top_button_y': top_button_y,
            'top_button_width': top_button_width, 'top_button_height': top_button_height,
        }

    def dispose(self):
        try:
            self.logger.info("Disposing TrainingSessionList")
            if hasattr(self, 'container') and self.container is not None:
                try:
                    try:
                        self.container.getPeer().setVisible(False)
                    except Exception:
                        pass
                    self.container.dispose()
                except Exception as container_error:
                    self.logger.error(f"Error disposing container: {str(container_error)}")
                finally:
                    self.container = None
        except Exception as e:
            self.logger.error(f"Error during disposal: {e}")
            self.logger.error(traceback.format_exc())
        