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
def log_full_request():
    from pprint import pformat  # for pretty-printing dicts

    log_data = {
        "method": request.method,
        "url": request.url,
        "base_url": request.base_url,
        "path": request.path,
        "full_path": request.full_path,
        "query_string": request.query_string.decode(),
        "headers": dict(request.headers),
        "content_type": request.content_type,
        "content_length": request.content_length,
        "mimetype": request.mimetype,
        "remote_addr": request.remote_addr,
        "user_agent": str(request.user_agent),
        "cookies": request.cookies,
        "args (query params)": request.args.to_dict(),
        "form data": request.form.to_dict(),
        "json body": request.get_json(silent=True),
        "files": list(request.files.keys())
    }

    app.logger.info(f"Full Request Info:\n{pformat(log_data)}")

@app.route('/')
def home():
    image_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if allowed_file(f)]
    
    # Display images in HTML
    image_tags = ''.join([f'<img src="/uploads/{f}" alt="{f}" width="200" height="auto">' for f in image_files])
    return f'<h1>Uploaded Images</h1>{image_tags}'

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# Add the CGI-like route here for the AXIS camera
@app.route('/cgi-bin/notify.cgi', methods=['GET', 'POST'])
def cgi_notify():
    # Log incoming request details
    app.logger.info(f"Request Headers: {request.headers}")
    app.logger.info(f"Request Content-Type: {request.content_type}")

    if request.method == 'GET':
        app.logger.info("Camera sent a GET request to /cgi-bin/notify.cgi")
        return jsonify({"message": "Camera connected successfully. Use POST to upload images."}), 200

    # Try to extract filename from Content-Disposition header
    filename = None
    content_disposition = request.headers.get('Content-Disposition', '')
    if content_disposition:
        match = re.search(r'filename="(.+?)"', content_disposition)
        if match:
            filename = secure_filename(match.group(1))

    # Handle multipart/form-data uploads
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            app.logger.error('No selected file')
            return 'No selected file', 400
        
        if not filename:
            filename = secure_filename(file.filename)  # Use provided filename if no header filename

        image_data = file.read()  # Read image data from file object

    # Handle raw binary image upload (for camera)
    elif request.content_type and request.content_type.startswith('image/'):
        image_data = request.data  # Read raw image bytes from request body
        if not filename:
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
    original_image_path = os.path.join(app.config['UPLOAD_FOLDER'], f'original-{filename}')
    os.replace(image_path, original_image_path)

    # Create a new image that is resized and add watermark
    watermark_filename = f"{filename.rsplit('.', 1)[0]}-watermarked.jpg"
    watermark_filepath = os.path.join(app.config['UPLOAD_FOLDER'], watermark_filename)

    # Open the image and apply resizing and watermark
    with Image.open(original_image_path) as img:
        # Resize the image to 800x468
        img_resized = img.resize((800, 468))

        # Calculate new height with the black bar
        new_height = img_resized.height + 20

        # Create a new image with the added space
        new_img = Image.new("RGB", (img_resized.width, new_height), "black")  # Black background

        # Paste the resized image onto the new image (at the top)
        new_img.paste(img_resized, (0, 0))

        draw = ImageDraw.Draw(new_img)

        # Load a larger font for the timestamp
        try:
            large_font = ImageFont.truetype("arial.ttf", size=14)  # Adjust path and font as needed.
        except IOError:
            print("Timestamp font not found. Using default.")
            large_font = ImageFont.load_default()

        # Load a font for "DriveBC.ca" (can be the same or different)
        try:
            drivebc_font = ImageFont.truetype("arial.ttf", size=14)  # Adjust path and font size as needed.
        except IOError:
            print("DriveBC font not found. Using default.")
            drivebc_font = ImageFont.load_default()

        timestamp = datetime.datetime.now().strftime("%b %d, %Y %I:%M:%S %p")

        # Timestamp position (right side)
        timestamp_bbox = draw.textbbox((0, 0), timestamp, font=large_font)
        timestamp_width = timestamp_bbox[2] - timestamp_bbox[0]
        timestamp_height = timestamp_bbox[3] - timestamp_bbox[1]
        timestamp_position = (new_img.width - timestamp_width - 10, new_img.height - timestamp_height - 8)

        # "DriveBC.ca" position (left side)
        drivebc_bbox = draw.textbbox((0, 0), "DriveBC.ca", font=drivebc_font)
        drivebc_width = drivebc_bbox[2] - drivebc_bbox[0]
        drivebc_height = drivebc_bbox[3] - drivebc_bbox[1]
        drivebc_position = (10, new_img.height - drivebc_height - 8)  # 10px from left and bottom

        draw.text(timestamp_position, timestamp, fill="white", font=large_font)
        draw.text(drivebc_position, "DriveBC.ca", fill="white", font=drivebc_font)

        new_img.save(watermark_filepath)

    # Log successful file upload and processing
    app.logger.info(f'File uploaded and processed successfully: {watermark_filename}')

    return 'File uploaded and processed successfully', 200


if __name__ == '__main__':
    app.run(debug=True)
