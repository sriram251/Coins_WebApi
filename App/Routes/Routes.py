from datetime import timedelta
from io import BytesIO
import os
import time
from typing import List
import uuid
from flask import jsonify, request,Response, send_file
from sqlalchemy import and_

from App import app,Session,container_client

from flask_jwt_extended import create_access_token,jwt_required,get_jwt_identity
from App.Extensions.OpenAI import FinancialAssistant, Summarize_document, chat
from App.Extensions.Embedding import Embed_Scheme, Embed_document, Embeded_Text, process_document
from App.Modals.Budget import Budget, BudgetSchema
from App.Modals.Expense import Expense, ExpenseSchema
from App.Modals.ExpenseCategory import ExpenseCategory, ExpenseCategorySchema
from App.Modals.IncomeSource import IncomeSource, IncomeSourceSchema
from App.Modals.Insurance_scheme import InsuranceCategory, InsuranceCategorySchema, InsuranceScheme, InsuranceSchemeSchema, SchemeVector, SchemeVectorSchema

from App.Modals.users import Users,User_schema
from App.Modals.Documents import Document, Document_schema
from App.Modals.DocumentChunks import DocumentChunks, DocumentChunks_schema

from blinker import signal
from langchain.prompts import PromptTemplate
from multiprocessing import Process
document_embedding_signal = signal('document-embedding')
InsuranceScheme_embedding_signal = signal('InsuranceScheme-embedding')
def InsertDocumentChunk(documnet_chink : List[DocumentChunks]):
    try:
        session = Session()
        session.add_all(documnet_chink)
        session.commit()
        pass
    except Exception as e:
        raise e
        pass
    finally:
        session.close()
    
    
def generate_unique_filename(original_filename):
    # Generate a UUID and append it to the original filename
    unique_id = str(uuid.uuid4())
    _, file_extension = original_filename.rsplit('.', 1)
    new_filename = f"{unique_id}.{file_extension}"
    return new_filename


@InsuranceScheme_embedding_signal.connect
def on_InsuranceScheme_embedding(sender, **document_embedding_event):
    session = Session()
    try:
        
        scheme_id = document_embedding_event.get("scheme_id")
        document_path = document_embedding_event.get("document_path")
        
        Document_chunks = Embed_Scheme(path=document_path,scheme_id= scheme_id)
        InsertDocumentChunk(Document_chunks)
        Response = session.query(InsuranceScheme).filter( InsuranceScheme.scheme_id == scheme_id).first()
        Response.isencoded = True
        session.add(Response)
        session.commit()
    except Exception as e:
        raise e
    finally:
        session.close()

@document_embedding_signal.connect
def on_document_embedding(sender, **document_embedding_event):
    document_id = document_embedding_event.get("document_id")
    document_path = document_embedding_event.get("SchemeDocument_path")
    try:
        session = Session()
        Document_chunks = Embed_document(path=document_path,Document_id= document_id)
        InsertDocumentChunk(Document_chunks)
        Response = session.query(Document).filter( Document.document_id == document_id).first()
        Response.is_encoded = True
        session.add(Response)
        session.commit()
    except Exception as e:
        raise e
    finally:
        session.close()
    
def document_embedding(document_id,document_path):
    # document_id = document_embedding_event.get("document_id")
    # document_path = document_embedding_event.get("SchemeDocument_path")
    try:
        session = Session()
        print("Is embedding")
        Document_chunks = Embed_document(path=document_path,Document_id= document_id)
        InsertDocumentChunk(Document_chunks)
        Response = session.query(Document).filter( Document.document_id == document_id).first()
        Response.is_encoded = True
        session.add(Response)
        session.commit()
    except Exception as e:
        raise e
    finally:
        session.close()
    
