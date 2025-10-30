from librepy.app.data.base_dao import BaseDAO
from librepy.app.data.model import TrainingSession

class TrainingSessionDAO(BaseDAO):

    def __init__(self, logger):
        super().__init__(TrainingSession, logger)