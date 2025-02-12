from flask import Flask, request, jsonify
from flask_httpauth import HTTPBasicAuth
import os
import logging

# Initialize Flask app and Basic Auth
app = Flask(__name__)
auth = HTTPBasicAuth()

# Configure logging to display messages at INFO level and above
logging.basicConfig(level=logging.INFO)

# Set the upload folder where images will be saved
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Define the allowed extensions (for image files)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Dummy users data (replace with a database or more secure approach in production)
users = {
    "admin": "password123",
    "user1": "mypassword"
}

# Verify username and password
@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username
    else:
        app.logger.error(f"Unauthorized access attempt with username: {username}")
        return None  # Will trigger a 401 Unauthorized response

@app.route('/')
def home():
    return 'Image Upload API'

@app.route('/upload', methods=['POST'])
@auth.login_required  # Protect this route with Basic Authentication
def upload_file():
    # Check if the request contains a file
    if 'file' not in request.files:
        app.logger.error('No file part in the request')
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    
    # If no file is selected
    if file.filename == '':
        app.logger.error('No selected file')
        return jsonify({'error': 'No selected file'}), 400
    
    # Check if the file has an allowed extension
    if file and allowed_file(file.filename):
        # Save the file to the upload folder
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        # Log successful file upload
        app.logger.info(f'File uploaded successfully: {file.filename}')
        
        # Return a success message
        return jsonify({'message': 'File uploaded successfully', 'filename': file.filename}), 200
    else:
        app.logger.error(f'Invalid file type: {file.filename}')
        return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(debug=True)