def InsuranceScheme_embedding(scheme_id,document_path):
    
    # scheme_id = document_embedding_event.get("scheme_id")
    # document_path = document_embedding_event.get("document_path")
    try:
        session = Session()
        Document_chunks = Embed_Scheme(path=document_path,scheme_id= scheme_id)
        InsertDocumentChunk(Document_chunks)
        Response = session.query(InsuranceScheme).filter( InsuranceScheme.scheme_id == scheme_id).first()
        Response.isencoded = True
        session.add(Response)
        session.commit()
    except Exception as e:
        raise e
    finally:
        session.close()
@app.route('/GetUserInfo', methods=['GET'])
@jwt_required()
def hello():
    try:
        session = Session()
        current_token = get_jwt_identity()
        user_id = current_token['User_id'] 
        Response = session.query(Users).filter(Users.id == user_id).one()
        return jsonify({'Response':User_schema.dump(Response)}),200
    except Exception as e:
        print(e)
        return jsonify({'Response':"something went wrong"}),500
    finally:
        session.close()
        
@app.route('/')
def index():
    return jsonify({'Response': "Application is running"}),200
@app.route('/register', methods=['POST'])
def register():
    try:
        session = Session()
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
    finally:
        session.close()
            
     


@app.route('/login', methods=['POST'])
def Login():
    
    try:
        session = Session()
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
            Expiry = timedelta(minutes=30)
            clams = {'role': 'admin' if user.admin else 'User'}
            token = create_access_token(identity=user_info,expires_delta=Expiry,additional_claims=clams) 
            return jsonify({"username":user.username,"email":user.email,"access_token":token}), 200
        else:
             return jsonify({"Response":"Email or password is incorrect"}),401 
            
    except Exception as e:
        session.rollback() 
        print(e)
        return jsonify({'Response': "Something went wrong"}),500
    finally:
        session.close()
    

@app.route('/add_income_source', methods=['POST'])
@jwt_required()
def add_income_source():
    try:
        session = Session()
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
    finally:
        session.close()

@app.route('/Get_income_sources', methods=['GET'])
@jwt_required()
def get_all_income_sources():
    try:
        session = Session()
        current_token = get_jwt_identity()
        user_id = current_token['User_id'] 
        income_sources = session.query(IncomeSource).filter(IncomeSource.user_id == user_id).order_by(IncomeSource.transaction_date).all()
        income_sources_schema = IncomeSourceSchema(many=True)
        result = income_sources_schema.dump(income_sources)
        return jsonify({'Response': result}), 200
    except Exception as e:
         return jsonify({'error': str(e)}), 400
    finally:
        session.close()


@app.route('/add_Budget', methods=['POST'])
@jwt_required()
def add_Budget():
    try:
        session = Session()
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
    finally:
        session.close()

@app.route('/Get_Budgets', methods=['GET'])
@jwt_required()
def get_all_Budgets():
    try:
        session = Session()
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
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()
@app.route('/add_ExpenseCategory', methods=['POST'])
@jwt_required()
def add_ExpenseCategory():
    try:
        session = Session()
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
    finally:
        session.close()

@app.route('/Get_ExpenseCategorys', methods=['GET'])
@jwt_required()
def get_all_ExpenseCategorys():
    try:
        session = Session()
        current_token = get_jwt_identity()
        user_id = current_token['User_id'] 
        Budgets = session.query(ExpenseCategory).filter(ExpenseCategory.user_id == user_id).all()
        Budget_schema = ExpenseCategorySchema(many=True)
        result = Budget_schema.dump(Budgets)
        return jsonify({'Response': result}), 200
    except Exception as e:
        
        # Handle validation errors or other exceptions
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()

@app.route('/Get_InsuranceScheme', methods=['GET'])
@jwt_required()
def get_all_InsuranceScheme():
    try:
        session = Session()
        insurance_schemes = session.query(InsuranceScheme).all()
        insurance_scheme = InsuranceSchemeSchema(many=True)
        result = insurance_scheme.dump(insurance_schemes)
        return jsonify({'Response': result}), 200
    except Exception as e:
         # Handle validation errors or other exceptions
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()

