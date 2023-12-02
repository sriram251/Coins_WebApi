from sqlalchemy import Column, Integer, ForeignKey, Text, LargeBinary
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DocumentTagging(Base):
    __tablename__ = 'document_tagging'

    document_id = Column(Integer, ForeignKey('documents.document_id'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('document_tags.tag_id'), primary_key=True)
    
    
    documents = relationship('Document', secondary='document_tagging', back_populates='tags')
    