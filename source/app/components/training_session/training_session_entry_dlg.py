from librepy.pybrex import dialog
from librepy.pybrex.msgbox import msgbox, confirm_action
from librepy.pybrex.uno_date_time_converters import uno_date_to_python, uno_time_to_python, python_date_to_uno, python_time_to_uno


class TrainingSessionEntryDlg(dialog.DialogBase):
    """
    Dialog for creating/editing a Training Session.

    Fields:
      - Name (text)
      - Teacher (combo)
      - Session Date (date)
      - Session Time (time)
      - Price (numeric/currency)
    """

    POS_SIZE = 0, 0, 440, 330

    MARGIN = 32
    ROW_SPACING = 10
    LABEL_HEIGHT = 14
    FIELD_HEIGHT = 22
    BUTTON_HEIGHT = 24

    def __init__(self, parent, ctx, smgr, frame, ps, **props):
        props['Title'] = props.get('Title', 'Training Session')
        # Optional edit-mode id
        self.session_id = props.pop('session_id', None)

        self.ctx = ctx
        self.parent = parent
        self.smgr = smgr
        self.frame = frame
        self.ps = ps
        self.logger = parent.logger

        # Generic pairs storage for list controls (replicate Employee Contract pattern)
        self._pairs_map = {}

        self.lbl_width = None
        self.field_width = None

        parent_window = self.frame.window if self.frame is not None else None
        super().__init__(ctx, self.parent, parent_window, **props)

    def _create(self):
        x = self.MARGIN
        y = self.MARGIN // 3

        total_inner_width = self.POS_SIZE[2] - (self.MARGIN * 2)
        self.lbl_width = int(total_inner_width * 0.34)
        self.field_width = total_inner_width - self.lbl_width

        label_kwargs = dict(FontWeight=120, FontHeight=11, VerticalAlign=2)

        # Name
        self.add_label('LblName', x, y, self.lbl_width, self.LABEL_HEIGHT, Label='Name', **label_kwargs)
        self.edt_name = self.add_edit('EdtName', x + self.lbl_width, y - 2, self.field_width, self.FIELD_HEIGHT)
        y += self.FIELD_HEIGHT + self.ROW_SPACING

        # Teacher (list) - replicate Employee Contract dialog pattern
        self.add_label('LblTeacher', x, y, self.lbl_width, self.LABEL_HEIGHT, Label='Teacher', **label_kwargs)
        self.lst_teacher = self.add_list('LstTeacher', x + self.lbl_width, y - 2, self.field_width, self.FIELD_HEIGHT, MultiSelection=False, Dropdown=True)
        y += self.FIELD_HEIGHT + self.ROW_SPACING

        # Session Date
        self.add_label('LblDate', x, y, self.lbl_width, self.LABEL_HEIGHT, Label='Session Date', **label_kwargs)
        self.edt_date = self.add_date('EdtDate', x + self.lbl_width, y - 2, self.field_width, self.FIELD_HEIGHT, Dropdown=True)
        y += self.FIELD_HEIGHT + self.ROW_SPACING

        # Session Time
        self.add_label('LblTime', x, y, self.lbl_width, self.LABEL_HEIGHT, Label='Session Time', **label_kwargs)
        self.edt_time = self.add_time('EdtTime', x + self.lbl_width, y - 2, self.field_width, self.FIELD_HEIGHT, Spin=True, StrictFormat=False, TimeFormat=2)
        y += self.FIELD_HEIGHT + self.ROW_SPACING

        # Price
        self.add_label('LblPrice', x, y, self.lbl_width, self.LABEL_HEIGHT, Label='Price', **label_kwargs)
        self.edt_price = self.add_numeric('EdtPrice', x + self.lbl_width, y - 2, self.field_width, self.FIELD_HEIGHT)
        y += self.FIELD_HEIGHT + self.ROW_SPACING


        # Buttons depending on mode
        if self.session_id is None:
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

    # ---------- Generic list helpers (replicate Employee Contract dialog) ----------
    def set_list_items(self, list_ctrl, labels):
        count = list_ctrl.getItemCount()
        if count:
            list_ctrl.removeItems(0, count)
        if labels:
            list_ctrl.addItems(tuple(labels), 0)

    def set_combo_pairs(self, list_ctrl, pairs, store_attr):
        self._pairs_map[store_attr] = list(pairs or [])
        labels = [lbl for _id, lbl in (pairs or [])]
        self.set_list_items(list_ctrl, labels)

    def get_selected_index(self, list_ctrl):
        return list_ctrl.getSelectedItemPos()

    def get_selected_id(self, list_ctrl, store_attr):
        idx = self.get_selected_index(list_ctrl)
        pairs = self._pairs_map.get(store_attr, [])
        if isinstance(idx, int) and 0 <= idx < len(pairs):
            return pairs[idx][0]
        return None

    def select_by_id(self, list_ctrl, store_attr, wanted_id):
        if wanted_id is None:
            return False
        pairs = self._pairs_map.get(store_attr, [])
        for i, (pid, _lbl) in enumerate(pairs):
            if pid == wanted_id:
                list_ctrl.selectItemPos(i, True)
                return True
        return False

    def commit(self) -> dict:
        name = self.edt_name.getText().strip()
        teacher_id = self.get_selected_id(self.lst_teacher, '_teacher_items')

        # Date
        py_date = None
        udate = self.edt_date.getDate()
        if udate and udate.Year > 0:
            py_date = uno_date_to_python(udate)

        # Time
        py_time = None
        utime = self.edt_time.getTime()
        if utime:
            pt = uno_time_to_python(utime)
            if pt and (pt.hour != 0 or pt.minute != 0 or pt.second != 0):
                py_time = pt

        # Price
        price_val = float(self.edt_price.getValue())

        return {
            'session_id': self.session_id,
            'name': name,
            'teacher': teacher_id,
            'session_date': py_date,
            'session_time': py_time,
            'price': price_val,
        }

    def _on_save(self, event=None):
        from librepy.app.service.srv_training_session import save_training_session
        payload = self.commit()
        result = save_training_session(payload, context=self)
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

    def _prepare(self):
        # Populate teachers list via service (pairs)
        from librepy.app.service.srv_training_session import load_teacher_pairs
        pairs = load_teacher_pairs(self.logger)
        self.set_combo_pairs(self.lst_teacher, pairs, store_attr='_teacher_items')

        if self.session_id is None:
            return

        from librepy.app.data.dao.training_session_dao import TrainingSessionDAO
        dao = TrainingSessionDAO(self.logger)
        rec = dao.get_by_id(self.session_id)
        if not rec:
            self.logger.info(f"TrainingSessionEntryDlg._prepare: no record found for id={self.session_id}")
            return
        if not isinstance(rec, dict):
            rec = dao.to_dict(rec)
        # Populate fields
        self.edt_name.setText((rec.get('name') or '').strip())

        # Preselect teacher by id
        teacher_id = None
        teacher_ref = rec.get('teacher')
        if teacher_ref is not None:
            teacher_id = teacher_ref if isinstance(teacher_ref, int) else getattr(teacher_ref, 'teacher_id', None)
        if teacher_id is not None:
            self.select_by_id(self.lst_teacher, '_teacher_items', teacher_id)

        if rec.get('session_date'):
            self.edt_date.setDate(python_date_to_uno(rec['session_date']))
        if rec.get('session_time'):
            self.edt_time.setTime(python_time_to_uno(rec['session_time']))
        if rec.get('price') is not None:
            self.edt_price.setValue(float(rec['price']))

    def _on_delete(self, event=None):
        if self.session_id is None:
            return
        from librepy.app.service.srv_training_session import delete_training_session
        if not confirm_action("Are you sure you want to delete this training session?", Title="Confirm Delete"):
            return
        res = delete_training_session(self.session_id, context=self)
        if res.get('ok'):
            self.end_execute(2)
        else:
            self.logger.error("Failed to delete training session")
            msgbox("Failed to delete the training session. Please try again.", "Delete Error")

    def _dispose(self):
        pass

    def _done(self, ret):
        return ret
