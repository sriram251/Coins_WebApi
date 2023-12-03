from datetime import timedelta
import os
import time
from typing import List
import uuid
from flask import jsonify, request,Response, send_file
from sqlalchemy import and_

from App import app,session,container_client
from flask_jwt_extended import create_access_token,jwt_required,get_jwt_identity
from App.Extensions.OpenAI import FinancialAssistant, chat
from App.Modals.Budget import Budget, BudgetSchema
from App.Modals.Expense import Expense, ExpenseSchema
from App.Modals.ExpenseCategory import ExpenseCategory, ExpenseCategorySchema
from App.Modals.IncomeSource import IncomeSource, IncomeSourceSchema

from App.Modals.users import Users,User_schema
from App.Modals.Documents import Document, Document_schema
from App.Modals.DocumentChunks import DocumentChunks, DocumentChunks_schema

from blinker import signal
from App.Extensions.Embedding import Embed_document, Embeded_Text
from langchain.prompts import PromptTemplate
document_embedding_signal = signal('document-embedding')

def InsertDocumentChunk(documnet_chink : List[DocumentChunks]):
    try:
        session.add_all(documnet_chink)
        session.commit()
        pass
    except Exception as e:
        raise e
        pass
    
    
def generate_unique_filename(original_filename):
    # Generate a UUID and append it to the original filename
    unique_id = str(uuid.uuid4())
    _, file_extension = original_filename.rsplit('.', 1)
    new_filename = f"{unique_id}.{file_extension}"
    return new_filename

@document_embedding_signal.connect
def on_document_embedding(sender, **document_embedding_event):
    print(document_embedding_event)
    document_id = document_embedding_event.get("document_id")
    document_path = document_embedding_event.get("document_path")
    
    Document_chunks = Embed_document(path=document_path,Document_id= document_id)
    InsertDocumentChunk(Document_chunks)
    Response = session.query(Document).filter( Document.document_id == document_id).first()
    Response.is_encoded = True
    session.add(Response)
    session.commit()


@app.route('/GetUserInfo', methods=['GET'])
@jwt_required()
def hello():
    current_token = get_jwt_identity()
    user_id = current_token['User_id'] 
    Response = session.query(Users).filter(Users.id == user_id).one()
    return jsonify({'Response':User_schema.dump(Response)}),200

@app.route('/register', methods=['POST'])
def register():
    try:
        
        username = request.json.get('username', None)
        email = request.json.get('email', None)
        password = request.json.get('password', None)
        admin = request.json.get('Isadmin', None)
        print(admin)
        user_exist = session.query(Users).filter(Users.username == username or Users.email ==email ).first()
        
        if user_exist:
            print("User Already Exist")
            return jsonify({'Response' :'User Already Exist'}),409
        else:
            new_user = Users(username=username, email=email,admin=admin)
            new_user.set_password(password)
            session.add(new_user)
            session.commit()
            print("added")
            return jsonify({'Response' :'User Added succesfully'}),200
    except Exception as e:
            session.rollback()
            return jsonify({'Response': e}),500
            
     


@app.route('/login', methods=['POST'])
def Login():
    
    try:
        email = request.json.get('email', None)
        password = request.json.get('password', None)
        
        user:Users = session.query(Users).filter(Users.email==email).first()
        if user and user.check_password(password):
            user_info = {
                    'username': user.username,
                    'email': user.email,
                    'Admin':  user.admin,
                    "User_id":user.id
                }
            Expiry = timedelta(minutes=15)
            clams = {'role': 'admin' if user.admin else 'User'}
            token = create_access_token(identity=user_info,expires_delta=Expiry,additional_claims=clams) 
            return jsonify({"username":user.username,"email":user.email,"access_token":token}), 200
        else:
             return jsonify({"Response":"Email or password is incorrect"}),401 
            
    except Exception as e:
        print(e)
        return jsonify({'Response': "Something went wrong"}),500
    

@app.route('/add_income_source', methods=['POST'])
@jwt_required()
def add_income_source():
    try:
        data = request.get_json()
        current_token = get_jwt_identity()
        user_id = current_token['User_id'] 
        # Validate and deserialize input data using IncomeSourceSchema
        income_source_schema = IncomeSource()
        income_source_schema.user_id = user_id
        income_source_schema.transaction_date = data.get("transaction_date")
        income_source_schema.amount = data.get("amount")
        income_source_schema.source_name = data.get("source_name")
       

        # Add the new income source to the database
        session.add(income_source_schema)
        session.commit()

        # Return the added income source in the response
        return jsonify({'message': 'Income source added successfully'}), 201

    except Exception as e:
        # Handle validation errors or other exceptions
        return jsonify({'error': str(e)}), 400

@app.route('/Get_income_sources', methods=['GET'])
@jwt_required()
def get_all_income_sources():
    current_token = get_jwt_identity()
    user_id = current_token['User_id'] 
    income_sources = session.query(IncomeSource).filter(IncomeSource.user_id == user_id).order_by(IncomeSource.transaction_date).all()
    income_sources_schema = IncomeSourceSchema(many=True)
    result = income_sources_schema.dump(income_sources)
    return jsonify({'Response': result}), 200


