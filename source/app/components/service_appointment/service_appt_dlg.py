from librepy.pybrex import dialog
from librepy.pybrex.uno_date_time_converters import uno_date_to_python, uno_time_to_python, python_date_to_uno, python_time_to_uno
from librepy.app.utils.utils import format_phone_for_display
from librepy.pybrex.msgbox import msgbox, confirm_action


class ServiceAppointmentDialog(dialog.DialogBase):
    """
    Minimal dialog container for creating/editing a Service Appointment.

    Requirements (no functionality yet):
    - Fields with labels: name, phone #, email, date, time, notes
    - Buttons: Cancel (left), Save (right)
    - All labels the same width
    - All fields the same width
    """

    # x, y, width, height
    POS_SIZE = 0, 0, 380, 300

    # Layout constants
    MARGIN = 24
    ROW_SPACING = 8
    LABEL_HEIGHT = 14
    FIELD_HEIGHT = 22
    BUTTON_HEIGHT = 26
    
    # Colors
    SAVE_BUTTON_COLOR = 0x2E7D32  # Green
    DELETE_BUTTON_COLOR = 0xC62828  # Red
    CANCEL_BUTTON_COLOR = 0x757575  # Gray

    def __init__(self, parent, ctx, smgr, frame, ps, **props):
        # Basic dialog appearance
        props['Title'] = props.get('Title', 'Service Appointment')

        # Optional edit-mode id
        self.service_apt_id = props.pop('service_apt_id', None)

        self.ctx = ctx
        self.parent = parent
        self.smgr = smgr
        self.frame = frame
        self.ps = ps
        self.logger = parent.logger

        # Controls (optional references)
        self.lbl_width = None
        self.field_width = None

        # Pass the parent window (frame.window) to DialogBase for ownership/centering when available
        parent_window = self.frame.window if self.frame is not None else None
        super().__init__(ctx, self.parent, parent_window, **props)

    def _create(self):
        """Create the static UI controls with equal label/field widths."""
        x = self.MARGIN
        y = self.MARGIN // 2

        # Compute equal widths for labels and fields
        total_inner_width = self.POS_SIZE[2] - (self.MARGIN * 2)
        # 30% labels, 70% fields (rounded to integers)
        self.lbl_width = int(total_inner_width * 0.30)
        self.field_width = total_inner_width - self.lbl_width

        label_kwargs = dict(FontWeight=120, FontHeight=12, VerticalAlign=2)

        # name
        self.add_label('LblName', x, y, self.lbl_width, self.LABEL_HEIGHT, Label='Name', **label_kwargs)
        self.edt_name = self.add_edit('EdtName', x + self.lbl_width, y - 2, self.field_width, self.FIELD_HEIGHT)
        y += self.FIELD_HEIGHT + self.ROW_SPACING

        # phone #
        self.add_label('LblPhone', x, y, self.lbl_width, self.LABEL_HEIGHT, Label='Phone #', **label_kwargs)
        self.edt_phone = self.add_edit('EdtPhone', x + self.lbl_width, y - 2, self.field_width, self.FIELD_HEIGHT)
        y += self.FIELD_HEIGHT + self.ROW_SPACING

        # email
        self.add_label('LblEmail', x, y, self.lbl_width, self.LABEL_HEIGHT, Label='Email', **label_kwargs)
        self.edt_email = self.add_edit('EdtEmail', x + self.lbl_width, y - 2, self.field_width, self.FIELD_HEIGHT)
        y += self.FIELD_HEIGHT + self.ROW_SPACING

        # date
        self.add_label('LblDate', x, y, self.lbl_width, self.LABEL_HEIGHT, Label='Date', **label_kwargs)
        self.edt_date = self.add_date('EdtDate', x + self.lbl_width, y - 2, self.field_width, self.FIELD_HEIGHT, Dropdown=True)
        y += self.FIELD_HEIGHT + self.ROW_SPACING

        # time (picker)
        self.add_label('LblTime', x, y, self.lbl_width, self.LABEL_HEIGHT, Label='Time', **label_kwargs)
        self.edt_time = self.add_time('EdtTime', x + self.lbl_width, y - 2, self.field_width, self.FIELD_HEIGHT, Spin=True, StrictFormat=False, TimeFormat=2)
        y += self.FIELD_HEIGHT + self.ROW_SPACING

        # notes (multi-line)
        notes_height = 50
        self.add_label('LblNotes', x, y, self.lbl_width, self.LABEL_HEIGHT, Label='Notes', **label_kwargs)
        self.edt_notes = self.add_edit('EdtNotes', x + self.lbl_width, y - 2, self.field_width, notes_height, MultiLine=True)
        y += notes_height + self.ROW_SPACING

        # Buttons: choose layout based on mode (create vs edit)
        if self.service_apt_id is None:
            self._create_buttons_normal()
        else:
            self._create_buttons_edit()

    # ---------- Buttons (centered group) ----------
    def _create_buttons_normal(self):
        """Create Cancel and Save buttons centered as a group."""
        btn_width = 90
        gap = 12
        count = 2
        total_w = count * btn_width + (count - 1) * gap
        dlg_w = self.POS_SIZE[2]
        start_x = (dlg_w - total_w) // 2
        btn_y = self.POS_SIZE[3] - self.MARGIN - self.BUTTON_HEIGHT

        # Cancel (left)
        self.btn_cancel = self.add_button(
            'BtnCancel', start_x, btn_y, btn_width, self.BUTTON_HEIGHT,
            Label='Cancel',
            BackgroundColor=self.CANCEL_BUTTON_COLOR,
            TextColor=0xFFFFFF
        )
        self.add_action_listener(self.btn_cancel, lambda e: self.end_execute(0))
        
        # Save (right)
        self.btn_save = self.add_button(
            'BtnSave', start_x + (btn_width + gap), btn_y, btn_width, self.BUTTON_HEIGHT,
            Label='Save',
            DefaultButton=False,
            BackgroundColor=self.SAVE_BUTTON_COLOR,
            TextColor=0xFFFFFF,
            FontWeight=150
        )
        self.add_action_listener(self.btn_save, self._on_save)

    def _create_buttons_edit(self):
        """Create Delete, Cancel, Save buttons centered as a group."""
        btn_width = 80
        gap = 10
        count = 3
        total_w = count * btn_width + (count - 1) * gap
        dlg_w = self.POS_SIZE[2]
        start_x = (dlg_w - total_w) // 2
        btn_y = self.POS_SIZE[3] - self.MARGIN - self.BUTTON_HEIGHT

        # Delete (far left)
        self.btn_delete = self.add_button(
            'BtnDelete', start_x, btn_y, btn_width, self.BUTTON_HEIGHT,
            Label='Delete',
            BackgroundColor=self.DELETE_BUTTON_COLOR,
            TextColor=0xFFFFFF
        )
        self.add_action_listener(self.btn_delete, self._on_delete)
        
        # Cancel (middle)
        self.btn_cancel = self.add_button(
            'BtnCancel', start_x + (btn_width + gap), btn_y, btn_width, self.BUTTON_HEIGHT,
            Label='Cancel',
            BackgroundColor=self.CANCEL_BUTTON_COLOR,
            TextColor=0xFFFFFF
        )
        self.add_action_listener(self.btn_cancel, lambda e: self.end_execute(0))
        
        # Save (right)
        self.btn_save = self.add_button(
            'BtnSave', start_x + 2 * (btn_width + gap), btn_y, btn_width, self.BUTTON_HEIGHT,
            Label='Save',
            DefaultButton=False,
            BackgroundColor=self.SAVE_BUTTON_COLOR,
            TextColor=0xFFFFFF,
            FontWeight=150
        )
        self.add_action_listener(self.btn_save, self._on_save)

    def commit(self):
        """Collect all field values into a dictionary using UNO date/time getters and log it.
        Returns the dictionary. This does not perform any persistence.
        """
        def _txt(ctrl):
            return ctrl.getText().strip()

        # Date via UNO getDate -> python date
        py_date = None
        udate = self.edt_date.getDate()
        if udate and udate.Year > 0:
            py_date = uno_date_to_python(udate)

        # Time via UNO getTime -> python time, ignore 00:00:00
        py_time = None
        utime = self.edt_time.getTime()
        if utime:
            pt = uno_time_to_python(utime)
            if pt and (pt.hour != 0 or pt.minute != 0 or pt.second != 0):
                py_time = pt

        data = {
            'name': _txt(self.edt_name),
            'phone': _txt(self.edt_phone),
            'email': _txt(self.edt_email),
            'date': py_date,
            'time': py_time,
            'notes': _txt(self.edt_notes)
        }
        data['service_apt_id'] = self.service_apt_id
        return data

    def _on_save(self, event=None):
        """Action listener for Save button: gather inputs and persist via service layer."""
        from librepy.app.service.srv_appointment import save_service_appointment

        raw = self.commit()  # {'name','phone','email','date','time','notes'}
        payload = {
            'service_apt_id': raw.get('service_apt_id'),  # may be None when creating
            'name': raw.get('name'),
            'phone': raw.get('phone'),
            'email': raw.get('email'),
            'date': raw.get('date'),
            'time': raw.get('time'),
            'notes': raw.get('notes'),
        }
        result = save_service_appointment(payload, context=self)
        if result.get('ok'):
            self.end_execute(1)
        else:
            errors = result.get('errors') or []
            self.logger.error(f"Failed to save service appointment: {errors}")
            if isinstance(errors, list) and errors:
                lines = []
                for e in errors:
                    fld = e.get('field') if isinstance(e, dict) else None
                    msg = e.get('message') if isinstance(e, dict) else str(e)
                    if fld and fld != '__all__':
                        lines.append(f"{fld}: {msg}")
                    else:
                        lines.append(str(msg))
                body = "\n".join(lines)
            else:
                body = "Invalid input. Please correct the highlighted fields."
            msgbox(body, "Validation Error")

    def _on_delete(self, event=None):
        """Confirm deletion and delete the current service appointment."""
        if self.service_apt_id is None:
            return
        from librepy.app.service.srv_appointment import delete_service_appointment

        if not confirm_action("Are you sure you want to delete this appointment?", Title="Confirm Delete"):
            return
        res = delete_service_appointment(self.service_apt_id, context=self)
        if res.get('ok'):
            # Distinct return code for delete
            self.end_execute(2)
        else:
            self.logger.error("Failed to delete service appointment")
            msgbox("Failed to delete the appointment. Please try again.", "Delete Error")

    def _prepare(self):
        if self.service_apt_id is None:
            return

        from librepy.app.data.dao.service_appointment_dao import ServiceAppointmentDAO

        dao = ServiceAppointmentDAO(self.logger)
        rec = dao.get_by_id(self.service_apt_id)
        if not rec:
            self.logger.info(f"ServiceAppointmentDialog._prepare: no record found for id={self.service_apt_id}")
            return
        # Convert model instance to dict when needed
        if not isinstance(rec, dict):
            rec = dao.to_dict(rec)
        # Populate text fields
        self.edt_name.setText(rec['name'] or '')
        self.edt_phone.setText(format_phone_for_display(rec['phone_number']))
        self.edt_email.setText(rec['email'] or '')
        self.edt_notes.setText(rec.get('notes') or '')
        if rec.get('appointment_date'):
            self.edt_date.setDate(python_date_to_uno(rec['appointment_date']))
        if rec.get('appointment_time'):
            self.edt_time.setTime(python_time_to_uno(rec['appointment_time']))

    def _dispose(self):
        pass

    def _done(self, ret):
        # No custom behavior yet; just return the result code
        return ret
