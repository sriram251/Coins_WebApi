from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, Text, DECIMAL, Date, TIMESTAMP, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, fields
from pgvector.sqlalchemy import Vector
Base = declarative_base()

class InsuranceCategory(Base):
    __tablename__ = 'insurance_categories'
    category_id = Column(Integer, primary_key=True)
    category_name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP", nullable=False)

class SchemeVector(Base):
    __tablename__ = 'scheme_vectors'
    vector_id = Column(Integer, primary_key=True)
    scheme_id = Column(Integer, ForeignKey('insurance_schemes.scheme_id', ondelete='CASCADE'), nullable=False)
    vector_data:Vector = Column(Vector(1536), nullable=False)  # Assuming a string field for vector data
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP", nullable=False)

class InsuranceScheme(Base):
    __tablename__ = 'insurance_schemes'
    scheme_id = Column(Integer, primary_key=True)
    scheme_name = Column(String(255), nullable=False)
    description = Column(Text)
    description_vector_data:Vector = Column(Vector(1536), nullable=True)  # Assuming a string field for vector data
    coverage_amount = Column(Integer)
    premium_amount = Column(DECIMAL(10, 2))
    start_date = Column(Date)
    end_date = Column(Date)
    isencoded = Column(Boolean, nullable=False)
    document_path = Column(String(255), nullable=False)
    category_id = Column(Integer, ForeignKey('insurance_categories.category_id'), nullable=False)
    created_at = Column(TIMESTAMP, server_default="CURRENT_TIMESTAMP", nullable=False)
    category = relationship(InsuranceCategory, backref='insurance_schemes', lazy=True)
   
    vectors = relationship(SchemeVector, backref='insurance_scheme', lazy='dynamic')
    def __init__(self, scheme_name, description, coverage_amount,description_vector_data, premium_amount, start_date, end_date, category_id,document_path):
        self.scheme_name = scheme_name
        self.description = description
        self.coverage_amount = coverage_amount
        self.premium_amount = premium_amount
        self.start_date = start_date
        self.end_date = end_date
        self.description_vector_data = description_vector_data
        self.category_id = category_id
        self.document_path = document_path
        self.created_at = datetime.now()
        self.isencoded = False

class InsuranceCategorySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = InsuranceCategory
        include_fk = True
        load_instance = True


class SchemeVectorSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = SchemeVector
        include_fk = True
        load_instance = True
        exclude = ('vector_data',)

class InsuranceSchemeSchema(SQLAlchemyAutoSchema):
    category = fields.Nested(InsuranceCategorySchema, only=('category_name',))
    
    class Meta:
        model = InsuranceScheme
        include_fk = True
        exclude = ('description_vector_data','vectors')
        include_relationships = True
        load_instance = True
       