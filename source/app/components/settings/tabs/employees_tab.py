from .base_tab import BaseTab


class EmployeesTab(BaseTab):
    def __init__(self, dialog, page, ctx, smgr, logger):
        super().__init__(dialog, page, ctx, smgr, logger)

    def build(self):
        self.dialog.add_label(
            'LblEmployeesPlaceholder',
            10, 10,
            220, 14,
            page=self.page,
            Label='Employees Tab (Placeholder)',
            FontWeight=150,
        )
