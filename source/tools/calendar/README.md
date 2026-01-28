# Calendar Component

A comprehensive, multi-view calendar component for LibreOffice UNO applications with support for Month, Week, and Day views.

## Features

### Multi-View Support
- **Month View**: Traditional calendar grid with expandable rows for multiple events
- **Week View**: 7-day column view with hourly time slots (6 AM - 9 PM)
- **Day View**: Single-day view spanning full width with hourly time slots

### Advanced UI Features
- **Dynamic Row Heights**: Rows automatically expand to accommodate overlapping events
- **Frozen Headers**: Day/date headers remain visible during scrolling
- **Smooth Scrolling**: Vertical scrolling with up/down buttons and scrollbar
- **Responsive Layout**: Automatically adjusts to window resizing
- **Row-Based Event Stacking**: Multiple events in the same time slot stack vertically
- **Grid Lines**: Clean visual separation using lines (not labels) to prevent overlay issues

### Data Management
- **Flexible Data Loading**: Callback-based architecture for custom data sources
- **Filter Support**: Built-in filtering with customizable filter options
- **Color Coding**: Per-item color customization via callbacks
- **Click Handling**: Event callbacks for item interactions

### Print Support
- **All Views Printable**: Generate formatted documents for Month, Week, and Day views
- **Auto-Generated Tables**: Creates LibreOffice Writer documents with proper formatting
- **Color Preservation**: Event colors maintained in printed output

## Installation

Place the calendar module in your LibreOffice Python package:

```
your_package/
├── tools/
│   └── calendar/
│       ├── __init__.py
│       ├── calendar.py          # Main calendar controller
│       ├── month_calendar.py    # Month view implementation
│       ├── week_calendar.py     # Week view implementation
│       ├── day_calendar.py      # Day view implementation
│       └── README.md
```

## Quick Start

### Basic Implementation

```python
from librepy.tools.calendar.calendar import Calendar

class MyCalendarView:
    def __init__(self, parent, ctx, smgr, frame, ps):
        # Define action buttons (optional)
        action_buttons = [
            {
                'label': '+ Create Event',
                'callback': self.create_event,
                'color': 0x2C3E50
            },
            {
                'label': 'Print Calendar',
                'callback': self.print_calendar,
                'color': 0x2C3E50
            }
        ]
        
        # Initialize calendar with callbacks
        self.calendar = Calendar(
            parent=parent,
            ctx=ctx,
            smgr=smgr,
            frame=frame,
            ps=ps,
            get_items_callback=self._get_calendar_items,
            get_filter_options_callback=self._get_filter_options,
            get_item_color_callback=self._get_item_color,
            on_item_click_callback=self._handle_item_click,
            filter_label="Filter By",
            action_buttons=action_buttons,
            calendar_title="My Calendar",
            default_view="Month",
            toolbar_offset=0
        )
    
    def _get_calendar_items(self, start_date, end_date, filter_value):
        """
        Load calendar items for the given date range.
        
        Returns:
            dict: {
                '2025-01-15': [
                    {
                        'id': 'unique_id',
                        'title': 'Event Title',
                        'start_time': datetime_obj,  # Full datetime with time
                        'end_time': datetime_obj,    # Optional
                        'duration_hours': 2.0,       # Optional
                        'color': 0x3498DB,           # Optional
                        'type': 'meeting',           # Optional, your custom fields
                        # ... any other custom fields
                    },
                    ...
                ]
            }
        """
        items_by_date = {}
        
        # Your data loading logic here
        # Query database, filter by date range and filter_value
        
        return items_by_date
    
    def _get_filter_options(self):
        """
        Return list of filter options for the dropdown.
        
        Returns:
            list: ['All', 'Team A', 'Team B', 'Events']
        """
        return ["All", "Team A", "Team B", "Events"]
    
    def _get_item_color(self, item):
        """
        Determine color for an item.
        
        Args:
            item (dict): The calendar item
            
        Returns:
            int: Color as hex integer (e.g., 0x3498DB)
        """
        # Option 1: Color stored in item
        if 'color' in item:
            return item['color']
        
        # Option 2: Color based on item type
        type_colors = {
            'meeting': 0x3498DB,  # Blue
            'deadline': 0xE74C3C,  # Red
            'event': 0x9B59B6,     # Purple
            'task': 0x2ECC71       # Green
        }
        return type_colors.get(item.get('type'), 0x95A5A6)  # Default gray
    
    def _handle_item_click(self, item_id, item):
        """
        Handle when user clicks on a calendar item.
        
        Args:
            item_id: The item's unique identifier
            item (dict): The full item data
        """
        # Open editor, show details, etc.
        print(f"Clicked item: {item_id}")
        # self.open_item_dialog(item_id)
    
    def create_event(self, event):
        """Handle create event button click"""
        # Open your event creation dialog
        pass
    
    def print_calendar(self, event):
        """Handle print button click"""
        if self.calendar.current_view:
            self.calendar.current_view.print_calendar(event)
```

