from typing import Any, Dict, Optional

from librepy.app.forms.base_form import BaseForm
from librepy.app.data.dao.teacher_dao import TeacherDAO


class TeacherForm(BaseForm):
    class Meta(BaseForm.Meta):
        dao = None
        dao_factory = staticmethod(lambda context: TeacherDAO(getattr(context, "logger", context)))
        create_fn = "create"
        update_fn = "update"
        pk_field = "teacher_id"

    def clean(self) -> None:
        teacher_id = self.get("teacher_id")
        first_name_in = self.require("first_name")
        last_name_in = self.require("last_name")
        email_in = self.get("email")

        cleaned: Dict[str, Any] = {}

        # PK passthrough for updates
        if teacher_id is not None:
            try:
                cleaned["teacher_id"] = int(teacher_id) if str(teacher_id).strip() != "" else None
            except (TypeError, ValueError):
                self.add_error("teacher_id", "Invalid teacher id")

        # first_name
        if (first_name_in is not None) or not self.partial:
            fn = (str(first_name_in or "")).strip()
            if len(fn) > 45:
                self.add_error("first_name", "First name cannot exceed 45 characters")
            else:
                cleaned["first_name"] = fn

        # last_name
        if (last_name_in is not None) or not self.partial:
            ln = (str(last_name_in or "")).strip()
            if len(ln) > 45:
                self.add_error("last_name", "Last name cannot exceed 45 characters")
            else:
                cleaned["last_name"] = ln

        em_raw = email_in
        em = None if em_raw is None else str(em_raw).strip()
        if em is None or em == "":
            cleaned["email"] = None
        else:
            if "@" not in em:
                self.add_error("email", "Invalid email address")
            else:
                cleaned["email"] = em

        # Assign
        self.cleaned_data.update(cleaned)
