import json
import os
from flask.helpers import send_from_directory
from flask import Flask, jsonify, abort, request, make_response, render_template, send_file
from flask_httpauth import HTTPBasicAuth
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os.path, time, datetime

app = Flask(__name__, static_url_path="", template_folder='templates')
CORS(app)
auth = HTTPBasicAuth()

LIFE_TIME = 365 #days
UPLOAD_PATH = "Workspaces/"

months = {
        'Jan': 1,
        'Feb': 2,
        'Mar': 3,
        'Apr': 4,
        'May': 5,
        'Jun': 6,
        'Jul': 7,
        'Aug': 8,
        'Sep': 9,
        'Oct': 10,
        'Nov': 11,
        'Dec': 12,
    }

# Nota: Registar autenticacoes e registar utilizadores e assim

@auth.get_password
def get_password(username):
    for user in users:
        if username == user['username']:
            return user['password']
    return None

@auth.error_handler
def unauthorized():
    # return 403 instead of 401 to prevent browsers from displaying the default
    # auth dialog
    return make_response(jsonify({'error': 'Unauthorized access'}), 403)

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

users = [
    {
        'username': 'ricardo',
        'password': '18845'
    },
]

def write_file(filename, data):
    with open(filename, 'w') as file:
        file.truncate(0)
        json.dump(data, file)
        file.close()

def read_file(filename):
    try:
        with open(filename, 'r') as file:
            try:
                content = json.load(file)
            except ValueError:
                return []
    except IOError as e:
        return []
    file.close()
    return content

def check_age(path):
    if os.path.exists(path):
        c = time.ctime(os.path.getctime(path))
        day = c[8:10]
        month = months[c[4:7]]
        year = c[-4:]

        file_date = datetime.datetime(int(year), int(month), int(day))
        now = datetime.datetime.now()
        difference = file_date - now

        if abs(difference.days) > LIFE_TIME:
            os.remove(path)

# Ler os dados dos ficheiros
users = read_file('users.txt')

# Página Principal
@app.route('/',  methods=['GET'])
def root():
    if auth.current_user() != None:
        return send_from_directory("templates", "index.html")
    return render_template("login.html")

# Obtem ficheiros
@app.route('/templates/<string:file_name>',  methods=['GET'])
def get_file(file_name):
    return send_from_directory("templates", file_name)

# Página após o login
@app.route('/login',  methods=['GET'])
@auth.login_required
def login():
    return send_from_directory("templates", "index.html")

@app.route('/upload',  methods=['POST'])
@auth.login_required
def upload():
    if 'file' not in request.files:
        abort(400)
    username = auth.current_user()
    path = UPLOAD_PATH + username
    if not os.path.exists(path):
        os.makedirs(path)
    f = request.files['file']
    f.save(os.path.join(path, secure_filename(f.filename)))
    return jsonify("File saved"), 201

@app.route('/download/<string:file_name>',  methods=['GET'])
@auth.login_required
def download(file_name):
    username = auth.current_user()
    path = UPLOAD_PATH + username
    check_age(path)
    if not os.path.exists(path + "/" + file_name):
        abort(404)
    
    return send_from_directory(path, file_name, as_attachment=True)

@app.route('/delete/<string:file_name>',  methods=['DELETE'])
@auth.login_required
def delete(file_name):
    username = auth.current_user()
    path = UPLOAD_PATH + username + "/" + file_name
    check_age(path)
    if not os.path.exists(path):
        abort(404)

    os.remove(path)

    return jsonify("File removed"), 200

@app.route('/listfiles',  methods=['GET'])
@auth.login_required
def listfiles():
    username = auth.current_user()
    path = UPLOAD_PATH + username
    if not os.path.exists(path):
        abort(404)

    files = []
    for f in os.listdir(path):
        check_age(path + "/" + f)
        if os.path.isfile(os.path.join(path, f)):
            files.append(f)

    return jsonify(files), 200

if __name__ == '__main__':
    app.run(debug=True)