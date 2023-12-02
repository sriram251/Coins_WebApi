from marshmallow_sqlalchemy import SQLAlchemyAutoSchema,fields
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship
from App import Base, bcrypt,ma
from App.Modals.Budget import Budget, BudgetSchema
from App.Modals.Expense import Expense, ExpenseSchema
from App.Modals.ExpenseCategory import ExpenseCategory
from App.Modals.IncomeSource import IncomeSource, IncomeSourceSchema

class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(60), nullable=False)
    admin = Column(Boolean)
    
    income_sources = relationship(IncomeSource, backref='user')
    expense_categories = relationship(ExpenseCategory, backref='user', lazy=True)
    expenses = relationship(Expense, backref='user', lazy=True)
    budgets = relationship(Budget, backref='user', lazy=True)
    
    def set_password(self, password):
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)
    


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Users
        include_fk = True
        include_relationships = True
        load_instance = True
        exclude = ('password',)
    income_sources = fields.Nested(IncomeSourceSchema,many=True)
    expenses = fields.Nested(ExpenseSchema,many=True)
    budgets = fields.Nested(BudgetSchema,many=True)
        
User_schema = UserSchema()
User_schemas = UserSchema(many=True)     