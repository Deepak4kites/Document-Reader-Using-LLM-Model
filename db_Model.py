import os
import json
import re
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
import easyocr
from pymongo import MongoClient
from langchain_groq import ChatGroq
from states.state import state
import pandas as pd
from pymongo import MongoClient
from urllib.parse import quote_plus
# Initialize OCR reader
reader = easyocr.Reader(['en'], gpu=False)

# # Initialize MongoDB client
# username = "deepakkushwaha"
# password = "jXgyUuDBWfLC1SuW"

# # URL-encode the username and password
# encoded_username = quote_plus(username)
# encoded_password = quote_plus(password)

# # Construct the MongoDB URI
# #mongo_uri = "mongodb://encoded_username:encoded_password@cluster0.03tgz28.mongodb.net/"
# #mongo_uri= "mongodb://{encoded_username}:{encoded_password}@cluster12.zsk7elr.mongodb.net/Booking_Record?retryWrites=true&w=majority&appName=Cluster12"
# mongo_uri = "mongodb://deepakkushwaha:jXgyUuDBWfLC1SuW@cluster12.9mpgpue.mongodb.net/?appName=cluster12"
# client = MongoClient(mongo_uri)
# db = client['Booking_Record']
# collection = db['BookingRecord']

from pymongo import MongoClient
from urllib.parse import quote_plus
import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Get MongoDB credentials from environment variables
username = os.getenv('MONGO_USERNAME')
password = os.getenv('MONGO_PASSWORD')
host = os.getenv('MONGO_HOST', 'cluster12.zsk7elr.mongodb.net')
database = os.getenv('MONGO_DATABASE', "Booking_Record")  # Replace 'your_database' with your actual database name
collection_name = os.getenv('MONGO_COLLECTION', 'BookingRecord') 

# URL-encode the username and password
encoded_username = quote_plus(username)
encoded_password = quote_plus(password)

# Construct the MongoDB URI (SRV connection string format)
mongo_uri = f"mongodb+srv://{encoded_username}:{encoded_password}@{host}/{database}?retryWrites=true&w=majority"

# Connect to MongoDB
print("hello")
try:
    client = MongoClient(mongo_uri)
    db = client[database]  # Access the specified database
    collection = db[collection_name]
    print("world")
    # Test the connection
    print("Connected to MongoDB, collections: ", db.list_collection_names())
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")


#model used....
chat = ChatGroq(
    temperature=0,
    model="llama3-70b-8192",
    api_key="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"
)


# Function to interact with LangChain model
def ask_model(state):
    print("-------------reached asked_model------------\n\n")
    pdf_text = state['pdfText']
    filename = state['fileName']
    prompt = """Extract the Fields from the user input in the format given below.
    The format is
    {
   "fileName": "231231_booking_confirmation_1672312862.pdf",
   "orgName": "TestOrg ",
   "orderId": 231231,
   "ocrBucketName": "unilever-international-2086",
   "docType": "BOOKING_CONFIRMATION",
   "bookingDetails": {
       "carrierBookingNum": "",
       "billOfLadingNum": "",
       "referenceNumber": "",
       "carrierName": "SeaLand",
       "originServiceMode": "CY",
       "destinationServiceMode": "CY",
       "placeOfOrigin": "ZADUR",
       "placeOfDelivery": "KRPUS",
       "portOfLoad": "ZADUR",
       "portOfDischarge": "KRPUS",
       "temperature": {
           "unit": "C",
           "value": 23
       },
       "humidity": 13,
       "gensetRequired": false,
       "travelType": "SEA",
       "containerDetails": {
           "code": "standard20",
           "quantity": 2
       },
       "weight": {
           "unit": "mt",
           "value": 10
       },
       "commodityType": "",
       "hazardous": {
           "hazCode": "",
           "imoClassType": "",
           "packageCount": 1,
           "packageType": "",
           "packageGroup": ""
       },
       "voyageInfo": {
           "vesselName": "",
           "voyageNumber": "",
           "imoNumber": "",
           "departureEstimated": "2023-02-02T12:00:00Z",
           "arrivalEstimated": "2023-02-02T12:00:00Z"
       }
   },
   "shipmentDetails": {
       "shipmentDate": "2022-12-14 13:02:48",
       "containerPickUpDate": "2022-12-14 13:02:48",
       "railCutOffDate": "2022-12-14 13:02:48",
       "portCutOffDate": "2022-12-14 13:02:48",
       "vgmCutoffDate": "2022-12-14 13:02:48",
       "portOpenDate": "2022-12-14 13:02:48",
       "siCutOffDate": "2022-12-14 13:02:48",
       "shipOnBoardDate": "2022-12-14 13:02:48",
       "vent": "Close"
   },
   "containers": [{
       "containerId": "ABCD1234569",
       "type": "40' Dry Standard"
   },{
       "containerId": "ABCD1234568",
       "type": "20' Dry Standard"
   }]
}
    The output should strictly and EXACTLY in the above format and dont miss commas where nessassary.
    If a field is not present in the user input, leave it as an empty string.
    YOU MUST put orderID value in double quotes "".
    NEVER repeat the values of containers.
    The User input is: """+pdf_text+"""
    The filename is:"""+filename
    result = chat.invoke(prompt)
    print("model result: " + result.content)
    print("\n\n")

    string =result.content

    start_index = string.find('{')
    end_index = string.rfind('}') + 1
    if start_index == -1 or end_index == -1:
        raise ValueError("Invalid JSON string")
    json_string = string[start_index:end_index]
    json_data = json.loads(json_string)

    state['result'] = json.dumps(json_data, indent=4)
    # return {'fileName':state['fileName'],"filePath":state['filePath'],"image":False,"pdfText":result,"result":result.content}
    return state

