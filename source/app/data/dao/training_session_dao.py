from librepy.app.data.base_dao import BaseDAO
from librepy.app.data.model import TrainingSession
from datetime import time, date

class TrainingSessionDAO(BaseDAO):

    def __init__(self, logger):
        super().__init__(TrainingSession, logger)

    def _row_to_dict(self, row):
        """Map TrainingSession row to minimal dict for calendar usage."""
        try:
            ts = row
            return {
                'id': getattr(ts, 'session_id', None),
                'date': getattr(ts, 'session_date', None),
                'title': getattr(ts, 'name', None),
                'status': getattr(ts, 'status', 'scheduled') if hasattr(ts, 'status') else 'scheduled',
            }
        except Exception:
            return {
                'id': getattr(row, 'session_id', None),
                'date': getattr(row, 'session_date', None),
                'title': getattr(row, 'name', None),
                'status': 'scheduled',
            }

    def get_sessions_between(self, start_date, end_date):
        """Query TrainingSession rows within [start_date, end_date].

        Returns: List[dict] with keys: id, date (date or 'YYYY-MM-DD'), title, status
        """
        def _query():
            query = (TrainingSession
                     .select()
                     .where((TrainingSession.session_date >= start_date) &
                            (TrainingSession.session_date <= end_date))
                     .order_by(TrainingSession.session_date))
            return [self._row_to_dict(row) for row in query]

        return self.safe_execute('get_sessions_between', _query, default_return=[])

    def get_session_by_id(self, session_id):
        """Fetch one TrainingSession by id.

        Returns: dict with keys: id, date, title, status or None if not found
        """
        def _query():
            row = TrainingSession.get(TrainingSession.session_id == session_id)
            return self._row_to_dict(row)

        return self.safe_execute('get_session_by_id', _query, default_return=None)

    def get_training_sessions(self):
        """Return list of sessions joined to teachers for grid display.

        Each dict contains: id, name, teacher_name, session_date, session_time, price
        session_date is formatted as 'YYYY-MM-DD'; session_time as 'HH:MM'.
        """
        sql = (
            "SELECT c.session_id AS id, c.name, "
            "concat(t.first_name, ' ', t.last_name) AS teacher_name, "
            "c.session_date, c.session_time, c.price "
            "FROM class_scheduler_admin.trainingsession c "
            "JOIN class_scheduler_admin.teacher t ON c.teacher_id = t.teacher_id "
            "ORDER BY c.session_date, c.session_time"
        )

        def _norm_time(v):
            try:
                if isinstance(v, time):
                    return v.strftime('%H:%M')
                s = str(v) if v is not None else ''
                if len(s) >= 5 and ':' in s:
                    return s[:5]
                return s
            except Exception:
                return str(v) if v is not None else ''

        def _norm_date(v):
            try:
                if isinstance(v, date):
                    return v.strftime('%Y-%m-%d')
                return str(v) if v is not None else ''
            except Exception:
                return str(v) if v is not None else ''

        def _query():
            cur = self.database.execute_sql(sql)
            rows = cur.fetchall()
            results = []
            for r in rows:
                # Expect order: id, name, teacher_name, session_date, session_time, price
                rec = {
                    'id': r[0],
                    'name': r[1],
                    'teacher_name': r[2],
                    'session_date': _norm_date(r[3]),
                    'session_time': _norm_time(r[4]),
                    'price': float(r[5]) if r[5] is not None else None,
                }
                results.append(rec)
            return results

        return self.safe_execute('get_training_sessions', _query, default_return=[]) 