@app.route('/add_Budget', methods=['POST'])
@jwt_required()
def add_Budget():
    try:
        data = request.get_json()
        current_token = get_jwt_identity()
        user_id = current_token['User_id'] 
        # Validate and deserialize input data using IncomeSourceSchema
        Budget_schema = Budget()
        Budget_schema.user_id = user_id
        Budget_schema.category_id = data.get("category_id")
        Budget_schema.budget_amount = data.get("budget_amount")
        Budget_schema.month = data.get("month")
        Budget_schema.year = data.get("year")

        # Add the new income source to the database
        session.add(Budget_schema)
        session.commit()

        # Return the added income source in the response
        return jsonify({'message': 'Budget added successfully'}), 201

    except Exception as e:
        session.rollback()
        # Handle validation errors or other exceptions
        return jsonify({'error': str(e)}), 400

@app.route('/Get_Budgets', methods=['GET'])
@jwt_required()
def get_all_Budgets():
    current_token = get_jwt_identity()
    user_id = current_token['User_id'] 
    Budgets = session.query(Budget).filter(Budget.user_id == user_id).all()
    Budget_schema = BudgetSchema(many=True)
    result = Budget_schema.dump(Budgets)
    result = [{"budget_amount": original_data["budget_amount"],
    "budget_id": original_data["budget_id"],
    "category_name": original_data["category"]["category_name"],
    "category_id": original_data["category_id"],
    "month": original_data["month"],
    "user_id": original_data["user_id"],
    "year": original_data["year"]} for item,original_data in enumerate(result)]
    return jsonify({'Response': result}), 200
@app.route('/add_ExpenseCategory', methods=['POST'])
@jwt_required()
def add_ExpenseCategory():
    try:
        data = request.get_json()
        current_token = get_jwt_identity()
        user_id = current_token['User_id'] 
        # Validate and deserialize input data using IncomeSourceSchema
        ExpenseCategory_schema = ExpenseCategory()
        ExpenseCategory_schema.user_id = user_id
        ExpenseCategory_schema.category_name = data.get("category_name")
       

        # Add the new income source to the database
        session.add(ExpenseCategory_schema)
        session.commit()

        # Return the added income source in the response
        return jsonify({'message': 'Expense Category added successfully'}), 201

    except Exception as e:
        session.rollback()
        # Handle validation errors or other exceptions
        return jsonify({'error': str(e)}), 400

@app.route('/Get_ExpenseCategorys', methods=['GET'])
@jwt_required()
def get_all_ExpenseCategorys():
    current_token = get_jwt_identity()
    user_id = current_token['User_id'] 
    Budgets = session.query(ExpenseCategory).filter(ExpenseCategory.user_id == user_id).all()
    Budget_schema = ExpenseCategorySchema(many=True)
    result = Budget_schema.dump(Budgets)
    return jsonify({'Response': result}), 200


@app.route('/add_Expense', methods=['POST'])
@jwt_required()
def add_Expense():
    try:
        data = request.get_json()
        current_token = get_jwt_identity()
        user_id = current_token['User_id'] 
        # Validate and deserialize input data using IncomeSourceSchema
        Expense_schema = Expense()
        Expense_schema.user_id = user_id
        Expense_schema.category_id = data.get("category_id")
        Expense_schema.amount = data.get("amount")
        Expense_schema.description = data.get("description")
        Expense_schema.expense_date = data.get("expense_date")
        
        # Add the new income source to the database
        session.add(Expense_schema)
        session.commit()

        # Return the added income source in the response
        return jsonify({'message': 'Expense Category added successfully'}), 201

    except Exception as e:
        session.rollback()
        # Handle validation errors or other exceptions
        return jsonify({'error': str(e)}), 400

@app.route('/Get_Expenses', methods=['GET'])
@jwt_required()
def get_all_Expense():
    current_token = get_jwt_identity()
    user_id = current_token['User_id'] 
    Expenses = session.query(Expense).filter(Expense.user_id == user_id).all()
    Expense_schema = ExpenseSchema(many=True)
    result = Expense_schema.dump(Expenses)
    result = [{"amount": original_data["amount"],
    "category_name": original_data["category"]["category_name"],
    "category_id": original_data["category_id"],
    "description": original_data["description"],
    "expense_date": original_data["expense_date"],
    "expense_id": original_data["expense_id"],
    "user_id": original_data["user_id"]} for item,original_data in enumerate(result)]
    return jsonify({'Response': result}), 200

@app.route('/QueryDoucment', methods=['POST'])
@jwt_required()
def QueryDoucment():
    current_token = get_jwt_identity()
    user_id = current_token['User_id'] 
    Query = request.json.get('Query', None)
    Query_vector = Embeded_Text(Query)
    Response =session.query(DocumentChunks.content,DocumentChunks.embedding.cosine_distance(Query_vector)).filter(DocumentChunks.embedding.cosine_distance(Query_vector) < 0.8).order_by(DocumentChunks.embedding.cosine_distance(Query_vector)).all()
    
    Jsoin_Response = DocumentChunks_schema.dump(Response)
    Records = [ item.get("content") for item in Jsoin_Response]
    Records = "".join(Records)
    
    return jsonify({"Response":Records}),200
    


