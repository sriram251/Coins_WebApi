from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from App import Base



class DocumentTag(Base):
    __tablename__ = 'document_tags'

    tag_id = Column(Integer, primary_key=True, autoincrement=True)
    tag_name = Column(String(50), unique=True, nullable=False)

    # Add a relationship to the DocumentChunks model
    