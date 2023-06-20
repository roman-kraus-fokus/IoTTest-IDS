from flask import Flask, request
from werkzeug.utils import secure_filename
import os

upload_folder = os.getcwd() + "/uploads/"

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = upload_folder

@app.route('/ids/upload_scap', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "no file in request", 400

    file = request.files['file']
    if file.filename == '':
        return 'no file_name in request', 400

    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return 'file sucessfull uploaded!', 200

if __name__ == "__main__":
    app.run(port=80, debug=True)
    