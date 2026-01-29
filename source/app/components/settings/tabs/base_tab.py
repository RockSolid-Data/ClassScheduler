class BaseTab:
    """
    Minimal base class for settings dialog tabs.
    Concrete tabs should inherit from this and implement build().
    """

    def __init__(self, dialog, page, ctx, smgr, logger):
        self.dialog = dialog
        self.page = page
        self.ctx = ctx
        self.smgr = smgr
        self.logger = logger

    def build(self):
        raise NotImplementedError("Subclasses must implement build()")

    def prepare(self):
        pass

    def dispose(self):
        pass
