import azure.functions as func
import logging

import openai

import json
import time

import os
from pymongo import MongoClient
from flask import jsonify


openAiKey = os.environ.get('OPENAI_API_KEY')
assistant_id = os.environ.get('ASSISTANT_ID')

print(openAiKey)
client = openai.OpenAI(api_key=openAiKey)
thread = client.beta.threads.create(messages=[])    
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="http_trigger")
def http_trigger(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        # Extracting the user input and thread_id from the request
        req_body = req.get_json()
        user_input = req_body.get('text')

        # Check if the user wants to exit
        if user_input.lower() == 'exit':
            return func.HttpResponse("Exit command received", status_code=200)

        # Add the user's message to the thread
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )

        # Create and run the assistant
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id,
            model="gpt-4-1106-preview",
            instructions="You are a helpful assistant that understand what the user wants and based on that suggest shoes from the .json file, \
                          and also ask follow up questions to narrow down the list. Give top 5 shoes that matches the description. \
                            If you cannot find all 5 related shoes, give remaining shoes which satisfies some of the user provided requriement, but always give 5 results.\
                                And before displaying the list of 5 shoes always use the phrase 'Here are the options.'",
            tools=[{"type": "code_interpreter"}, {"type": "retrieval"}]
        )

        # Wait for the run to complete
        run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id).status
        while run_status != 'completed':
            logging.info("run_status = {}".format(run_status))
            time.sleep(1)
            run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id).status

        # Retrieve and format the assistant's response
        messages = client.beta.threads.messages.list(thread_id=thread.id).data
        response = [message.content[0].text.value for message in messages if message.role == 'assistant']

        return func.HttpResponse(json.dumps(response), status_code=200, mimetype="application/json")

    except ValueError:
        return func.HttpResponse(
             "Invalid request. Please send a valid JSON with 'text' and 'thread_id'.",
             status_code=400
        )
    except Exception as e:
        return func.HttpResponse(
            f"An error occurred: {str(e)}",
            status_code=500
        )


# Replace 'YOUR_MONGODB_URI' with your actual MongoDB URI
MONGO_URI = 'mongodb+srv://ramvilla997:Qwerty123@cluster0.b8wxule.mongodb.net/shoebot_db?retryWrites=true&w=majority'

def get_mongo_client():
    return MongoClient(MONGO_URI)

def get_collection(collection_name):
    client = get_mongo_client()
    db = client.get_database('shoebot_db')
    return db.get_collection(collection_name)

@app.route('/api/records', methods=['GET'])
def get_records(request: func.HttpRequest) -> func.HttpResponse:
    try:
        # Access the desired collection
        collection = get_collection('products')

        # Query the collection to fetch all records
        records = list(collection.find({}))
        for record in records:
            record['_id'] = str(record['_id'])

        # Convert the records to a list of dictionaries
        records_list = [record for record in records]

        # Return the records as a JSON response
        return func.HttpResponse(jsonify(records_list), mimetype="application/json")

    except Exception as e:
        return func.HttpResponse(jsonify({'error': str(e)}), status_code=500)

@app.route('/save_message', methods=['POST'])
def save_message(request: func.HttpRequest) -> func.HttpResponse:
    try:
        # Access the desired collection
        collection = get_collection('messages')

        # Get headers from the request
        message = request.headers.get('Message')
        is_user = request.headers.get('IsUser')
        uid = request.headers.get('uid')

        # Check if both headers are present
        if not message or is_user is None or uid is None:
            return func.HttpResponse(jsonify({'error': 'Message, uid, and IsUser headers are required'}), status_code=400)

        # Convert is_user to boolean
        is_user = is_user.lower() == 'true'

        # Create a document to be inserted into MongoDB
        data = {'message': message, 'is_user': is_user, 'uid': uid}

        # Insert the document into the MongoDB collection
        result = collection.insert_one(data)

        # Return a success response
        return func.HttpResponse(jsonify({'success': True, 'message_id': str(result.inserted_id)}), status_code=200)

    except Exception as e:
        # Handle exceptions
        return func.HttpResponse(jsonify({'error': str(e)}), status_code=500)

@app.route('/get_messages', methods=['GET'])
def get_messages(request: func.HttpRequest) -> func.HttpResponse:
    try:
        # Access the desired collection
        collection = get_collection('messages')

        # Retrieve documents from the MongoDB collection
        records = list(collection.find({}))
        for record in records:
            record['_id'] = str(record['_id'])

        # Convert the records to a list of dictionaries
        records_list = [record for record in records]

        # Return the records as a JSON response
        return func.HttpResponse(jsonify(records_list), mimetype="application/json")

    except Exception as e:
        # Handle exceptions
        return func.HttpResponse(jsonify({'error': str(e)}), status_code=500)