@app.route('/Get_InsuranceCategory', methods=['GET'])
@jwt_required()
def Get_InsuranceCategory():
    try:
        session = Session()
        current_token = get_jwt_identity()
        user_id = current_token['User_id'] 
        Insurance_Category = session.query(InsuranceCategory).all()
        InsuranceCategory.description,
        InsuranceCategory.category_name,
        InsuranceCategory.category_id
        Insurance_Category_schema = InsuranceCategorySchema(many=True)
        result = Insurance_Category_schema.dump(Insurance_Category)
        result = [{"category_id": original_data["category_id"],
        "category_name": original_data["category_name"],
        "description": original_data["description"],
        } for item,original_data in enumerate(result)]
        return jsonify({'Response': result}), 200
    except Exception as e:
         # Handle validation errors or other exceptions
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()
@app.route('/add_insurance_scheme', methods=['POST'])
@jwt_required()
def add_insurance_scheme():
    try:
        session = Session()
        current_token = get_jwt_identity()
        user_id = current_token['User_id'] 
        if 'file' not in request.files:
            return "No file part"

        file = request.files['file']
        scheme_name = request.form.get('scheme_name')
        description = request.form.get('description')
        coverage_amount  = request.form.get('coverage_amount')
        premium_amount  = request.form.get('premium_amount')
        start_date = request.form.get('start_date')
        end_date  = request.form.get('end_date')
        category_id  = request.form.get('category_id')
        
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
        
            Documet_Exist = session.query(InsuranceScheme).filter(InsuranceScheme.document_path == new_filename).first()
            if(Documet_Exist):
                return jsonify({'Response' :'Scheme Already Exist'}),409

            # file.save(path)
            Embeded_description = Embeded_Text(description)
            InsuranceScheme_to_add = InsuranceScheme(scheme_name=scheme_name,description=description,category_id= category_id,coverage_amount=coverage_amount,end_date=start_date,premium_amount=premium_amount,start_date=end_date,document_path=new_filename,description_vector_data=Embeded_description) 
            session.add(InsuranceScheme_to_add)
        
            session.commit()
            response = {
                            "data": "Insurance Scheme is Added successfully",
                            "status": "success", 
                            "id": InsuranceScheme_to_add.scheme_id
                        }

            # embedding_event = {"scheme_id" : InsuranceScheme_to_add.scheme_id , "document_path":new_filename }
            # InsuranceScheme_embedding_signal.send(**embedding_event)
            # 
            bidding_cb = Process(target=InsuranceScheme_embedding, args=(InsuranceScheme_to_add.scheme_id, new_filename))
            bidding_cb.start()
            
            return jsonify(response),200
    except Exception as ex:
        session.rollback()
        return jsonify({"response":str(ex)}),200
    finally:
        session.close()
    
@app.route('/Get_insurance_scheme/<int:scheme_id>', methods=['GET'])
@jwt_required()
def Get_insurance_scheme(scheme_id):
    try:
        session = Session()
        insurance_scheme = session.query(InsuranceScheme).get(scheme_id)
        insurance_schema = InsuranceSchemeSchema()
        result = insurance_schema.dump(insurance_scheme)
        return jsonify(result), 200

    except Exception as ex:
        session.rollback()
        return jsonify({"response": str(ex)}), 500
    finally:
        session.close()

