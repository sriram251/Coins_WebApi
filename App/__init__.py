import os
from flask import Flask
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base  
from azure.storage.blob import BlobServiceClient


from App.Extensions.OpenAI import ChainStreamHandler
app = Flask(__name__)
app.config.from_pyfile("../config.py")

from langchain.callbacks.manager import CallbackManager



os.environ["GOOGLE_API_KEY"] = "AIzaSyBCkK86PM9H98r1YVtKmiAZY6lvLWrRyPI"
os.environ["GOOGLE_CSE_ID"] = "733b2a2e844774208"
os.environ["OPENAI_API_TYPE"] = "azure"
os.environ["OPENAI_API_VERSION"] = "2023-03-15-preview"
os.environ["OPENAI_API_BASE"] = "https://mind-benders.openai.azure.com/"
os.environ["OPENAI_API_KEY"] ="ec509f23a3e94f9a8c776b65a2beba3a"
os.environ["blob_account_name"] ="mindbenders"
os.environ["blob_account_key"] ="+M2Z119kiTM6D5arCnUd2+q16rqFBBcwlq33D8zhg9DeH7uccXMzWhUWpRvDNWT5rLGwQzAiLwOU+AStes98Yg=="
os.environ["blob_container_name"] ="userdouments"
os.environ["Dbconnection"] ="postgresql://mindbinders:Aspire1234@mindbenders.postgres.database.azure.com:5432/coins"
bcrypt = Bcrypt(app=app)
Jwt = JWTManager(app=app)

CORS(app)
engine =  create_engine(app.config.get('SQLALCHEMY_DATABASE_URI'),echo=True)
Session = sessionmaker(engine)
session = Session()
Base = declarative_base()
ma = Marshmallow(app=app)
print(app.config)
account_name = os.environ.get("blob_account_name")
account_key = os.environ.get("blob_account_key")
container_name = os.environ.get("blob_container_name")

blob_service_client = BlobServiceClient(account_url=f"https://{account_name}.blob.core.windows.net", credential=account_key)
container_client = blob_service_client.get_container_client(container_name)


from .Routes import Routes

