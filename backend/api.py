from flask import Flask, jsonify
from flask_cors import CORS # Import CORS
import json

app = Flask(__name__)
# Enable CORS to allow requests from your React app
CORS(app) 

@app.route("/")
def home():
    # A simple message to confirm the API is running
    return "Parking Lot API is running."

@app.route("/data")
def get_data():
    """This endpoint reads and returns the parking lot data."""
    try:
        with open('lots.json', 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error reading lots.json: {e}")
        # Return an empty list if the file is missing or invalid
        return jsonify([])

if __name__ == "__main__":
    # The API will run on the default port 5000
    app.run(debug=True)