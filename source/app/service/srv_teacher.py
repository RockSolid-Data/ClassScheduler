from librepy.app.forms.teacher_form import TeacherForm
from librepy.app.data.dao.teacher_dao import TeacherDAO


def save_teacher(data: dict, context=None) -> dict:
    """
    Validate and persist a Teacher using BaseForm.

    Args:
        data: Dict with keys from UI commit: first_name, last_name, email; optional teacher_id.
        context: Optional context object; passed to form for DAO construction/logging.

    Returns:
        - {"ok": False, "errors": [{"field", "message"}, ...]} when validation fails
        - {"ok": True, "result": <model instance>} on success (create/update)
    """
    form = TeacherForm(data=data, context=context)
    if not form.is_valid():
        return {"ok": False, "errors": form.errors}
    return form.save()


def delete_teacher(teacher_id: int, context=None) -> dict:
    """Delete a Teacher by id.

    Returns: {"ok": True, "deleted": n} when n > 0, else {"ok": False}
    """
    dao = TeacherDAO(getattr(context, "logger", context))
    n = dao.delete_where(dao.model_class.teacher_id == teacher_id, operation_name='delete Teacher by id')
    return {"ok": bool(n and n > 0), "deleted": n or 0}
