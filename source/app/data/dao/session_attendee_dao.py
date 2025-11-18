from librepy.app.data.base_dao import BaseDAO
from librepy.app.data.model import SessionAttendee, TrainingSession


class SessionAttendeeDAO(BaseDAO):
    """Data-access for SessionAttendee model.

    Provides helpers to retrieve attendees for a specific session for grid display,
    and basic create/update methods following the existing DAO pattern.
    """

    def __init__(self, logger):
        super().__init__(SessionAttendee, logger)

    # ---- CRUD helpers ----
    def create(self, session, name, email=None, phone=None, paid=False, notes=None):
        """Create a new SessionAttendee and return the model instance."""
        def _q():
            return SessionAttendee.create(
                session=session,
                name=name,
                email=email,
                phone=phone,
                paid=bool(paid),
                notes=notes,
            )
        return self.safe_execute('create SessionAttendee', _q, default_return=None)

    def update(self, attendee_id, session=None, name=None, email=None, phone=None, paid=None, notes=None):
        """Update fields on SessionAttendee and return the model instance."""
        updates = {
            'session': session,
            'name': name,
            'email': email,
            'phone': phone,
            'paid': paid,
            'notes': notes,
        }
        self.update_fields(SessionAttendee.attendee_id == attendee_id, updates, operation_name='update SessionAttendee')
        def _fetch():
            return SessionAttendee.get(SessionAttendee.attendee_id == attendee_id)
        return self.safe_execute('get SessionAttendee after update', _fetch, default_return=None)

    # ---- Queries for UI ----
    def get_all_for_grid(self, session_id):
        """Return list of dicts for attendees of a given session, tailored for grid display.

        Keys: id, name, email, phone, paid, notes
        """
        def _query():
            q = (SessionAttendee
                 .select()
                 .where(SessionAttendee.session == int(session_id))
                 .order_by(SessionAttendee.attendee_id))
            rows = []
            for a in q:
                rows.append({
                    'id': getattr(a, 'attendee_id', None),
                    'name': getattr(a, 'name', '') or '',
                    'email': getattr(a, 'email', '') or '',
                    'phone': getattr(a, 'phone', '') or '',
                    'paid': bool(getattr(a, 'paid', False)),
                })
            return rows
        return self.safe_execute('get attendees for session (grid)', _query, default_return=[])

    def get_attendance_for_grid(self, session_id):
        """Return list of dicts for Attendance tab grid.

        Only includes attendees with paid == True, because attendance only counts if payment.
        Keys per row: id, name, attendance (attendance maps to model.attended)
        """
        def _query():
            q = (SessionAttendee
                 .select(SessionAttendee.attendee_id, SessionAttendee.name, SessionAttendee.attended)
                 .where(
                     (SessionAttendee.session == int(session_id)) &
                     (SessionAttendee.paid == True)
                 )
                 .order_by(SessionAttendee.attendee_id))
            rows = []
            for a in q:
                rows.append({
                    'id': getattr(a, 'attendee_id', None),
                    'name': getattr(a, 'name', '') or '',
                    'attendance': bool(getattr(a, 'attended', False)),
                })
            return rows
        return self.safe_execute('get attendance for session (paid only)', _query, default_return=[])

    def get_by_id(self, attendee_id):
        def _q():
            return SessionAttendee.get(SessionAttendee.attendee_id == attendee_id)
        return self.safe_execute('get SessionAttendee by id', _q, default_return=None)

    def toggle_attendance(self, attendee_id) -> bool:
        """Toggle the 'attended' boolean for a given attendee_id.

        Uses Peewee's boolean inversion to generate SQL like: attended = NOT attended
        Returns True if at least one row was updated, False otherwise.
        """
        def _q():
            aid = attendee_id
            q = (SessionAttendee
                 .update(attended=~SessionAttendee.attended)
                 .where(SessionAttendee.attendee_id == aid))
            return q.execute()

        affected = self.safe_execute('toggle attendance', _q, default_return=0)

        return bool(affected and affected > 0)

    def to_dict(self, inst):
        if inst is None:
            return None
        return {
            'attendee_id': getattr(inst, 'attendee_id', None),
            'session': getattr(inst, 'session_id', getattr(inst, 'session', None)),
            'name': getattr(inst, 'name', ''),
            'email': getattr(inst, 'email', None),
            'phone': getattr(inst, 'phone', None),
            'paid': bool(getattr(inst, 'paid', False)),
            'notes': getattr(inst, 'notes', None),
        }
