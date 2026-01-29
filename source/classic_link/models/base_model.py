from librepy.peewee.db_model.base_model import BaseModel

class ClassicAccountingBase(BaseModel):
    """
    Base model for Classic Accounting database tables.
    
    All Classic Accounting models inherit from this class to connect
    to the Classic Accounting database using the application's database
    connection. All tables are in the 'public' schema.
    """
    class Meta:
        schema = 'public'