from datetime import datetime
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema,fields
from sqlalchemy import DECIMAL, TIMESTAMP, Column, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from App import Base
from App.Modals.ExpenseCategory import ExpenseCategory, ExpenseCategorySchema


class Expense(Base):
    __tablename__ = 'expenses'
    expense_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('expense_categories.category_id'), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    description = Column(Text)
    expense_date = Column(TIMESTAMP, default=datetime.utcnow)
    category = relationship(ExpenseCategory, backref='expense', lazy=True)

class ExpenseSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Expense
        include_fk = True
        include_relationships = True
        load_instance = True
    category = fields.Nested(ExpenseCategorySchema,only=('category_name',))
   