from flask import Flask, request, jsonify, send_from_directory
from flask_httpauth import HTTPBasicAuth
from PIL import Image, ImageDraw, ImageFont
import os
import logging
import datetime
from werkzeug.utils import secure_filename

# Initialize Flask app and Basic Auth
app = Flask(__name__)
auth = HTTPBasicAuth()

# Configure logging to display messages at INFO level and above
logging.basicConfig(level=logging.INFO)

# Set the upload folder where images will be saved
UPLOAD_FOLDER = '/tmp/uploads'  # Update to a writable directory
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

@app.before_request
def log_request():
    app.logger.info(f"Request Method: {request.method}, Path: {request.path}")
    app.logger.info(f"Request Headers: {request.headers}")

@app.route('/')
def home():
    image_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if allowed_file(f)]
    
    # Option 1: Return filenames as JSON
    # return jsonify(image_files)
    
    # Option 2: Display images in HTML
    image_tags = ''.join([f'<img src="/uploads/{f}" alt="{f}" width="200" height="auto">' for f in image_files])
    return f'<h1>Uploaded Images</h1>{image_tags}'

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


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
        original_filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(original_filepath)

        # Keep a copy of the original image
        original_image_path = os.path.join(app.config['UPLOAD_FOLDER'], f'original_{file.filename}')
        os.rename(original_filepath, original_image_path)

        # Create a new image that is resized and add watermark
        watermark_filename = f"{file.filename.rsplit('.', 1)[0]}-watermarked.jpg"
        watermark_filepath = os.path.join(app.config['UPLOAD_FOLDER'], watermark_filename)
        
        # Open the image and apply resizing and watermark
        with Image.open(original_image_path) as img:
            # Resize the image to 800x468
            img_resized = img.resize((800, 468))

            # Create a watermark with the current timestamp
            draw = ImageDraw.Draw(img_resized)
            font = ImageFont.load_default()  # You can choose a different font here if desired
            
            # Add watermark text at the bottom
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Use textbbox (bounding box for text) instead of textsize
            bbox = draw.textbbox((0, 0), timestamp, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Position the watermark at the bottom-right
            position = (img_resized.width - text_width - 10, img_resized.height - text_height - 10)
            
            draw.text(position, timestamp, fill="white", font=font)

            # Save the new image with watermark
            img_resized.save(watermark_filepath)

        # Log successful file upload and processing
        app.logger.info(f'File uploaded and processed successfully: {watermark_filename}')

        # Return a success message
        return jsonify({'message': 'File uploaded and processed successfully', 'filename': watermark_filename}), 200
    else:
        app.logger.error(f'Invalid file type: {file.filename}')
        return jsonify({'error': 'Invalid file type'}), 400


# Add the CGI-like route here for the AXIS camera
@app.route('/cgi-bin/notify.cgi', methods=['GET', 'POST'])
def cgi_notify():
    # Log incoming request details
    app.logger.info(f"Request Headers: {request.headers}")
    app.logger.info(f"Request Content-Type: {request.content_type}")

    if request.method == 'GET':
        app.logger.info("Camera sent a GET request to /cgi-bin/notify.cgi")
        return jsonify({"message": "Camera connected successfully. Use POST to upload images."}), 200

    # Check if request is a standard multipart form upload
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            app.logger.error('No selected file')
            return 'No selected file', 400
        
        filename = secure_filename(file.filename)
        image_data = file.read()  # Read image data from the file object

    # Handle raw binary image upload (for camera)
    elif request.content_type and request.content_type.startswith('image/'):
        image_data = request.data  # Read raw image bytes from request body
        filename = f"upload_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        app.logger.info(f"Camera uploaded raw image, saving as {filename}")

    else:
        app.logger.error('No file part in the request')
        return 'No file part', 400

    # Save the image
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    with open(image_path, 'wb') as f:
        f.write(image_data)

    # Keep a copy of the original image
    original_image_path = os.path.join(app.config['UPLOAD_FOLDER'], f'original_{filename}')
    os.rename(image_path, original_image_path)

    # Create a new image that is resized and add watermark
    watermark_filename = f"{filename.rsplit('.', 1)[0]}-watermarked.jpg"
    watermark_filepath = os.path.join(app.config['UPLOAD_FOLDER'], watermark_filename)

    # Open the image and apply resizing and watermark
    with Image.open(original_image_path) as img:
        # Resize the image to 800x468
        img_resized = img.resize((800, 468))

        # Create a watermark with the current timestamp
        draw = ImageDraw.Draw(img_resized)
        font = ImageFont.load_default()  # Change this if needed
        
        # Add watermark text at the bottom
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        bbox = draw.textbbox((0, 0), timestamp, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = (img_resized.width - text_width - 10, img_resized.height - text_height - 10)
        draw.text(position, timestamp, fill="white", font=font)

        # Save the new image with watermark
        img_resized.save(watermark_filepath)

    # Log successful file upload and processing
    app.logger.info(f'File uploaded and processed successfully: {watermark_filename}')

    return 'File uploaded and processed successfully', 200

if __name__ == '__main__':
    app.run(debug=True)
