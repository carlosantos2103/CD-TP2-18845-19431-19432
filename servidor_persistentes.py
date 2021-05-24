import json
from flask.helpers import send_from_directory
from flask import Flask, jsonify, abort, request, make_response, render_template
from flask_httpauth import HTTPBasicAuth
from flask_cors import CORS

app = Flask(__name__, static_url_path="", template_folder='templates')
CORS(app)
auth = HTTPBasicAuth()

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

messages = [
    # {
    #    'id_sms':  1,
    #    'sms': '',
    #    'sender': '',
    #    'receiver': '',
    #    'status': 'NR' # Status: R- READ or NR - NOT READ or D - Delete
    # },
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

# Ler os dados dos ficheiros
messages = read_file('messages.txt')
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




# Cria novos utilizadores
@app.route('/add_user',  methods=['POST'])
def add_user():
    if not request.json or 'username' and 'password' not in request.json:
        abort(400)

    dic = json.loads(request.json)
    # Verificar se ja existe esse utilizador
    user = [user for user in users if user['username'] == str(dic['username'])]
    # Caso ja exista esse utilizador dar erro
    if len(user) != 0 and str(dic['username']) != "" and str(dic['password']) != "":
        abort(404)
    # Cria um novo utilizador
    new_user = {
        'username': str(dic['username']),
        'password': str(dic['password'])
    }
    # Adiciona a estrutura princiapl o utilizador
    users.append(new_user)
    # Escreve em ficheiros a estrutura de dados
    write_file('users.txt', users)
    #return jsonify('Inserido com sucesso'), 201
    return send_from_directory("templates", "index.html")

# Envia uma mensagem para um utilizador ou para um grupo de utilizadores
@app.route('/send_message',  methods=['POST'])
@auth.login_required
def send_message():
    username = auth.current_user()
    if not request.json or 'message' and 'receiver' not in request.json:
        abort(400)

    dic = json.loads(request.json)

    request_users = str(dic['receiver'])
    receivers = request_users.split(',')

    if len([user for user in users if user['username'] == username]) == 0:
        abort(404)
    # Adicionar os utilizadores a quem deve enviar a mensagem
    for receiver in receivers:
        if [user for user in users if user['username'] == receiver]:
            new_message = {
                'id_sms': len(messages) + 1,
                'sms': str(dic['message']),
                'sender': username,
                'receiver': receiver,
                'status': 'NR',
            }
            # Adiciona a estrutura principal
            messages.append(new_message)
    # Escreve em ficheiros
    write_file('messages.txt', messages)
    return jsonify(messages), 201

@app.route('/get_messages', methods=['GET'])
@auth.login_required
def get_messages():
    username = auth.current_user()
    print(username)
    all_messages = []
    # Verificar se existe mensagens para o utilizador
    for message in messages:
        if message['receiver'] == username and message['status'] != 'D':
            # Lista de todas as mensagens (tanto lidas como nao)
            all_messages.append( { 'id_sms': message['id_sms'], 'sms': message['sms'], 'sender': message['sender'], 'status': message['status'] } )
    return jsonify(all_messages), 201

@app.route('/get_message/<int:message_id>', methods=['GET'])
@auth.login_required
def get_message(message_id):
    username = auth.current_user()
    # Verificar se existe mensagens para o utilizador
    for message in messages:
        if message['receiver'] == username and message['status'] != 'D' and message['id_sms'] == message_id :
            # Alterar o estado para lido
            message['status'] = 'R'
            # Lista de todas as mensagens (tanto lidas como nao)
            return jsonify({'id_sms': message['id_sms'], 'sms': message['sms'], 'sender': message['sender']}), 201

    abort(404)

@app.route('/remove_message/<int:message_id>', methods=['DELETE'])
@auth.login_required
def remove_message(message_id):
    username = auth.current_user()
    # Verificar se existe mensagens para o utilizador
    for message in messages:
        if message['id_sms'] == message_id:
            if message['receiver'] == username and message['status'] != 'D':
                # Remover a mensagem enviada
                message['status'] = 'D'
                return jsonify(messages), 201
            else:
                abort(404)
    abort(404)


if __name__ == '__main__':
    app.run(debug=True)