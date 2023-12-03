from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy import Column, ForeignKey, Integer, String
from App import Base


class ExpenseCategory(Base):
    __tablename__ = 'expense_categories'
    category_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    category_name = Column(String(50), nullable=False)
    

class ExpenseCategorySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ExpenseCategory
        include_fk = True
        load_instance = True

