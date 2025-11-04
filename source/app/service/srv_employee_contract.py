from typing import Any, Dict

from librepy.app.forms.employee_contract_form import EmployeeContractForm
from librepy.app.data.dao.employee_contract_dao import EmployeeContractDAO


def save_employee_contract(data: Dict[str, Any], context=None) -> Dict[str, Any]:
    """
    Validate and persist an Employee Contract using BaseForm.

    Args:
        data: Dict with fields: employee_id, start_date, end_date, optional time_in, time_out; optional contract_id.
        context: Optional context object; passed to form for DAO construction/logging.

    Returns:
        - {"ok": False, "errors": [{"field", "message"}, ...]} when validation fails
        - {"ok": True, "result": <model instance>} on success (create/update)
    """
    form = EmployeeContractForm(data=data, context=context)
    if not form.is_valid():
        return {"ok": False, "errors": form.errors}
    return form.save()



def delete_employee_contract(contract_id: int, context=None) -> Dict[str, Any]:
    """Delete an EmployeeContract by id.

    Returns: {"ok": True, "deleted": n} when n > 0, else {"ok": False}
    """
    dao = EmployeeContractDAO(getattr(context, "logger", context))
    n = dao.delete_where(dao.model_class.contract_id == contract_id, operation_name='delete EmployeeContract by id')
    return {"ok": bool(n and n > 0), "deleted": n or 0}