@app.route('/edit_insurance_scheme/<int:scheme_id>', methods=['PUT'])
@jwt_required()
def edit_insurance_scheme(scheme_id):
    try:
        session = Session()
        current_token = get_jwt_identity()
        user_id = current_token['User_id']

        # Fetch the insurance scheme to edit
        insurance_scheme = session.query(InsuranceScheme).get(scheme_id)
        if not insurance_scheme:
            return jsonify({'response': 'Scheme not found'}), 404

        # Check if the user has the right to edit this scheme
        if insurance_scheme.user_id != user_id:
            return jsonify({'response': 'Unauthorized'}), 401

        # Check if a new file is provided
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                # Update the document path if a new file is provided
                new_filename = generate_unique_filename(file.filename)
                blob_client = container_client.get_blob_client(new_filename)
                blob_client.upload_blob(file.stream.read(), overwrite=True)
                insurance_scheme.document_path = new_filename

        # Update other scheme attributes based on the request form data
        insurance_scheme.scheme_name = request.form.get('scheme_name', insurance_scheme.scheme_name)
        insurance_scheme.description = request.form.get('description', insurance_scheme.description)
        insurance_scheme.coverage_amount = request.form.get('coverage_amount', insurance_scheme.coverage_amount)
        insurance_scheme.premium_amount = request.form.get('premium_amount', insurance_scheme.premium_amount)
        insurance_scheme.start_date = request.form.get('start_date', insurance_scheme.start_date)
        insurance_scheme.end_date = request.form.get('end_date', insurance_scheme.end_date)
        insurance_scheme.category_id = request.form.get('category_id', insurance_scheme.category_id)

        # Commit the changes to the database
        session.commit()

        response = {
            "data": "Insurance Scheme is updated successfully",
            "status": "success",
            "id": insurance_scheme.scheme_id
        }

        # Trigger the embedding signal for the updated scheme
        
        return jsonify(response), 200

    except Exception as ex:
        session.rollback()
        return jsonify({"response": str(ex)}), 500
    finally:
        session.close()

@app.route('/DeleteInsuranceschemes/<int:scheme_id>', methods=['DELETE'])
@jwt_required()
def DeleteInsuranceschemes(scheme_id):
    current_token = get_jwt_identity()
    user_id = current_token['User_id']
    try:
        session = Session()
        Response = session.query(InsuranceScheme).filter(InsuranceScheme.scheme_id == scheme_id).first()
        
        if(Response):
            document_client =  container_client.get_blob_client(Response.document_path)
            session.delete(Response)
            session.commit()
            if(document_client):
                document_client.delete_blob()
            return jsonify({"Response": "scheme removed successfully" }),200
        else:
            return jsonify({"Response": "scheme Not found" }),404
    except Exception as ex:
        session.rollback()
        return jsonify({"response": str(ex)}), 500
    finally:
        session.close()
@app.route('/add_Expense', methods=['POST'])
@jwt_required()
def add_Expense():
    try:
        session = Session()
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
    finally:
        session.close()

@app.route('/Get_Expenses', methods=['GET'])
@jwt_required()
def get_all_Expense():
    try:
        session = Session()
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
    except Exception as e:
        session.rollback()
        # Handle validation errors or other exceptions
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()

@app.route('/QueryDoucment', methods=['POST'])
@jwt_required()
def QueryDoucment():
    try:
        session = Session()
        current_token = get_jwt_identity()
        user_id = current_token['User_id'] 
        Query = request.json.get('Query', None)
        Query_vector = Embeded_Text(Query)
        Response =session.query(DocumentChunks.content,DocumentChunks.embedding.cosine_distance(Query_vector)).filter(DocumentChunks.embedding.cosine_distance(Query_vector) < 0.8).order_by(DocumentChunks.embedding.cosine_distance(Query_vector)).all()
        
        Jsoin_Response = DocumentChunks_schema.dump(Response)
        Records = [ item.get("content") for item in Jsoin_Response]
        Records = "".join(Records)
        
        return jsonify({"Response":Records}),200
    except Exception as e:
       
        # Handle validation errors or other exceptions
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()
    

