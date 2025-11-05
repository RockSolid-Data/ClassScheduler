from typing import Any, Dict, Optional
from datetime import date as dt_date, time as dt_time, datetime

from librepy.app.forms.base_form import BaseForm
from librepy.app.data.dao.training_session_dao import TrainingSessionDAO


class TrainingSessionForm(BaseForm):
    class Meta(BaseForm.Meta):
        dao = None
        dao_factory = staticmethod(lambda ctx: TrainingSessionDAO(getattr(ctx, "logger", ctx)))
        create_fn = "create"
        update_fn = "update"
        pk_field = "session_id"

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
        # Inputs
        raw_session_id = self.get("session_id")
        raw_name = self.require("name")
        raw_teacher = self.require("teacher")
        raw_session_date = self.require("session_date") if not self.partial else self.get("session_date")
        raw_session_time = self.require("session_time") if not self.partial else self.get("session_time")
        raw_price = self.require("price") if not self.partial else self.get("price")

        cleaned: Dict[str, Any] = {}

        # PK (optional for updates)
        if raw_session_id is not None:
            try:
                cleaned["session_id"] = int(raw_session_id) if str(raw_session_id).strip() != "" else None
            except (TypeError, ValueError):
                self.add_error("session_id", "Invalid session id")

        # name
        if (raw_name is not None) or not self.partial:
            nm = (str(raw_name or "")).strip()
            if not nm:
                self.add_error("name", "Name is required")
            elif len(nm) > 45:
                self.add_error("name", "Name cannot exceed 45 characters")
            else:
                cleaned["name"] = nm

        # teacher FK (accept integer id)
        if (raw_teacher is not None) or not self.partial:
            try:
                t_id = int(raw_teacher) if raw_teacher is not None and str(raw_teacher).strip() != "" else None
            except (TypeError, ValueError):
                t_id = None
            if not t_id or t_id <= 0:
                self.add_error("teacher", "Valid teacher id is required")
            else:
                cleaned["teacher"] = t_id

        # session_date
        if (raw_session_date is not None) or not self.partial:
            sd = raw_session_date if isinstance(raw_session_date, dt_date) and not isinstance(raw_session_date, datetime) else self._parse_date(raw_session_date)
            if sd is None:
                self.add_error("session_date", "Invalid or missing session date")
            else:
                cleaned["session_date"] = sd

        # session_time
        if (raw_session_time is not None) or not self.partial:
            st = raw_session_time if isinstance(raw_session_time, dt_time) else self._parse_time(raw_session_time)
            if st is None:
                self.add_error("session_time", "Invalid or missing session time")
            else:
                cleaned["session_time"] = st

        # price (positive numeric)
        if (raw_price is not None) or not self.partial:
            try:
                price_val = float(raw_price)
            except (TypeError, ValueError):
                price_val = None
            if price_val is None or price_val <= 0:
                self.add_error("price", "Price must be a positive number")
            else:
                cleaned["price"] = price_val

        self.cleaned_data.update(cleaned)
