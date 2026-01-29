from librepy.pybrex import dialog
from librepy.pybrex.msgbox import msgbox, confirm_action
from librepy.app.components.training_session.tabs.details_tab import DetailsTab
from librepy.app.components.training_session.tabs.people_tab import PeopleTab
from librepy.app.components.training_session.tabs.attendance_tab import AttendanceTab


class TrainingSessionEntryDlg(dialog.DialogBase):
    """
    Dialog for creating/editing a Training Session.

    Now uses a multi-tab UI:
      - Details: existing form fields (moved here)
      - People: empty for now

    Behaviour (save, delete, cancel) remains unchanged.
    """

    POS_SIZE = 0, 0, 400, 300

    MARGIN = 28
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

        # Tabs
        self.details_tab = None
        self.people_tab = None
        self.attendance_tab = None

        parent_window = self.frame.window if self.frame is not None else None
        super().__init__(ctx, self.parent, parent_window, **props)

    def _create(self):
        # Create tab container area, matching StaffDialog layout
        # Use full MARGIN on sides so inner tab content can center correctly
        content_x = self.MARGIN
        content_y = self.MARGIN - 20
        content_w = self.POS_SIZE[2] - (self.MARGIN * 2)
        # Leave room for action buttons + extra margin to avoid overlap
        content_h = self.POS_SIZE[3] - (self.MARGIN * 3) - self.BUTTON_HEIGHT + 30

        tabs = self.add_page_container('Tabs', content_x, content_y, content_w, content_h)

        page_details = self.add_page(tabs, 'DetailsPage', 'Details')

        # Instantiate and build tabs
        self.details_tab = DetailsTab(self, page_details, self.ctx, self.smgr, self.logger, session_id=self.session_id)
        self.details_tab.build()

        # Only show additional tabs in edit mode
        if self.session_id is not None:
            page_people = self.add_page(tabs, 'PeoplePage', 'People')
            self.people_tab = PeopleTab(self, page_people, self.ctx, self.smgr, self.logger, session_id=self.session_id)
            self.people_tab.build()
            # Attendance tab (empty for now)
            page_attendance = self.add_page(tabs, 'AttendancePage', 'Attendance')
            self.attendance_tab = AttendanceTab(self, page_attendance, self.ctx, self.smgr, self.logger, session_id=self.session_id)
            self.attendance_tab.build()
        else:
            self.people_tab = None
            self.attendance_tab = None

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

        self.add_cancel('BtnCancel', start_x, btn_y, btn_width, self.BUTTON_HEIGHT, 
                       BackgroundColor=0x808080, TextColor=0xFFFFFF, FontWeight=150)
        self.btn_save = self.add_button('BtnSave', start_x + (btn_width + gap), btn_y, btn_width, self.BUTTON_HEIGHT, 
                                       Label='Save', DefaultButton=False,
                                       BackgroundColor=0x2E7D32, TextColor=0xFFFFFF, FontWeight=150)
        self.add_action_listener(self.btn_save, self._on_save)

    def _create_buttons_edit(self):
        btn_width = 80
        gap = 10
        count = 3
        total_w = count * btn_width + (count - 1) * gap
        dlg_w = self.POS_SIZE[2]
        start_x = (dlg_w - total_w) // 2
        btn_y = self.POS_SIZE[3] - self.MARGIN - self.BUTTON_HEIGHT

        self.btn_delete = self.add_button('BtnDelete', start_x, btn_y, btn_width, self.BUTTON_HEIGHT, 
                                         Label='Delete',
                                         BackgroundColor=0xC62828, TextColor=0xFFFFFF, FontWeight=150)
        self.add_action_listener(self.btn_delete, self._on_delete)
        self.add_cancel('BtnCancel', start_x + (btn_width + gap), btn_y, btn_width, self.BUTTON_HEIGHT,
                       BackgroundColor=0x808080, TextColor=0xFFFFFF, FontWeight=150)
        self.btn_save = self.add_button('BtnSave', start_x + 2 * (btn_width + gap), btn_y, btn_width, self.BUTTON_HEIGHT, 
                                       Label='Save', DefaultButton=False,
                                       BackgroundColor=0x2E7D32, TextColor=0xFFFFFF, FontWeight=150)
        self.add_action_listener(self.btn_save, self._on_save)

    def commit(self) -> dict:
        """Collect payload only from Details tab.
        People tab manages its own CRUD and does not contribute to session payload.
        """
        payload = {}
        if self.details_tab is not None:
            data = self.details_tab.commit()
            if isinstance(data, dict):
                payload.update(data)
        # Ensure session_id included as before
        payload.setdefault('session_id', self.session_id)
        return payload

    def refresh_attendance_tab(self):
        if self.attendance_tab is not None:
            self.attendance_tab.load_data()

    def _on_save(self, event=None):
        from librepy.app.service.srv_training_session import save_training_session
        payload = self.commit()
        result = save_training_session(payload, context=self)
        if result.get('ok'):
            # Capture the new id when creating (for callers to reopen in edit mode)
            if self.session_id is None:
                self.last_saved_id = result.get('session_id') or result.get('id')
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
        # Delegate to Details tab for data loading
        if self.details_tab is not None:
            self.details_tab.prepare()

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

