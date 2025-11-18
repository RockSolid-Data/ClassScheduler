from librepy.jasper_report import jasper_report_manager
from librepy.pybrex.values import pybrex_logger, JASPER_REPORTS_DIR

import os
from datetime import datetime, date


logger = pybrex_logger(__name__)


def _normalize_date(d):
    if isinstance(d, datetime):
        return d.date()
    return d


def print_training_sessions_list(start_date, end_date):
    """
    Generate a Jasper report listing all training sessions within the given date range.

    Parameters passed to the template:
      - start_date (java.util.Date)
      - end_date   (java.util.Date)
      - title      (string)
    The SQL is embedded in the JRXML template.
    """
    if not start_date or not end_date:
        raise ValueError("start_date and end_date are required")

    s = _normalize_date(start_date)
    e = _normalize_date(end_date)

    report_path = os.path.join(JASPER_REPORTS_DIR, 'TrainingSessionsList.jrxml')
    title = f"Training Sessions: {s.strftime('%Y-%m-%d')} to {e.strftime('%Y-%m-%d')}"

    report_params = {
        'start_date': {'value': s, 'type': 'date'},
        'end_date':   {'value': e, 'type': 'date'},
        'title':      {'value': title, 'type': 'string'},
    }

    logger.info(f"Printing Training Sessions list for range {s} .. {e}")
    jasper_report_manager.main(report_path, report_params)
