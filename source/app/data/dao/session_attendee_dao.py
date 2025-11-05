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
        """Create a new SessionAttendee and return the model instance.

        Args:
            session: session id (int) or TrainingSession instance
            name: attendee name
            email: optional email
            phone: optional phone
            paid: boolean flag
            notes: optional notes
        """
        def _q():
            sess = session
            if not isinstance(sess, TrainingSession):
                try:
                    sess = TrainingSession.get(TrainingSession.session_id == int(session))
                except Exception:
                    # Let Peewee raise if invalid during create
                    pass
            return SessionAttendee.create(
                session=sess,
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

    def get_by_id(self, attendee_id):
        def _q():
            return SessionAttendee.get(SessionAttendee.attendee_id == attendee_id)
        return self.safe_execute('get SessionAttendee by id', _q, default_return=None)

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
