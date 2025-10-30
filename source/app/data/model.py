from peewee.db_model.base_model import BaseModel
from librepy.peewee.peewee import (
    Model,
    AutoField,
    ForeignKeyField,
    CharField,
    DateField,
    TimeField,
    TextField,
    BooleanField,
    IntegerField,
    DateField,
    DecimalField,
    BigIntegerField,
)


class Teacher(BaseModel):
    teacher_id = AutoField(primary_key=True)
    first_name = CharField(max_length=45)
    last_name = CharField(max_length=45)
    email = CharField()

class TrainingSession(BaseModel):
    session_id = AutoField(primary_key=True)
    session_date = DateField()
    session_time = TimeField()
    price = DecimalField(max_digits=10, decimal_places=2)
    teacher = ForeignKeyField(Teacher, backref='training_sessions')