## Calendar Configuration

### Initialization Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `parent` | object | Yes | Parent component reference |
| `ctx` | UNO context | Yes | Component context |
| `smgr` | UNO service manager | Yes | Service manager |
| `frame` | XFrame | Yes | Frame object |
| `ps` | tuple | Yes | Position/size (x, y, width, height) |
| `get_items_callback` | function | Yes | Function to load calendar data |
| `get_filter_options_callback` | function | No | Function to get filter options |
| `get_item_color_callback` | function | No | Function to determine item colors |
| `on_item_click_callback` | function | No | Function to handle item clicks |
| `filter_label` | str | No | Label for filter dropdown (default: "Filter") |
| `action_buttons` | list | No | Additional action buttons |
| `calendar_title` | str | No | Calendar title (default: "Calendar") |
| `default_view` | str | No | Initial view: "Month", "Week", or "Day" |
| `toolbar_offset` | int | No | Top offset for toolbar (default: 0) |

### Action Button Format

```python
{
    'label': 'Button Text',
    'callback': function_reference,
    'color': 0x2C3E50  # Hex color
}
```

## Data Format Specifications

### Calendar Item Structure

```python
{
    'id': 'unique_identifier',           # Required: Unique ID for the item
    'title': 'Event Title',              # Required: Display text
    'start_time': datetime(2025, 1, 15, 9, 0),  # Required for Week/Day views
    'end_time': datetime(2025, 1, 15, 11, 0),   # Optional
    'duration_hours': 2.0,               # Optional: Duration in hours
    'color': 0x3498DB,                   # Optional: Override default color
    
    # Custom fields (preserved and passed back in callbacks)
    'type': 'meeting',
    'description': 'Team standup',
    'location': 'Conference Room A',
    'attendees': ['user1', 'user2'],
    # ... any other fields your application needs
}
```

### Return Format for `get_items_callback`

```python
{
    '2025-01-15': [item1, item2, ...],
    '2025-01-16': [item3, item4, ...],
    # ... more dates
}
```

**Important Notes:**
- Keys must be date strings in format `'YYYY-MM-DD'`
- `start_time` should be a `datetime` object with time information for Week/Day views
- For Month view, only the date portion is used
- Items without `start_time` will default to the start of the day

## View-Specific Features

### Month View
- **Grid Layout**: Traditional month calendar grid
- **Row Expansion**: Rows expand to fit all events for each day
- **Multi-Item Display**: Shows multiple items per day cell
- **Week Headers**: Displays day names (Sun, Mon, etc.)
- **Previous/Next Month**: Shows dates from adjacent months

### Week View
- **7-Day Columns**: Sunday through Saturday
- **Hourly Time Slots**: 6 AM to 9 PM (configurable)
- **Fixed Event Height**: All events have consistent 20px height
- **Vertical Stacking**: Multiple events at same time stack vertically
- **Dynamic Row Heights**: Hour rows expand for overlapping events
- **Time Column**: Left column shows hour labels

### Day View
- **Full Width**: Single day column spans entire available width
- **Same Structure as Week**: Consistent UI with week view
- **Extended Titles**: More space for longer event titles
- **Hourly Breakdown**: Same 6 AM to 9 PM time range

## Configuration Options

### Time Range (Week/Day Views)

Edit the configuration in `week_config` or `day_config`:

```python
self.week_config = {
    'start_hour': 6,      # Start at 6 AM
    'end_hour': 21,       # End at 9 PM
    'hour_height': 80,    # Height per hour slot in pixels
    'time_label_width': 70,
    'colors': {
        'header_bg': 0xE0E0E0,
        'today_header_bg': 0x3498DB,
        'time_slot_bg': 0xFFFFFF,
        'time_slot_border': 0xDDDDDD,
        'item_default': 0x3498DB
    }
}
```

### Month View Settings

```python
self.calendar_config = {
    'day_label_height': 25,
    'item_button_height': 20,
    'item_button_spacing': 2,
    'item_font_size': 9,
    'colors': {
        'day_label_bg': 0xF8F8F8,
        'header_bg': 0xE3E8EF,
        'today_bg': 0xFFE5E5,
        'selected_bg': 0xE3F2FD
    }
}
```