@app.route('/downloadScheme/<schemeId>')
def downloadScheme(schemeId):
    try:
        session = Session()
        Response = session.query(InsuranceScheme).filter(InsuranceScheme.scheme_id == schemeId).first()
        filename = Response.document_path
        blob_client = container_client.get_blob_client(filename)
        blob_content = blob_client.download_blob().readall()

    # Wrap the content in BytesIO to make it a file-like object
        file_like = BytesIO(blob_content)

        # Specify the content type based on the file extension
        content_type = "application/octet-stream"
        if "." in filename:
            _, extension = filename.rsplit(".", 1)
            content_type = f"application/{extension}"

        return send_file(
            file_like,
            mimetype=content_type,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
       
        # Handle validation errors or other exceptions
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()

@app.route('/download/<documentID>')
def download(documentID):
    try:
        session = Session()
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
    except Exception as e:
        
        # Handle validation errors or other exceptions
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()

@app.route('/UploadDocument', methods=['POST'])
@jwt_required()
def uploadDoument():
    try:
        session = Session()
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
                            "data": "File uploaded successfully.. Encoding is in progress",
                            "status": "success", 
                            "id": Document_to_add.document_id
                        }

            #embedding_event = {"document_id" : Document_to_add.document_id , "document_path":new_filename }
            bidding_cb = Process(target=document_embedding, args=(Document_to_add.document_id, new_filename))
            bidding_cb.start()
            #document_embedding_signal.send(**embedding_event)
            return jsonify(response),200
    except Exception as e:
        session.rollback()
        # Handle validation errors or other exceptions
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()
    
    
@app.route('/GetDocuments', methods=['GET'])
@jwt_required()
def GetDocuments():
    try:
        session = Session()
        current_token = get_jwt_identity()
        user_id = current_token['User_id']
        
        Response = session.query(Document).filter(Document.user_id == user_id ).all()
        
        return jsonify({"Response":Document_schema.dump(Response)}),200
    except Exception as e:
        
        # Handle validation errors or other exceptions
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()

@app.route('/DeleteDocument/<int:Document_id>', methods=['DELETE'])
@jwt_required()
def DeleteDocument(Document_id):
    try:
        session = Session()
        current_token = get_jwt_identity()
        user_id = current_token['User_id']
        
        Response = session.query(Document).filter(Document.user_id == user_id and Document.document_id == Document_id).first()
        
        if(Response):
            document_client =  container_client.get_blob_client(Response.file_path)
            session.delete(Response)
            session.commit()
            document_client.delete_blob()
            return jsonify({"Response": "File removed successfully" }),200
        else:
            return jsonify({"Response": "File Not found" }),404
    except Exception as e:
        session.rollback()
        # Handle validation errors or other exceptions
        return jsonify({'error': str(e)}), 400
    finally:
        session.close()

@app.route('/QAInsuranceScheme', methods=['POST'])
@jwt_required()
def AskQuestionAboutInsuranceScheme():
    try:
        session = Session()
        SchemeId = request.json.get('SchemeId', None)
        Question = request.json.get('Question', None)
        Query_vector = Embeded_Text(Question)
        #Response =session.query().filter(InsuranceScheme.description_vector_data.cosine_distance(Query_vector) <= 0.8).order_by(DocumentChunks.embedding.cosine_distance(Query_vector)).limit(30).all()
        #Scheme_id = [item.get('scheme_id') for item in Response]
        SchemeContent =session.query(SchemeVector.content).filter(and_(SchemeVector.vector_data.cosine_distance(Query_vector) <= 0.8,SchemeVector.scheme_id == SchemeId)).order_by(SchemeVector.vector_data.cosine_distance(Query_vector)).limit(30).all()
        
        insurance_scheme = SchemeVectorSchema(many=True)
        result = insurance_scheme.dump(SchemeContent)
        
        Records = [ item.get("content") for item in result]
        Records = "".join(Records)
        
        qa_template = """Context information is below from a Insurance Scheme document.
                            ---------------------
                            {context}
                            ---------------------
                            you are a world class Insurance assistant. 
                            Given the context information and not prior knowledge, 
                            Begin! Remember to speak as a Insurance assistant to the customer 
                            with no perior knowledge in insurace  background when giving your final answer.
                            If the question not related to the context you can Answer as question is not related to Insurance Scheme.
                            If need you should provide points you should provide it as points. like
                            1.)...
                            2.)..
                            .
                            answer the question: {question}
                            Answer:
                      """
        prompt_template = PromptTemplate.from_template(qa_template)
        Result = chat({"context":Records,"question":Question},prompt_template)    
        return jsonify({"schemes":SchemeId,"Question":Question,"Response":Result}),200
    except Exception as e:
        session.rollback()
        return jsonify({"Response":str(e)}),500
    finally:
        session.close()
