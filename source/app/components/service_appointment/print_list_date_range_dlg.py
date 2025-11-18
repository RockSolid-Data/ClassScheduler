from librepy.pybrex import dialog
from librepy.pybrex.uno_date_time_converters import uno_date_to_python


class PrintListDateRangeDialog(dialog.DialogBase):
    """
    Simple dialog for selecting a start and end date for printing a list.

    Requirements:
    - Two date fields: Start Date and End Date
    - Cancel and Continue buttons
    - On Continue, store selected_start_date and selected_end_date and close with ret=1
    - On Cancel, close with ret=0
    """

    POS_SIZE = 0, 0, 360, 160  # x, y, w, h

    def __init__(self, parent, ctx, smgr, frame, ps, **props):
        props['Title'] = props.get('Title', 'Print List')
        self.parent = parent
        self.ctx = ctx
        self.smgr = smgr
        self.frame = frame
        self.ps = ps
        self.logger = getattr(parent, 'logger', None)

        # Output values
        self.selected_start_date = None
        self.selected_end_date = None

        parent_window = self.frame.window if self.frame is not None else None
        super().__init__(ctx, self.parent, parent_window, **props)

    def _create(self):
        margin = 18
        label_h = 14
        field_h = 22
        row_gap = 12

        total_inner_w = self.POS_SIZE[2] - (margin * 2)
        lbl_w = int(total_inner_w * 0.35)
        fld_w = total_inner_w - lbl_w

        x = margin
        y = margin

        # Start date
        self.add_label('LblStart', x, y, lbl_w, label_h, Label='Start date', FontWeight=120, FontHeight=10)
        self._date_start = self.add_date('DateStart', x + lbl_w, y - 2, fld_w, field_h, Dropdown=True)
        y += field_h + row_gap

        # End date
        self.add_label('LblEnd', x, y, lbl_w, label_h, Label='End date', FontWeight=120, FontHeight=10)
        self._date_end = self.add_date('DateEnd', x + lbl_w, y - 2, fld_w, field_h, Dropdown=True)

        # Buttons (centered): Cancel and Continue
        btn_w = 90
        btn_h = 24
        gap = 10
        count = 2
        total_w = count * btn_w + (count - 1) * gap
        start_x = (self.POS_SIZE[2] - total_w) // 2
        btn_y = self.POS_SIZE[3] - margin - btn_h

        self.add_button('BtnCancel', start_x, btn_y, btn_w, btn_h, Label='Cancel', callback=self._on_cancel)
        self.add_button('BtnContinue', start_x + btn_w + gap, btn_y, btn_w, btn_h, Label='Continue', callback=self._on_submit)

    # Reference methods from provided snippet (adapted; no checkbox logic)
    def _prepare(self):
        pass

    def _dispose(self):
        pass

    def _on_submit(self, _evt=None):
        try:
            # Read UNO date ints and convert to python dates if provided
            start_uno = self._date_start.Model.Date
            end_uno = self._date_end.Model.Date
            self.selected_start_date = uno_date_to_python(start_uno) if start_uno else None
            self.selected_end_date = uno_date_to_python(end_uno) if end_uno else None
            self.end_execute(1)
        except Exception:
            if self.logger:
                import traceback as _tb
                self.logger.error('Error on Submit in PrintListDateRangeDialog')
                self.logger.error(_tb.format_exc())
            self.end_execute(0)

    def _on_cancel(self, _evt=None):
        self.selected_start_date = None
        self.selected_end_date = None
        self.end_execute(0)
