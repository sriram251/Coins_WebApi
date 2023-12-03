from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
from App import ma
from App import Base

class DocumentChunks(Base):
    __tablename__ = 'document_chunks'

    chunk_id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('documents.document_id',ondelete='CASCADE'), nullable=False)
    embedding:Vector = Column(Vector(1536), nullable=False)
    content = Column(Text, nullable=False)

   
    def __init_(self,document_id,embedding,content):
        self.document_id = document_id
        self.embedding =  embedding
        self.content = content
        
class DocumentChunksSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = DocumentChunks
        include_fk = True
        exclude = ('embedding',)


DocumentChunks_schema = DocumentChunksSchema()
DocumentChunks_schema = DocumentChunksSchema(many=True)        