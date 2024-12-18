from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
from google.cloud import storage
import os

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)  # Enable Cross-Origin Resource Sharing

# Configure Google Cloud Storage
BUCKET_NAME = "photocloud-img-process-bucket"
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

UPLOAD_IMAGE_URL = "https://us-central1-photocloud-443915.cloudfunctions.net/upload_image"

# PROCESS_IMAGE_URL = "https://us-central1-photocloud-443915.cloudfunctions.net/process_image"

@app.route('/')
def index():
    """Render the main page."""
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload_image():
    """Handle image upload by calling the Cloud Function."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    filter_option = request.form['filter']  # filter is part of form data, not file
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        print(filter_option)
        # Upload the file with the correct 'files' format
        files = {'file': (file.filename, file.stream, file.mimetype)}
        # Include the filter option in form data
        data = {'filter': filter_option}
        
        response = requests.post(UPLOAD_IMAGE_URL, files=files, data=data)  # Send the filter option as form data
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/process', methods=['POST'])
def process_image():
    """Handle image processing by calling the Cloud Function."""
    data = request.get_json()
    if not data or 'image_url' not in data or 'filter_type' not in data:
        return jsonify({'error': 'Invalid request'}), 400

    image_url = data['image_url']
    filter_type = data['filter_type']

    try:
        # Send the request to the Cloud Function
        response = requests.post(PROCESS_IMAGE_URL, json={
            "image_url": image_url,
            "filter_type": filter_type
        })

        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/processed-images', methods=['GET'])
def list_processed_images():
    """List all processed images and render them in the frontend."""
    try:
        blobs = bucket.list_blobs(prefix="processed/")  # List blobs with 'processed/' prefix
        processed_images = [blob.public_url for blob in blobs if blob.name.endswith(('jpg', 'jpeg', 'png'))]

        return render_template("processed_images.html", images=processed_images)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def main(request):
    """Google Cloud Function entry point."""
    return app(request)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host="0.0.0.0", port=port)
