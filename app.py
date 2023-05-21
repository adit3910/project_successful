from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
import cv2
from fpdf import FPDF
import face_recognition

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Function to check if the file has an allowed extension
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Function to capture live image from video
def capture_image():
    video_capture = cv2.VideoCapture(0)
    ret, frame = video_capture.read()
    if ret:
        cv2.imwrite(os.path.join(app.config['UPLOAD_FOLDER'], 'live_image.jpg'), frame)
    video_capture.release()

# Function to compare the captured image with uploaded images
def compare_images(captured_image_path, document_paths):

    captured_image = face_recognition.load_image_file(captured_image_path)
    captured_encoding = face_recognition.face_encodings(captured_image)

    if len(captured_encoding) == 0:
        # No faces detected in the captured image
        return False, []

    matched_images = []

    for document_path in document_paths:
        document_image = face_recognition.load_image_file(document_path)
        document_encoding = face_recognition.face_encodings(document_image)

        if len(document_encoding) == 0:
            # No faces detected in the document image
            continue

        # Compare the face encodings
        match = face_recognition.compare_faces(document_encoding, captured_encoding[0])
        if match[0]:
            matched_images.append(document_path)

    return len(matched_images) > 0, matched_images

# Function to create a PDF with watermarked images
def create_pdf(images):
    pdf = FPDF()
    for image in images:
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(40, 10, 'Verified by BHARGAV')
        pdf.image(image, x=10, y=20, w=180)
    pdf.output('result.pdf')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/capture')
def capture():
    capture_image()
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
def upload():
    # Check if a file is uploaded
    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']

    # Check if the file is allowed
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        captured_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'live_image.jpg')
        document_paths = [file_path]

        match, matched_images = compare_images(captured_image_path, document_paths)

        if match:
            images = [captured_image_path] + matched_images
            create_pdf(images)
            return redirect(url_for('result'))
        else:
            return render_template('result.html', message='No match found')

    return redirect(url_for('index'))
 
@app.route('/result')
def result():
    return render_template('result.html', message='Verification successful')

if __name__ == '__main__':
    app.run()
