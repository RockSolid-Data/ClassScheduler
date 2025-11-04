from typing import Any, Dict, Optional
from datetime import date as dt_date, time as dt_time, datetime

from librepy.app.forms.base_form import BaseForm
from librepy.app.data.dao.employee_contract_dao import EmployeeContractDAO


class EmployeeContractForm(BaseForm):
    class Meta(BaseForm.Meta):
        dao = None
        dao_factory = staticmethod(lambda ctx: EmployeeContractDAO(getattr(ctx, "logger", ctx)))
        create_fn = "create"
        update_fn = "update"
        pk_field = "contract_id"

    def _parse_date(self, v) -> Optional[dt_date]:
        if v is None:
            return None
        if isinstance(v, dt_date) and not isinstance(v, datetime):
            return v
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return None
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
                try:
                    return datetime.strptime(s, fmt).date()
                except ValueError:
                    continue
        return None

    def _parse_time(self, v) -> Optional[dt_time]:
        if v is None:
            return None
        if isinstance(v, dt_time):
            return v
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return None
            for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p"):
                try:
                    return datetime.strptime(s, fmt).time()
                except ValueError:
                    continue
        return None

    def clean(self) -> None:
        # Incoming payload fields
        raw_contract_id = self.get("contract_id")
        raw_employee_id = self.require("employee_id")
        raw_start_date = self.require("start_date") if not self.partial else self.get("start_date")
        raw_end_date = self.require("end_date") if not self.partial else self.get("end_date")
        raw_time_in = self.get("time_in")
        raw_time_out = self.get("time_out")

        cleaned: Dict[str, Any] = {}

        # PK (optional)
        if raw_contract_id is not None:
            try:
                cleaned["contract_id"] = int(raw_contract_id) if str(raw_contract_id).strip() != "" else None
            except (TypeError, ValueError):
                self.add_error("contract_id", "Invalid contract id")

        # employee -> as FK id is accepted by Peewee
        try:
            emp_id_int = int(raw_employee_id) if raw_employee_id is not None and str(raw_employee_id).strip() != "" else None
        except (TypeError, ValueError):
            emp_id_int = None
        if (raw_employee_id is not None) or not self.partial:
            if not emp_id_int or emp_id_int <= 0:
                self.add_error("employee_id", "Valid employee id is required")
            else:
                cleaned["employee"] = emp_id_int

        # Dates
        if (raw_start_date is not None) or not self.partial:
            sd = raw_start_date if isinstance(raw_start_date, dt_date) and not isinstance(raw_start_date, datetime) else self._parse_date(raw_start_date)
            if sd is None:
                self.add_error("start_date", "Invalid or missing start date")
            else:
                cleaned["start_date"] = sd
        if (raw_end_date is not None) or not self.partial:
            ed = raw_end_date if isinstance(raw_end_date, dt_date) and not isinstance(raw_end_date, datetime) else self._parse_date(raw_end_date)
            if ed is None:
                self.add_error("end_date", "Invalid or missing end date")
            else:
                cleaned["end_date"] = ed

        # Ensure end_date >= start_date when both present
        sd = cleaned.get("start_date")
        ed = cleaned.get("end_date")
        if sd is not None and ed is not None and ed < sd:
            self.add_error("end_date", "End date must be on or after start date")

        # Times (optional). If both provided, ensure time_in < time_out
        if raw_time_in is not None:
            tin = raw_time_in if isinstance(raw_time_in, dt_time) else self._parse_time(raw_time_in)
            if tin is None:
                self.add_error("time_in", "Invalid time")
            else:
                cleaned["time_in"] = tin
        if raw_time_out is not None:
            tout = raw_time_out if isinstance(raw_time_out, dt_time) else self._parse_time(raw_time_out)
            if tout is None:
                self.add_error("time_out", "Invalid time")
            else:
                cleaned["time_out"] = tout

        if ("time_in" in cleaned) and ("time_out" in cleaned):
            if cleaned["time_in"] >= cleaned["time_out"]:
                self.add_error("time_in", "time_in must be before time_out")

        self.cleaned_data.update(cleaned)
