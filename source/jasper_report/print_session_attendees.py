from librepy.jasper_report import jasper_report_manager
from librepy.pybrex.values import pybrex_logger, JASPER_REPORTS_DIR

import os
from datetime import date, datetime, time as dtime


logger = pybrex_logger(__name__)


def _normalize_date(d):
    if isinstance(d, datetime):
        return d.date()
    return d


def _normalize_time(t):
    # Jasper will accept a string time nicely for labels
    if isinstance(t, dtime):
        return t.strftime('%H:%M')
    return t or ''


def print_session_attendees(session_id: int, session_date=None, session_time=None, session_name: str = ''):
    """
    Generate/print a Jasper report listing attendees for a specific training session.

    Parameters passed to the template for display:
      - id
      - date
      - time
      - name

    The actual attendees are fetched by an internal SQL query filtered by session_id.
    """
    if not session_id:
        raise ValueError('session_id is required')

    report_path = os.path.join(JASPER_REPORTS_DIR, 'SessionAttendees.jrxml')

    # Coerce date/time for display and UNO compatibility (jasper_report_manager handles 'date' type)
    disp_date = _normalize_date(session_date)
    disp_time = _normalize_time(session_time)

    # Build the SQL that the JRXML will execute via $P!{query_text}
    query_text = (
        "SELECT\n"
        "    attendee_id,\n"
        "    name,\n"
        "    email,\n"
        "    phone,\n"
        "    CASE WHEN paid = true THEN 'Yes' ELSE 'No' END AS paid\n"
        "FROM class_scheduler_admin.sessionattendee\n"
        f"WHERE session_id = {int(session_id)};"
    )

    report_params = {
        'id':    {'value': int(session_id), 'type': 'int'},
        'date':  {'value': disp_date, 'type': 'date'},
        'time':  {'value': str(disp_time), 'type': 'string'},
        'name':  {'value': session_name or '', 'type': 'string'},
        'query_text': {'value': query_text, 'type': 'string'},
        # A composed title is handy
        'title': {'value': f"Attendees - {session_name} ({disp_date}) {disp_time}", 'type': 'string'},
    }

    logger.info(f"Printing session attendees report for session_id={session_id}")
    jasper_report_manager.main(report_path, report_params)