## Advanced Usage

### Custom Filtering

```python
def _get_filter_options(self):
    # Dynamic filter options from database
    teams = self.database.get_all_teams()
    return ["All"] + [team.name for team in teams] + ["Events"]

def _get_calendar_items(self, start_date, end_date, filter_value):
    if filter_value == "All":
        items = self.database.get_all_items(start_date, end_date)
    elif filter_value == "Events":
        items = self.database.get_events_only(start_date, end_date)
    else:
        items = self.database.get_items_by_team(filter_value, start_date, end_date)
    
    # Transform to calendar format
    return self._transform_items(items)
```

### Color Schemes

```python
def _get_item_color(self, item):
    # Priority-based coloring
    priority = item.get('priority', 'normal')
    
    priority_colors = {
        'urgent': 0xE74C3C,   # Red
        'high': 0xE67E22,     # Orange
        'normal': 0x3498DB,   # Blue
        'low': 0x95A5A6       # Gray
    }
    
    return priority_colors.get(priority, 0x3498DB)
```

### Multi-Day Events

```python
def _get_calendar_items(self, start_date, end_date, filter_value):
    items_by_date = {}
    
    # Get your events
    events = self.get_events_from_database(start_date, end_date)
    
    for event in events:
        # For multi-day events, add to each day
        current_date = event.start_date
        while current_date <= event.end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            if date_str not in items_by_date:
                items_by_date[date_str] = []
            
            items_by_date[date_str].append({
                'id': event.id,
                'title': event.title,
                'start_time': event.start_time if current_date == event.start_date else 
                             datetime.combine(current_date, datetime.min.time()),
                'color': self._get_event_color(event)
            })
            
            current_date += timedelta(days=1)
    
    return items_by_date
```

## Print Functionality

All views support printing:

```python
# From your calendar instance
calendar.current_view.print_calendar()

# Or from action button
action_buttons = [
    {
        'label': 'Print',
        'callback': lambda e: calendar.current_view.print_calendar(e),
        'color': 0x2C3E50
    }
]
```

Generated documents include:
- **Month View**: Full month grid with all events
- **Week View**: 7-day table with hourly breakdown
- **Day View**: Single-day table with event details

## Navigation

Calendar provides navigation methods:
- `navigate_to_today()`: Jump to current date
- `navigate_prev()`: Previous month/week/day
- `navigate_next()`: Next month/week/day

Navigation buttons are automatically created in the header.

## Troubleshooting

### Events Not Appearing

**Issue**: Items don't show up in Week/Day view

**Solution**: Ensure `start_time` is a `datetime` object with time information:
```python
# Wrong
item['start_time'] = date(2025, 1, 15)

# Correct
item['start_time'] = datetime(2025, 1, 15, 9, 0)  # 9:00 AM
```

### Items Hidden Behind Grid

**Issue**: Event buttons not visible

**Solution**: This was fixed by using `add_line` instead of labels for grid. Ensure you're using the latest version.

### Overlapping Events Not Stacking

**Issue**: Multiple events at same time overlap instead of stacking

**Solution**: The calendar automatically detects and stacks overlapping events. Ensure all events have proper `start_time` values.

### Scroll Issues

**Issue**: Partial rows appearing or scroll not working

**Solution**: The calendar uses fixed event heights and dynamic row expansion. This should be automatic. Check that your hour configuration is valid.

## Performance Considerations

### Large Data Sets

For applications with many calendar items:

1. **Implement Pagination**: Only load items for visible date range
2. **Cache Results**: Store loaded data to avoid repeated queries
3. **Optimize Callbacks**: Make database queries efficient

```python
def _get_calendar_items(self, start_date, end_date, filter_value):
    # Check cache first
    cache_key = (start_date, end_date, filter_value)
    if cache_key in self._cache:
        return self._cache[cache_key]
    
    # Load only what's needed
    items = self.database.get_items_in_range(start_date, end_date, filter_value)
    result = self._transform_items(items)
    
    # Cache for future use
    self._cache[cache_key] = result
    return result
```

## License

This calendar component is part of your LibreOffice application. Adjust licensing as needed.

## Support

For issues, questions, or contributions, contact the development team.

## Version History

- **v1.0.0**: Initial release with Month, Week, and Day views
  - Dynamic row heights for overlapping events
  - Scrolling support with frozen headers
  - Print functionality for all views
  - Callback-based data architecture
  - Filter and color customization

## Credits

Developed by Josiah Aguilar
Created: November 13, 2025

