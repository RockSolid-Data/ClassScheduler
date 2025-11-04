from librepy.app.data.base_dao import BaseDAO
from librepy.app.data.model import Teacher


class TeacherDAO(BaseDAO):
    """Data-access for Teacher model.

    Provides simple helpers to retrieve teachers for grid display.
    """

    def __init__(self, logger):
        super().__init__(Teacher, logger)

    def create(self, first_name, last_name, email):
        """Create a new Teacher and return the model instance."""
        def _q():
            return Teacher.create(
                first_name=first_name,
                last_name=last_name,
                email=email,
            )
        return self.safe_execute('create Teacher', _q, default_return=None)

    def update(self, teacher_id, first_name=None, last_name=None, email=None):
        """Update provided fields on Teacher and return the model instance."""
        updates = {}
        if first_name is not None:
            updates['first_name'] = first_name
        if last_name is not None:
            updates['last_name'] = last_name
        if email is not None:
            updates['email'] = email
        
        if updates:
            self.update_fields(Teacher.teacher_id == teacher_id, updates, operation_name='update Teacher')
        # Return the (possibly updated) instance
        def _fetch():
            return Teacher.get(Teacher.teacher_id == teacher_id)
        return self.safe_execute('get Teacher after update', _fetch, default_return=None)

    def get_all_teachers(self):
        """Return list of dicts for all teachers.

        Keys: teacher_id, first_name, last_name, email
        """
        return self.get_all_dicts(
            fields=[
                'teacher_id',
                'first_name',
                'last_name',
                'email',
            ],
            order_by=Teacher.last_name,
            operation_name='get_all_teachers'
        )

    def get_all_for_grid(self):
        """Return list of dicts tailored for grid display in Teachers tab.

        Keys: id, name, email
        """
        rows = self.get_all_teachers() or []
        results = []
        for r in rows:
            fn = (r.get('first_name') or '').strip()
            ln = (r.get('last_name') or '').strip()
            full = f"{fn} {ln}".strip() if (fn or ln) else ''
            results.append({
                'id': r.get('teacher_id'),
                'name': full,
                'email': r.get('email') or '',
            })
        return results