@app.route('/QAdocument', methods=['POST'])
@jwt_required()
def AskQuestionAboutDocument():
    try:
        session = Session()
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
                            If need you can provide it as points.like
                            1.)...
                            2.)..
                            .
                            answer the question: {question}
                            Answer:
                      """
        prompt_template = PromptTemplate.from_template(qa_template)
        Result = chat({"context":Records,"question":Question},prompt_template)    
        return jsonify({"Document_id":Document_id,"Question":Question,"Response":Result})
        
    except Exception as e:
        return jsonify({"Response":str(e)}),500
        pass
    finally:
        session.close()
    
    
@app.route('/FinancialAssistant', methods=['POST'])
@jwt_required()
def stream_data():
    # Your streaming data source
    Question = request.json.get('Question', None)
        
    if(Question):
        return jsonify({"Response":FinancialAssistant(Question)}),200   
            # Create a streaming response with 'text/stream' content type
    return jsonify({"Response":"Question is not present"}),404


@app.route('/SummarizeDocument', methods=['POST'])
@jwt_required()
def SummarizeDocument():
    try:
        current_token = get_jwt_identity()
        user_id = current_token['User_id'] 
        if 'file' not in request.files:
            return "No file part"

        file = request.files['file']
        if file.filename == '':
            return "No selected file"

    
        if file:
            current_directory = os.getcwd()
            print("Present Working Directory:", current_directory)
                
            folder_name = "uploads"
            folder_path = os.path.join(current_directory, folder_name)
                # Check if the folder exists
            if not os.path.exists(folder_path):
                    # Create the folder if it doesn't exist
                    os.makedirs(folder_path)
                    print(f"Folder '{folder_path}' created successfully.")
            else:
                    print(f"Folder '{folder_path}' already exists.")

            file_path = os.path.join(folder_path, file.filename)
            file.save(file_path)
            #DocStrings = process_document(file_path)
            
        
            result = Summarize_document(user_id,file_path)
            os.remove(file_path)
            return jsonify(result),200
    except Exception as e:
        return jsonify({"Response":str(e)}),500
        pass  
    
@app.route('/InsuranceAssistant', methods=['POST'])
def InsuranceAssistant():
          try:
                session = Session()
                Question = request.json.get('Question', None)
                Query_vector = Embeded_Text(Question)
                SchemeContent =session.query(SchemeVector).filter(SchemeVector.vector_data.cosine_distance(Query_vector) <= 0.8).order_by(SchemeVector.vector_data.cosine_distance(Query_vector)).limit(30).all()
                
                insurance_scheme = SchemeVectorSchema(many=True)
                result = insurance_scheme.dump(SchemeContent)
                Scheme_ids = [item.get("scheme_id") for item in result]
                Scheme_ids = set(Scheme_ids)
                Scheme_ids = list(Scheme_ids)
                Records = [ item.get("content") for item in result]
                Records = "".join(Records)
                
                qa_template = """Context information is below from a Insurance Scheme document.
                                    ---------------------
                                    {context}
                                    ---------------------
                                    you are a world class Insurance assistant. 
                                    Given the context information and not prior knowledge, 
                                    Begin! Remember to speak as a Insurance assistant to the customer 
                                    with no perior knowledge in insurace  background when giving your final answer.
                                    If the question not related to the context you can Answer as question is not related to Insurance Scheme.
                                    If need user asked as list or points you should provide it as points. like
                                    1.)...
                                    2.)..
                                    .
                                    answer the question: {question}
                                    Answer:
                              """
                prompt_template = PromptTemplate.from_template(qa_template)
                Result = chat({"context":Records,"question":Question},prompt_template)    
                return jsonify({"schemes":Scheme_ids ,"Question":Question,"Response":Result}),200
          except Exception as e:
                
                return jsonify({"Response":e}),500  
          finally:
                session.close()  


        

     