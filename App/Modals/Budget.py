
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema,fields
from sqlalchemy import DECIMAL, Column, ForeignKey, Integer
from App import Base
from App.Modals.ExpenseCategory import ExpenseCategory, ExpenseCategorySchema
from sqlalchemy.orm import relationship

class Budget(Base):
    __tablename__ = 'budgets'
    budget_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('expense_categories.category_id'), nullable=False)
    budget_amount = Column(DECIMAL(10, 2), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    category = relationship(ExpenseCategory, backref='budget', lazy=True)
class BudgetSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Budget
        include_fk = True
        include_relationships = True
        load_instance = True
    category = fields.Nested(ExpenseCategorySchema,only=('category_name',))