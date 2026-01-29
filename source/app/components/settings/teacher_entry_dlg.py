from librepy.pybrex import dialog
from librepy.pybrex.msgbox import msgbox, confirm_action


class TeacherEntryDialog(dialog.DialogBase):
    """
    Dialog for creating/editing a Teacher entry.
    Follows the layout and workflow pattern from ServiceAppointmentDialog.
    """

    # x, y, width, height
    POS_SIZE = 0, 0, 280, 165      

    # Layout constants
    MARGIN = 32
    ROW_SPACING = 10
    LABEL_HEIGHT = 14   
    FIELD_HEIGHT = 22
    BUTTON_HEIGHT = 24

    def __init__(self, ctx, parent, logger, **props):
        props['Title'] = props.get('Title', 'Teacher Entry')
        # Optional edit-mode id
        self.teacher_id = props.pop('teacher_id', None)

        self.ctx = ctx
        self.parent = parent
        self.logger = logger

        # Controls (optional references)
        self.lbl_width = None
        self.field_width = None

        super().__init__(ctx, self.parent, **props)

    def _create(self):
        x = self.MARGIN
        y = self.MARGIN // 3

        total_inner_width = self.POS_SIZE[2] - (self.MARGIN * 2)
        self.lbl_width = int(total_inner_width * 0.30)
        self.field_width = total_inner_width - self.lbl_width

        label_kwargs = dict(FontWeight=120, FontHeight=11, VerticalAlign=2)

        # First Name
        self.add_label('LblFirstName', x, y, self.lbl_width, self.LABEL_HEIGHT, Label='First Name', **label_kwargs)
        self.edt_first = self.add_edit('EdtFirstName', x + self.lbl_width, y - 2, self.field_width, self.FIELD_HEIGHT)
        y += self.FIELD_HEIGHT + self.ROW_SPACING

        # Last Name
        self.add_label('LblLastName', x, y, self.lbl_width, self.LABEL_HEIGHT, Label='Last Name', **label_kwargs)
        self.edt_last = self.add_edit('EdtLastName', x + self.lbl_width, y - 2, self.field_width, self.FIELD_HEIGHT)
        y += self.FIELD_HEIGHT + self.ROW_SPACING

        # Email
        self.add_label('LblEmail', x, y, self.lbl_width, self.LABEL_HEIGHT, Label='Email', **label_kwargs)
        self.edt_email = self.add_edit('EdtEmail', x + self.lbl_width, y - 2, self.field_width, self.FIELD_HEIGHT)
        y += self.FIELD_HEIGHT + self.ROW_SPACING

        # Buttons based on mode
        if self.teacher_id is None:
            self._create_buttons_normal()
        else:
            self._create_buttons_edit()

    def _create_buttons_normal(self):
        btn_width = 80
        gap = 10
        count = 2
        total_w = count * btn_width + (count - 1) * gap
        dlg_w = self.POS_SIZE[2]
        start_x = (dlg_w - total_w) // 2
        btn_y = self.POS_SIZE[3] - self.MARGIN - self.BUTTON_HEIGHT

        # Cancel button - neutral gray
        self.add_cancel('BtnCancel', start_x, btn_y, btn_width, self.BUTTON_HEIGHT,
                       BackgroundColor=0x808080, TextColor=0xFFFFFF)
        
        # Save button - green
        self.btn_save = self.add_button('BtnSave', start_x + (btn_width + gap), btn_y, btn_width, self.BUTTON_HEIGHT, 
                                        Label='Save', DefaultButton=False,
                                        BackgroundColor=0x28A745, TextColor=0xFFFFFF)
        self.add_action_listener(self.btn_save, self._on_save)

    def _create_buttons_edit(self):
        btn_width = 80
        gap = 10
        count = 3
        total_w = count * btn_width + (count - 1) * gap
        dlg_w = self.POS_SIZE[2]
        start_x = (dlg_w - total_w) // 2
        btn_y = self.POS_SIZE[3] - self.MARGIN - self.BUTTON_HEIGHT

        # Delete button - red
        self.btn_delete = self.add_button('BtnDelete', start_x, btn_y, btn_width, self.BUTTON_HEIGHT, 
                                          Label='Delete',
                                          BackgroundColor=0xDC3545, TextColor=0xFFFFFF)
        self.add_action_listener(self.btn_delete, self._on_delete)
        
        # Cancel button - neutral gray
        self.add_cancel('BtnCancel', start_x + (btn_width + gap), btn_y, btn_width, self.BUTTON_HEIGHT,
                       BackgroundColor=0x808080, TextColor=0xFFFFFF)
        
        # Save button - green
        self.btn_save = self.add_button('BtnSave', start_x + 2 * (btn_width + gap), btn_y, btn_width, self.BUTTON_HEIGHT, 
                                        Label='Save', DefaultButton=False,
                                        BackgroundColor=0x28A745, TextColor=0xFFFFFF)
        self.add_action_listener(self.btn_save, self._on_save)

    def commit(self) -> dict:
        # Gather text inputs
        def _txt(ctrl):
            try:
                return ctrl.getText().strip()
            except Exception:
                return ''
        data = {
            'teacher_id': self.teacher_id,
            'first_name': _txt(self.edt_first),
            'last_name': _txt(self.edt_last),
            'email': _txt(self.edt_email),
        }
        return data

    def _on_save(self, event=None):
        from librepy.app.service.srv_teacher import save_teacher
        payload = self.commit()
        result = save_teacher(payload, context=self)
        if result.get('ok'):
            self.end_execute(1)
        else:
            errors = result.get('errors') or []
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
        if self.teacher_id is None:
            return
        from librepy.app.service.srv_teacher import delete_teacher
        if not confirm_action("Are you sure you want to delete this teacher?", Title="Confirm Delete"):
            return
        res = delete_teacher(self.teacher_id, context=self)
        if res.get('ok'):
            self.end_execute(2)
        else:
            self.logger.error("Failed to delete teacher")
            msgbox("Failed to delete the teacher. Please try again.", "Delete Error")

    def _prepare(self):
        # If editing, load and populate fields
        if self.teacher_id is None:
            return
        from librepy.app.data.dao.teacher_dao import TeacherDAO
        dao = TeacherDAO(self.logger)
        rec = dao.get_by_id(self.teacher_id)
        if not rec:
            self.logger.info(f"TeacherEntryDialog._prepare: no record found for id={self.teacher_id}")
            return
        # Convert model instance to dict when needed
        if not isinstance(rec, dict):
            rec = dao.to_dict(rec)
        self.edt_first.setText((rec.get('first_name') or '').strip())
        self.edt_last.setText((rec.get('last_name') or '').strip())
        self.edt_email.setText((rec.get('email') or '').strip())

    def _dispose(self):
        pass

    def _done(self, ret):
        return ret
