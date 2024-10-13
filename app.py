import os
import boto3
import cv2
import torch
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/upload_images'
app.config['RESULT_FOLDER'] = 'static/result_images'
app.secret_key = 'your_secret_key'

# AWS S3 Configuration
s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('AWS_ACCESS_KEY_PASSWORD'),
    region_name='ap-south-1'
)
BUCKET_NAME = 'mycapstone-imagebucket'

# YOLOv7 model loading
WEIGHTS_PATH = 'yolov7_weights/yolov7.pt'

if not os.path.exists(WEIGHTS_PATH):
    raise FileNotFoundError(f"Model weights file not found: {WEIGHTS_PATH}")

model = torch.hub.load('WongKinYiu/yolov7', 'custom', WEIGHTS_PATH)

# Ensure upload and result folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

# Function to process the image with YOLOv7
def process_image(image_path, filename):
    img = cv2.imread(image_path)

    if img is None:
        raise ValueError("Image not loaded properly. Please check the image path or format.")
    
    img = img.copy()  # Ensure the image is writable
    
    # YOLOv7 inference
    results = model(img)
    detected_img = results.render()[0]  # Render bounding boxes

    # Save the processed image
    result_image_path = os.path.join(app.config['RESULT_FOLDER'], filename)
    cv2.imwrite(result_image_path, detected_img)
    
    # Upload result image to S3
    s3.upload_file(result_image_path, BUCKET_NAME, f'output_images/{filename}')

    return result_image_path

# Route for handling both upload and display of processed image on the same page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file:
            filename = secure_filename(file.filename)
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(upload_path)

            # Upload the image to S3 input_images folder
            s3.upload_file(upload_path, BUCKET_NAME, f'input_images/{filename}')

            # Process the image using YOLOv7
            result_path = process_image(upload_path, filename)
            
            # Provide the processed image URL to display on the same page
            processed_image_url = url_for('static', filename=f'result_images/{filename}')
            flash('Image uploaded and processed successfully!')
            return render_template('index.html', processed_image_url=processed_image_url)

        flash('An error occurred while uploading the image.')
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
