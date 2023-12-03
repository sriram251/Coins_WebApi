import io
from langchain.embeddings import AzureOpenAIEmbeddings
from App import container_client
import fitz
import nltk
from  langchain.embeddings import AzureOpenAIEmbeddings
nltk.download('punkt')
from App.Modals.DocumentChunks import DocumentChunks
def Embed_document(path,Document_id)->list[DocumentChunks]:
    try:
        modal = AzureOpenAIEmbeddings(
                azure_deployment="text-embedding-ada-002",
                openai_api_version="2023-05-15",
            )
        chunk_size = 16
        Document = read_pdf(path)
        docs = nltk.sent_tokenize(Document)
        num_chunks = len(docs) // chunk_size + (1 if len(docs) % chunk_size != 0 else 0)
        embeddings = []
        for chunk_index in range(num_chunks):
                # Calculate the start and end indices for the current chunk
                start_index = chunk_index * chunk_size
                end_index = (chunk_index + 1) * chunk_size

                # Extract the current chunk of items
                current_chunk = docs[start_index:end_index]
                embeddingschunk = modal.embed_documents(current_chunk)
                embeddings.extend(embeddingschunk)
        #docs = text_splitter.split_text([Document])
        #doc_strings = documents_to_strings(docs)
        
        paramerters = [DocumentChunks(document_id = Document_id,embedding =value ,content = docs[index]) for index,value in enumerate(embeddings)]
        return paramerters
    except Exception as e:
        raise e
        print(f"Error  {str(e)}")
    finally:
        pass
    
def Embeded_Text(query:str):
    try:
        embeddings = AzureOpenAIEmbeddings(
                azure_deployment="text-embedding-ada-002",
                openai_api_version="2023-05-15",
            )
        embeddings = embeddings.embed_query(query)
        return embeddings
    except Exception as e:
        raise e
        print(f"Error  {str(e)}")
    finally:
        pass


def read_pdf(pdf_file_path):
    try:
        blob_client = container_client.get_blob_client(pdf_file_path)
        pdf_bytes = blob_client.download_blob().readall()

        # Read the PDF using PyMuPDF
        pdf_document = fitz.open(stream=io.BytesIO(pdf_bytes))

        text = ''
        for i in range(len(pdf_document)):
            page = pdf_document[i]
            text += page.get_text()

        # Close the PDF document
        pdf_document.close()

        return text
    except Exception as e :
         print(f"Error reading PDF: {e}")
         return None
        
# def read_pdf(pdf_file_path):
#     try:
#             text = ''
#             pdf_reader =PdfReader(pdf_file_path)
#             for i, page in enumerate(pdf_reader.pages):
#               text += page.extract_text()

#             return text

#     except Exception as e:
#         print(f"Error reading PDF: {e}")
#         return None



def documents_to_strings(documents):
    # Initialize an empty list to store the strings
    document_strings = []

    for document in documents:
        # Assuming each document is a dictionary or object with a 'content' property
        content = document.page_content
        document_strings.append(content)
    return document_strings
