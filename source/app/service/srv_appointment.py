
from librepy.app.forms.service_appointment_form import ServiceAppointmentForm
from librepy.app.data.dao.service_appointment_dao import ServiceAppointmentDAO


def save_service_appointment(data: dict, context=None) -> dict:
    """
    Validate and persist a Service Appointment using BaseForm.

    Args:
        data: Dict with keys from UI commit: name, phone, email, date, time, notes; optional service_apt_id.
        context: Optional context object; passed to form for DAO construction/logging.

    Returns:
        - {"ok": False, "errors": [{"field", "message"}, ...]} when validation fails
        - {"ok": True, "result": <model instance>} on success (create/update)
    """
    form = ServiceAppointmentForm(data=data, context=context)
    if not form.is_valid():
        return {"ok": False, "errors": form.errors}
    return form.save()


def delete_service_appointment(service_apt_id: int, context=None) -> dict:
    """Delete a Service Appointment by id.

    Returns: {"ok": True, "deleted": n} when n > 0, else {"ok": False}
    """
    dao = ServiceAppointmentDAO(getattr(context, "logger", context))
    n = dao.delete_where(dao.model_class.service_apt_id == service_apt_id, operation_name='delete ServiceAppointment by id')
    return {"ok": bool(n and n > 0), "deleted": n or 0}
