class UsersDTO:
    def __init__(self, username, email, documents=None):
        self.username = username
        self.email = email
        self.documents = documents or []  # List of DocumentDTO


class DocumentDTO:
    def __init__(self, title, description, upload_date, file_path, user_id, is_encoded, tags=None, chunks=None):
        self.title = title
        self.description = description
        self.upload_date = upload_date
        self.file_path = file_path
        self.user_id = user_id
        self.is_encoded = is_encoded
        self.tags = tags or []  # List of DocumentTagDTO
        self.chunks = chunks or []  # List of DocumentChunkDTO


class DocumentTagDTO:
    def __init__(self, document_id, tag_id):
        self.document_id = document_id
        self.tag_id = tag_id


class DocumentChunkDTO:
    def __init__(self, chunk_id, document_id, embedding, content):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.embedding = embedding
        self.content = content