@app.route('/download/<documentID>')
def download(documentID):
    Response = session.query(Document).filter(Document.document_id == documentID).first()
    filename = Response.file_path
    blob_client = container_client.get_blob_client(Response.file_path)
    blob_properties = blob_client.get_blob_properties()

    # Specify the content type based on the file extension
    content_type = "application/octet-stream"
    if "." in filename:
        _, extension = filename.rsplit(".", 1)
        content_type = f"application/{extension}"

    return send_file(
        blob_client.download_blob().readall(),
        mimetype=content_type,
        as_attachment=True,
        download_name=filename
    )

@app.route('/UploadDocument', methods=['POST'])
@jwt_required()
def uploadDoument():
    current_token = get_jwt_identity()
    user_id = current_token['User_id'] 
    if 'file' not in request.files:
        return "No file part"

    file = request.files['file']
    Title = request.form.get('Title')
    description = request.form.get('description')

    if file.filename == '':
        return "No selected file"

   
    if file:
        new_filename = generate_unique_filename(file.filename)

        blob_client = container_client.get_blob_client(new_filename)

        # Upload file to Azure Storage with the unique filename
        blob_client.upload_blob(file.stream.read(), overwrite=True)
        # Specify the directory where you want to save the file
        upload_folder = 'uploads'  # Change to your desired directory

        # if not os.path.exists(upload_folder):
        #     os.makedirs(upload_folder)
        # path = os.path.join(upload_folder, new_filename)
    
        Documet_Exist = session.query(Document).filter(Document.file_path == new_filename).first()
        if(Documet_Exist):
             return jsonify({'Response' :'Document Already Exist'}),409

        # file.save(path)

        Document_to_add = Document(title=Title,description=description,user_id = user_id,file_path=new_filename,is_encoded = False) 
        session.add(Document_to_add)
        session.commit()
        response = {
                        "data": "File uploaded successfully with description: " + description,
                        "status": "success", 
                        "id": Document_to_add.document_id
                    }

        embedding_event = {"document_id" : Document_to_add.document_id , "document_path":new_filename }
        document_embedding_signal.send(**embedding_event)
        return jsonify(response),200
    
    
    
@app.route('/GetDocuments', methods=['GET'])
@jwt_required()
def GetDocuments():
    current_token = get_jwt_identity()
    user_id = current_token['User_id']
    
    Response = session.query(Document).filter(Document.user_id == user_id ).all()
    
    return jsonify({"Response":Document_schema.dump(Response)}),200

@app.route('/DeleteDocument/<int:Document_id>', methods=['DELETE'])
@jwt_required()
def DeleteDocument(Document_id):
    current_token = get_jwt_identity()
    user_id = current_token['User_id']
    
    Response = session.query(Document).filter(Document.user_id == user_id and Document.document_id == Document_id).first()
    
    if(Response):
        session.delete(Response)
        session.commit()
        return jsonify({"Response": "File removed successfully" }),200
    else:
        return jsonify({"Response": "File Not found" }),404

@app.route('/QAdocument', methods=['POST'])
@jwt_required()
def AskQuestionAboutDocument():
    try:
        Document_id = request.json.get('Document_id', None)
        Question = request.json.get('Question', None)
        Query_vector = Embeded_Text(Question)
        Response =session.query(DocumentChunks.content,DocumentChunks.embedding.cosine_distance(Query_vector)).filter(and_(DocumentChunks.embedding.cosine_distance(Query_vector) < 0.8,DocumentChunks.document_id ==Document_id) ).order_by(DocumentChunks.embedding.cosine_distance(Query_vector)).limit(30).all()
    
        Jsoin_Response = DocumentChunks_schema.dump(Response)
        Records = [ item.get("content") for item in Jsoin_Response]
        Records = "".join(Records)
        
        qa_template = """Context information is below from a document.
                            ---------------------
                            {context}
                            ---------------------
                            you are a world class Financail assistant. 
                            Given the context information and not prior knowledge, 
                            Begin! Remember to speak as a Financail assistant to the customer 
                            with no financial background when giving your final answer.
                            If the question not related to the context you can Answer as question is not related to document.
                            If need you can provide it as points.
                            answer the question: {question}
                            Answer:
                      """
        prompt_template = PromptTemplate.from_template(qa_template)
        Result = chat({"context":Records,"question":Question},prompt_template)    
        return jsonify({"Document_id":Document_id,"Question":Question,"Response":Result})
        
        
        pass
    except Exception as e:
        pass
    
    
@app.route('/FinancialAssistant', methods=['POST'])
@jwt_required()
def stream_data():
    # Your streaming data source
    Question = request.json.get('Question', None)
        
    if(Question):
        return jsonify({"Response":FinancialAssistant(Question)}),200   
            # Create a streaming response with 'text/stream' content type
    return jsonify({"Response":"Question is not present"}),404
    
    




        

     