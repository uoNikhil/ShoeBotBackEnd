from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
 
app = Flask(__name__)
 
# Replace 'YOUR_MONGODB_URI' with your actual MongoDB URI
MONGO_URI = 'mongodb+srv://ramvilla997:Qwerty123@cluster0.b8wxule.mongodb.net/shoebot_db?retryWrites=true&w=majority'
 
@app.route('/api/records', methods=['GET'])
def get_records():
    try:
        # Create a connection to the MongoDB
        client = MongoClient(MONGO_URI)
 
        # Access the desired database and collection
        db = client.get_database('shoebot_db')
        collection = db.get_collection('products')
 
        # Query the collection to fetch all records
        records = list(collection.find({}))
        for record in records:
            record['_id'] = str(record['_id'])
        # Close the MongoDB connection
        client.close()
 
        # Convert the records to a list of dictionaries
        records_list = [record for record in records]
 
        # Return the records as a JSON response
        return jsonify(records_list)
 
    except Exception as e:
        return jsonify({'error': str(e)}), 500
 

@app.route('/save_message', methods=['POST'])
def save_message():

    client = MongoClient(MONGO_URI)

    db = client['shoebot_db']
    collection = db['messages']
    
    try:
        # Get headers from the request
        message = request.headers.get('Message')
        is_user = request.headers.get('IsUser')
        uid = request.headers.get('uid')

        # Check if both headers are present
        if not message or is_user or uid is None:
            return jsonify({'error': 'Message and IsUser headers are required'}), 400

        # Convert is_user to boolean
        is_user = is_user.lower() == 'true'

        # Create a document to be inserted into MongoDB
        data = {'message': message, 'is_user': is_user, 'uid':uid}

        # Insert the document into the MongoDB collection
        result = collection.insert_one(data)

        # Return a success response
        return jsonify({'success': True, 'message_id': str(result.inserted_id)}), 200

    except Exception as e:
        # Handle exceptions
        return jsonify({'error': str(e)}), 500
    
@app.route('/get_messages', methods=['GET'])
def get_messages():

    client = MongoClient(MONGO_URI)

    db = client['shoebot_db']
    collection = db['messages']

    try:
        # Get the 'uid' parameter from the query string
        # uid_filter = request.args.get('uid')

        # Build the filter based on the 'uid' parameter
        # filter_criteria = {}  # By default, an empty filter retrieves all messages
        # if uid_filter:
        #     filter_criteria['uid'] = uid_filter

        # Retrieve documents from the MongoDB collection based on the filter
        # messages = list(collection.find())

        records = list(collection.find({}))
        for record in records:
            record['_id'] = str(record['_id'])
        # Close the MongoDB connection
        client.close()

        # Convert the records to a list of dictionaries
        records_list = [record for record in records]

        # Return the records as a JSON response
        return jsonify(records_list)

        # Return the messages as a JSON response
        # return jsonify({'messages': messages}), 200

    except Exception as e:
        # Handle exceptions
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')