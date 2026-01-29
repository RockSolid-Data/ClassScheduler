from librepy.app.forms.training_session_form import TrainingSessionForm
from librepy.app.data.dao.teacher_dao import TeacherDAO
from librepy.app.data.dao.training_session_dao import TrainingSessionDAO
from librepy.app.data.dao.session_attendee_dao import SessionAttendeeDAO


def save_training_session(data: dict, context=None) -> dict:
    """
    Validate and persist a Training Session using BaseForm.

    Args:
        data: Dict with keys: name, teacher, session_date,
              session_time, price; optional session_id for updates.
        context: Optional context object for DAO construction/logging.

    Returns:
        - {"ok": False, "errors": [{"field", "message"}, ...]} on validation failure
        - {"ok": True, "result": <model instance>} on success
    """
    form = TrainingSessionForm(data=data, context=context)
    if not form.is_valid():
        return {"ok": False, "errors": form.errors}
    return form.save()


def delete_training_session(session_id: int, context=None) -> dict:
    """Delete a Training Session by id.
    
    First deletes all associated attendees to avoid foreign key constraint violations.

    Returns: {"ok": True, "deleted": n} when n > 0, else {"ok": False}
    """
    logger = getattr(context, "logger", context)
    
    # First, delete all attendees associated with this session
    attendee_dao = SessionAttendeeDAO(logger)
    attendee_dao.delete_where(
        attendee_dao.model_class.session == session_id,
        operation_name='delete SessionAttendees for training session'
    )
    
    # Now delete the training session itself
    dao = TrainingSessionDAO(logger)
    n = dao.delete_where(dao.model_class.session_id == session_id, operation_name='delete TrainingSession by id')
    return {"ok": bool(n and n > 0), "deleted": n or 0}


def load_teacher_pairs(context=None):
    """
    Return list of (id, label) pairs for teacher list controls.
    Replicates the Employee Contract dialog pattern.
    """
    dao = TeacherDAO(getattr(context, "logger", context))
    rows = dao.get_all_for_grid() or []  # [{id, name, email}]
    return [(r.get('id'), r.get('name') or '') for r in rows]
