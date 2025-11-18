from librepy.peewee.db_model.base_model import BaseModel
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
    email = CharField(null=True)

class TrainingSession(BaseModel):
    session_id = AutoField(primary_key=True)
    name = CharField(max_length=45)
    session_date = DateField()
    session_time = TimeField()
    price = DecimalField(max_digits=10, decimal_places=2)
    teacher = ForeignKeyField(Teacher, backref='training_sessions')

class SessionAttendee(BaseModel):
    attendee_id = AutoField(primary_key=True)
    session = ForeignKeyField(TrainingSession, backref='attendees')
    name = CharField(max_length=80)
    email = CharField(max_length=120, null=True)
    phone = CharField(max_length=20, null=True)
    paid = BooleanField(default=False)
    notes = TextField(null=True)
    attended = BooleanField(default=False)

    class Meta:
        # prevent duplicate sign-ups by email within the same session
        indexes = (
            (('session', 'email'), True),
        )

class ServiceAppointment(BaseModel):
    service_apt_id = AutoField(primary_key=True)
    name = CharField(max_length=45)
    phone_number = CharField(max_length=15)
    email = CharField(max_length=45)
    appointment_date = DateField()
    appointment_time = TimeField()
    notes = CharField(max_length=255)

class Employee(BaseModel):
    employee_id = AutoField(primary_key=True)
    first_name = CharField(max_length=45)
    last_name = CharField(max_length=45)
    email = CharField(max_length=45, null=True)

class EmployeeContract(BaseModel):
    contract_id = AutoField(primary_key=True)
    employee = ForeignKeyField(Employee, backref='contracts')
    start_date = DateField()
    end_date = DateField()
    time_in = TimeField()
    time_out = TimeField()
