from typing import Any, Dict, Optional
from datetime import date as dt_date, time as dt_time, datetime

from librepy.app.forms.base_form import BaseForm
from librepy.app.data.dao.service_appointment_dao import ServiceAppointmentDAO


class ServiceAppointmentForm(BaseForm):
    class Meta(BaseForm.Meta):
        dao = None
        dao_factory = staticmethod(lambda context: ServiceAppointmentDAO(getattr(context, "logger", context)))
        create_fn = "create"
        update_fn = "update"
        pk_field = "service_apt_id"

    def _parse_date(self, v) -> Optional[dt_date]:
        if v is None:
            return None
        if isinstance(v, dt_date) and not isinstance(v, datetime):
            return v
        # Try common string formats
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
        # Raw inputs from UI
        svc_id = self.get("service_apt_id")
        name = self.require("name")
        phone = self.require("phone")
        email = self.require("email")
        date_in = self.require("date") if not self.partial else self.get("date")
        time_in = self.get("time")
        notes_in = self.get("notes")

        # Validate and normalize
        cleaned: Dict[str, Any] = {}

        # PK passthrough for updates
        if svc_id is not None:
            try:
                cleaned["service_apt_id"] = int(svc_id) if str(svc_id).strip() != "" else None
            except (TypeError, ValueError):
                self.add_error("service_apt_id", "Invalid service appointment id")

        # name
        name_val = (name or "").strip()
        cleaned["name"] = name_val

        # phone: digits only, at least 7
        if (phone is not None) or not self.partial:
            digits = "".join([c for c in str(phone or "") if c.isdigit()])
            if len(digits) < 7:
                self.add_error("phone", "Phone number must have at least 7 digits")
            else:
                cleaned["phone_number"] = digits

        # email: must contain '@'
        if (email is not None) or not self.partial:
            email_val = (email or "").strip()
            if not email_val or "@" not in email_val:
                self.add_error("email", "Invalid email address")
            else:
                cleaned["email"] = email_val

        # date: required for create; optional for partial update
        if (date_in is not None) or not self.partial:
            parsed_date = date_in if isinstance(date_in, dt_date) and not isinstance(date_in, datetime) else self._parse_date(date_in)
            if parsed_date is None:
                self.add_error("date", "Invalid or missing date")
            else:
                cleaned["appointment_date"] = parsed_date

        # time: optional (default to 00:00 if omitted on create to satisfy DB non-null)
        if time_in is not None:
            parsed_time = time_in if isinstance(time_in, dt_time) else self._parse_time(time_in)
            if parsed_time is None:
                self.add_error("time", "Invalid time")
            else:
                cleaned["appointment_time"] = parsed_time
        else:
            # Only for create path (no pk), ensure a value to avoid DB null errors
            if not cleaned.get("service_apt_id"):
                cleaned["appointment_time"] = dt_time(0, 0)

        # notes: optional, trim and cap length
        if notes_in is not None:
            notes_val = (str(notes_in)).strip()
            if len(notes_val) > 255:
                notes_val = notes_val[:255]
            cleaned["notes"] = notes_val
        else:
            if not cleaned.get("service_apt_id"):
                cleaned["notes"] = ""

        # Assign
        self.cleaned_data.update(cleaned)
