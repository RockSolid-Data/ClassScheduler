from librepy.app.components.calendar.calendar_view import Calendar


class AppointmentCalendar(Calendar):
    """
    Appointment Calendar component.

    For now this component only inherits the base month grid, toolbar, and
    scrolling behavior from Calendar without loading or rendering any entries.
    """

    # Unique component name used for routing/navigation
    component_name = 'appointment_calendar'

    def __init__(self, parent, ctx, smgr, frame, ps):
        super().__init__(parent, ctx, smgr, frame, ps)
