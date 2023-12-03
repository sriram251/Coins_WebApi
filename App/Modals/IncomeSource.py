
from datetime import datetime
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy import DECIMAL, TIMESTAMP, Boolean, Column, ForeignKey, Integer, String
from App import Base

class IncomeSource(Base):
    __tablename__ = 'income_sources'
    source_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    source_name = Column(String(50), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    transaction_date = Column(TIMESTAMP, default=datetime.utcnow)


class IncomeSourceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = IncomeSource
        load_instance = True
        include_relationships = True
