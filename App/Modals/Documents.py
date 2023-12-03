
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from App import Base,ma




class Document(Base):
    __tablename__ = 'documents'

    document_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    description = Column(Text)
    upload_date = Column(TIMESTAMP, server_default='now()', nullable=False)
    file_path = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_encoded = Column(Boolean, nullable=False)



class DocumentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Document
        include_fk = True
Document_schema = DocumentSchema()
Document_schema = DocumentSchema(many=True)       