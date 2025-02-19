from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from PIL import Image, ImageFilter, ExifTags
import os
from prediction import predict_result  # Assuming this module contains prediction logic

app = Flask(__name__)

# Dummy user data for demonstration
users = {
    "user1": "password1",
    "user2": "password2"
}

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username in users and users[username] == password:
        # Authentication successful, redirect to index page
        return redirect(url_for('index'))
    else:
        # Authentication failed, render login page with error message
        return render_template('login.html', error='Invalid username or password')

@app.route('/index')
def index():
    return render_template('index.html')

# Configuration for uploading images for Exif processing
app.config['UPLOAD_FOLDER_EXIF'] = 'Uploads/exif'
# Configuration for uploading images for ELA processing
app.config['ELA_FOLDER'] = 'upload/ela'

def error_level_analysis(image_path, quality=90):
    # Open the image
    img = Image.open(image_path)
    # Convert the image to JPEG format with the given quality
    img_ela = img.convert('RGB').filter(ImageFilter.EDGE_ENHANCE_MORE).save('temp.jpg', 'JPEG', quality=quality)
    # Reopen the new JPEG image and convert it to ELA format
    ela_img = Image.open('temp.jpg').convert('L')
    return ela_img

# Routes for file upload and analysis
@app.route('/upload', methods=['POST'])
def upload():
    # Handle file upload logic here
    return jsonify({'status': 'success', 'message': 'File uploaded successfully'})

@app.route('/analyze', methods=['POST'])
def analyze():
    # Perform prediction when the analyze button is clicked
    prediction, confidence = predict_result(request.files.getlist('file'))
    return jsonify({'status': 'success', 'message': f'Prediction: {prediction}, Confidence: {confidence}%'})

# Routes for Exif processing
@app.route('/upload_exif', methods=['POST'])
def upload_exif():
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']
    
    if file.filename == '':
        return "No selected file"
    
    filename = os.path.join(app.config['UPLOAD_FOLDER_EXIF'], file.filename)
    file.save(filename)
    
    img = Image.open(filename)
    
    try:
        exif_data = img._getexif()
    except AttributeError:
        return "No EXIF data found"
    
    if exif_data:
        exif = {ExifTags.TAGS[k]: v for k, v in exif_data.items() if k in ExifTags.TAGS}
        return render_template('exif result.html', exif=exif)
    else:
        return "No EXIF data found"

@app.route('/analyze_ela', methods=['POST'])
def analyze_ela():
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']
    
    if file.filename == '':
        return "No selected file"
    
    filename = os.path.join(app.config['ELA_FOLDER'], file.filename)
    file.save(filename)

    ela_img = error_level_analysis(filename)
    # Save ELA image
    ela_path = os.path.join(app.config['ELA_FOLDER'], f'ela_{file.filename}')
    ela_img.save(ela_path)
    
    # Automatically trigger download
    try:
        return send_file(ela_path, as_attachment=True)
    except Exception as e:
        return str(e)

@app.route('/download_ela', methods=['GET'])
def download_ela():
    ela_path = request.args.get('ela_path')
    return send_file(ela_path, as_attachment=True)

@app.route('/close', methods=['POST'])
def close():
    # Handle closing the window if needed
    return jsonify({'status': 'success', 'message': 'Window closed'})

if __name__ == '__main__':
    app.run(debug=True)
