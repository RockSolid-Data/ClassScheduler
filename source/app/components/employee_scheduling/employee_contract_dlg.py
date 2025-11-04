from librepy.pybrex import dialog
from librepy.pybrex.uno_date_time_converters import uno_date_to_python, uno_time_to_python, python_date_to_uno, python_time_to_uno
from librepy.pybrex.msgbox import msgbox, confirm_action


class EmployeeContractDialog(dialog.DialogBase):
    """
    Dialog for creating/editing an Employee Contract (scheduling span).

    Fields: employee_id, start_date, end_date, time_in, time_out
    Buttons: Cancel/Save (new), Delete/Cancel/Save (edit)
    """

    POS_SIZE = 0, 0, 400, 260

    MARGIN = 32
    ROW_SPACING = 10
    LABEL_HEIGHT = 14
    FIELD_HEIGHT = 22
    BUTTON_HEIGHT = 24

    def __init__(self, parent, ctx, smgr, frame, ps, **props):
        props['Title'] = props.get('Title', 'Employee Contract')
        self.contract_id = props.pop('contract_id', None)

        self.ctx = ctx
        self.parent = parent
        self.smgr = smgr
        self.frame = frame
        self.ps = ps
        self.logger = parent.logger

        self.lbl_width = None
        self.field_width = None

        parent_window = self.frame.window if self.frame is not None else None
        super().__init__(ctx, self.parent, parent_window, **props)

    def _create(self):
        x = self.MARGIN
        y = self.MARGIN // 3

        total_inner_width = self.POS_SIZE[2] - (self.MARGIN * 2)
        self.lbl_width = int(total_inner_width * 0.35)
        self.field_width = total_inner_width - self.lbl_width

        label_kwargs = dict(FontWeight=120, FontHeight=11, VerticalAlign=2)

        # employee_id (numeric)
        self.add_label('LblEmp', x, y, self.lbl_width, self.LABEL_HEIGHT, Label='Employee ID', **label_kwargs)
        self.edt_emp = self.add_edit('EdtEmp', x + self.lbl_width, y - 2, self.field_width, self.FIELD_HEIGHT)
        y += self.FIELD_HEIGHT + self.ROW_SPACING

        # start_date
        self.add_label('LblStart', x, y, self.lbl_width, self.LABEL_HEIGHT, Label='Start Date', **label_kwargs)
        self.edt_start = self.add_date('EdtStart', x + self.lbl_width, y - 2, self.field_width, self.FIELD_HEIGHT, Dropdown=True)
        y += self.FIELD_HEIGHT + self.ROW_SPACING

        # end_date
        self.add_label('LblEnd', x, y, self.lbl_width, self.LABEL_HEIGHT, Label='End Date', **label_kwargs)
        self.edt_end = self.add_date('EdtEnd', x + self.lbl_width, y - 2, self.field_width, self.FIELD_HEIGHT, Dropdown=True)
        y += self.FIELD_HEIGHT + self.ROW_SPACING

        # time_in
        self.add_label('LblIn', x, y, self.lbl_width, self.LABEL_HEIGHT, Label='Time In', **label_kwargs)
        self.edt_in = self.add_time('EdtIn', x + self.lbl_width, y - 2, self.field_width, self.FIELD_HEIGHT, Spin=True, StrictFormat=False, TimeFormat=2)
        y += self.FIELD_HEIGHT + self.ROW_SPACING

        # time_out
        self.add_label('LblOut', x, y, self.lbl_width, self.LABEL_HEIGHT, Label='Time Out', **label_kwargs)
        self.edt_out = self.add_time('EdtOut', x + self.lbl_width, y - 2, self.field_width, self.FIELD_HEIGHT, Spin=True, StrictFormat=False, TimeFormat=2)
        y += self.FIELD_HEIGHT + self.ROW_SPACING

        if self.contract_id is None:
            self._create_buttons_new()
        else:
            self._create_buttons_edit()

    def _create_buttons_new(self):
        btn_width = 80
        gap = 10
        count = 2
        total_w = count * btn_width + (count - 1) * gap
        dlg_w = self.POS_SIZE[2]
        start_x = (dlg_w - total_w) // 2
        btn_y = self.POS_SIZE[3] - self.MARGIN - self.BUTTON_HEIGHT
        self.add_cancel('BtnCancel', start_x, btn_y, btn_width, self.BUTTON_HEIGHT)
        self.btn_save = self.add_button('BtnSave', start_x + (btn_width + gap), btn_y, btn_width, self.BUTTON_HEIGHT, Label='Save', DefaultButton=False)
        self.add_action_listener(self.btn_save, self._on_save)

    def _create_buttons_edit(self):
        btn_width = 80
        gap = 10
        count = 3
        total_w = count * btn_width + (count - 1) * gap
        dlg_w = self.POS_SIZE[2]
        start_x = (dlg_w - total_w) // 2
        btn_y = self.POS_SIZE[3] - self.MARGIN - self.BUTTON_HEIGHT
        self.btn_delete = self.add_button('BtnDelete', start_x, btn_y, btn_width, self.BUTTON_HEIGHT, Label='Delete')
        self.add_action_listener(self.btn_delete, self._on_delete)
        self.add_cancel('BtnCancel', start_x + (btn_width + gap), btn_y, btn_width, self.BUTTON_HEIGHT)
        self.btn_save = self.add_button('BtnSave', start_x + 2 * (btn_width + gap), btn_y, btn_width, self.BUTTON_HEIGHT, Label='Save', DefaultButton=False)
        self.add_action_listener(self.btn_save, self._on_save)

    def commit(self):
        def _txt(ctrl):
            return ctrl.getText().strip()

        # dates
        py_start = None
        ds = self.edt_start.getDate()
        if ds and ds.Year > 0:
            py_start = uno_date_to_python(ds)
        py_end = None
        de = self.edt_end.getDate()
        if de and de.Year > 0:
            py_end = uno_date_to_python(de)

        # times (ignore 00:00:00)
        py_in = None
        tin = self.edt_in.getTime()
        if tin:
            tpi = uno_time_to_python(tin)
            if tpi and (tpi.hour != 0 or tpi.minute != 0 or tpi.second != 0):
                py_in = tpi
        py_out = None
        tout = self.edt_out.getTime()
        if tout:
            tpo = uno_time_to_python(tout)
            if tpo and (tpo.hour != 0 or tpo.minute != 0 or tpo.second != 0):
                py_out = tpo

        # employee id
        emp_id_txt = _txt(self.edt_emp)
        emp_id = int(emp_id_txt) if emp_id_txt.isdigit() else None

        data = {
            'contract_id': self.contract_id,
            'employee_id': emp_id,
            'start_date': py_start,
            'end_date': py_end,
            'time_in': py_in,
            'time_out': py_out,
        }
        return data

    def _on_save(self, event=None):
        from librepy.app.service.srv_employee_contract import save_employee_contract

        payload = self.commit()
        result = save_employee_contract(payload, context=self)
        if result.get('ok'):
            self.end_execute(1)
        else:
            errors = result.get('errors') or []
            self.logger.error(f"Failed to save employee contract: {errors}")
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
        if self.contract_id is None:
            return
        from librepy.app.service.srv_employee_contract import delete_employee_contract

        if not confirm_action("Are you sure you want to delete this contract?", Title="Confirm Delete"):
            return
        res = delete_employee_contract(self.contract_id, context=self)
        if res.get('ok'):
            self.end_execute(2)
        else:
            self.logger.error("Failed to delete employee contract")
            msgbox("Failed to delete the contract. Please try again.", "Delete Error")

    def _prepare(self):
        if self.contract_id is None:
            return
        from librepy.app.data.dao.employee_contract_dao import EmployeeContractDAO

        dao = EmployeeContractDAO(self.logger)
        rec = dao.get_by_id(self.contract_id)
        if not rec:
            self.logger.info(f"EmployeeContractDialog._prepare: no record found for id={self.contract_id}")
            return
        # Convert to dict via BaseDAO
        if not isinstance(rec, dict):
            rec = dao.to_dict(rec)
        # Populate fields
        self.edt_emp.setText(str(rec.get('employee')) if rec.get('employee') is not None else '')
        if rec.get('start_date'):
            self.edt_start.setDate(python_date_to_uno(rec['start_date']))
        if rec.get('end_date'):
            self.edt_end.setDate(python_date_to_uno(rec['end_date']))
        if rec.get('time_in'):
            self.edt_in.setTime(python_time_to_uno(rec['time_in']))
        if rec.get('time_out'):
            self.edt_out.setTime(python_time_to_uno(rec['time_out']))

    def _dispose(self):
        pass

    def _done(self, ret):
        return ret