# Function to read text from PDF
def pdf_reader(state):
    print("reached pdf_reader")
    file_path = state['filePath']
    resource_manager = PDFResourceManager()
    fake_file_handle = StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams(detect_vertical=True))
    
    with open(file_path, 'rb') as fp:
        interpreter = PDFPageInterpreter(resource_manager, converter)
        for page in PDFPage.get_pages(fp, check_extractable=True):
            interpreter.process_page(page)
    
    text = fake_file_handle.getvalue()
    
    converter.close()
    fake_file_handle.close()
    print("pdf content: " + text)
    print("\n\n")
    state['pdfText']=text
    # return {'fileName':state['fileName'],"filePath":state['filePath'],"image":False,"pdfText":text}
    return state

# Function to perform OCR on images
def ocr_image(state):
    print("reached ocr_image")
    file_path = state['filePath']
    result = reader.readtext(file_path, detail=0, paragraph=True, allowlist=None, blocklist=None, rotation_info=None)
    state['pdfText'] = '\n'.join(result)
    print("image content: " + result)
    print("\n\n")
    state['pdfText']=result
    # return {'fileName':state['fileName'],"filePath":state['filePath'],"image":False,"pdfText":result}
    return state

def send_to_mongodb(state):
    json_data = state['result']
    if isinstance(json_data, str):
        try:
            json_data = json.loads(json_data)
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON string: {e}")
            return
    
    # Check if json_data is a dictionary
    if isinstance(json_data, dict):
        try:
            collection.insert_one(json_data)
            print("JSON data inserted successfully into MongoDB.")
        except Exception as e:
            print(f"Failed to insert JSON data into MongoDB: {e}")
    else:
        print("Invalid JSON data format for MongoDB insertion")


# Dummy function for unsupported file types
def unsupported_file_type(state):
    print('Unsupported file type. Allowed types are PDF, PNG, JPG, JPEG, GIF')

def check_extension(state):
    print("filename: ")
    filename= state['fileName']
    print(filename)
    if(filename.endswith(('.png', '.jpg', '.jpeg', '.gif'))):
        state['image']=True
        # return {'fileName':state['fileName'],"filePath":state['filePath'],"image":True}
    else:
        state['image']=False
        # return {'fileName':state['fileName'],"filePath":state['filePath'],"image":False}

    return state

def check_condition(state):
    # return {'fileName':state['fileName'],"filePath":state['filePath'],"image":state['image']}
    return state

def check_value_of_image(state):
    print("reached check_value_of_image")
    print(state['image'])
    return state['image']
