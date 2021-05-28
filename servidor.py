import json, os, shutil
from flask.helpers import send_from_directory, send_file
from flask import Flask, jsonify, abort, request, make_response, render_template
from flask_httpauth import HTTPBasicAuth
from flask_cors import CORS
from flask_socketio import SocketIO, emit, send, join_room, leave_room
from werkzeug.utils import secure_filename
from utils import write_file, read_file, check_file_age

UPLOAD_PATH = "Workspaces/"

app = Flask(__name__, static_url_path="", template_folder='templates')
CORS(app)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app)
auth = HTTPBasicAuth()

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

# Ler os dados dos ficheiros
channels = read_file('channels')
messages = read_file('messages')
users = read_file('users')

# Página Principal
@app.route('/',  methods=['GET'])
def root():
    if auth.current_user() != None:
        return send_from_directory("templates", "index.html")
    return render_template("login.html")

# Obtem ficheiros
@app.route('/templates/<string:file_name>',  methods=['GET'])
def get_template_file(file_name):
    return send_from_directory("templates", file_name)

# Página após o login
@app.route('/login',  methods=['GET'])
@auth.login_required
def login():
    username = auth.current_user()
    for channel in channels:
        for user in channel['users']:
            print(user)
            if user == username:
                room = channel['channel_id']
                on_join(user)
                emit('new room message', {'data': username + ' has entered the room.'}, to=room)
                print('Client connected to room ' + channel['name']) 

    return send_from_directory("templates", "index.html")

def on_join(data):
    username = data
    room = 1
    join_room(room)
    print(username)
    emit('sss', {'data': username + ' has entered the room.'}, to=room)

#region 1 - MENSAGENS PERSISTENTES

@app.route('/messages/send_message',  methods=['POST'])
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

@app.route('/messages/get_messages', methods=['GET'])
@auth.login_required
def get_messages():
    username = auth.current_user()

    all_messages = []
    # Verificar se existe mensagens para o utilizador
    for message in messages:
        if message['receiver'] == username and message['status'] != 'D':
            # Lista de todas as mensagens (tanto lidas como nao)
            all_messages.append( { 'id_sms': message['id_sms'], 'sms': message['sms'], 'sender': message['sender'], 'status': message['status'] } )
    return jsonify(all_messages), 201

@app.route('/messages/get_messages/<int:message_id>', methods=['GET'])
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

@app.route('/messages/remove_message/<int:message_id>', methods=['DELETE'])
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

#endregion

#region 2 - MENSAGENS INSTANTANEAS

# Mostra as mensagens que o canal possui
@app.route('/channels/get_messages/<int:channel_id>',  methods=['GET'])
@auth.login_required
def get_channel_messages(channel_id):
    username = auth.current_user()
    channel = [channel for channel in channels if channel['channel_id'] == int(channel_id)]
    # Verificar se existe o canal
    if len(channel) == 0:
        abort(404)
    # Verificar se esse utilizador existe no canal
    for cha in channel:
        for user in cha['users']:
            # Verifica se existe esse utilizador
            if user == username:
                new_messages = []
                for message in messages:
                    if message['username'] != username:
                        new_message = {
                            'sms': str(message['sms']),
                            'username': username,
                        }
                        new_messages.append(new_message)

                # Vai a estrutura principal e acrecenta a lista dos enviados 'send' o username a quem enviou
                for message in messages:
                    if message['channel'] == int(channel_id):
                        send = [send for send in message['send'] if send == username ]
                        # Verifica se o user ja esta inserido na estrutura de dados (para n inserir repetidos)
                        if send == 0:
                            # Acrescenta o user na lista
                            message['send'].append(username)

                return jsonify(messages), 201
    abort(404)

# Inserir um utilizador num canal #SOCKETS
@app.route('/channels/insert_user', methods=['POST'])
def insert_user():
    if not request.json or 'channel_id' and 'username' not in request.json:
        abort(400)

    dic = json.loads(request.json)
    # Verificar se existe o canal
    channel = [channel for channel in channels if channel['channel_id'] == int(dic['channel_id'])]
    # Caso n exista o canal
    if len(channel) != 1:
        abort(404)

    user = [user for user in channel[0]['users'] if user == str(dic['username'])]
    # Caso n exista o utilizador
    if len(user) != 0:
        abort(404)

    for channel in channels:
        if channel['channel_id'] == int(dic['channel_id']):
            # Adiciona outro utilizador ao canal
            channel['users'].append(str(dic['username']))

    # Escreve os a estrutura de dados num ficheiro
    write_file('channels.txt', channels)
    return jsonify(channels), 201

# Enviar mensagem para um canal #SOCKETS
@app.route('/channels/send_message/<int:channel_id>', methods=['POST'])
def send_channel_message(channel_id):
    username = auth.current_user()
    if not request.json or 'message' not in request.json:
        abort(400)

    dic = json.loads(request.json)
    # Verifica se existe o canal
    channel = [ channel for channel in channels if channel['channel_id'] == int(channel_id) ]
    if len(channel) == 0:
        abort(404)

    user = [user for user in channel[0]['users'] if user == username]
    # Caso exista o utilizador
    if len(user) == 0:
        abort(404)

    # Criar a nova estrutura
    message = {
            'channel': int(channel_id),
            'sms': str(dic['message']),
            'username': username,
        }

    # Insere a nova mensagem na estrutura de dados
    messages.append(message)
    return jsonify(messages), 201

# Apaga o utilizador caso exista do canal #SOCKETS
@app.route('/channels/remove_user/<int:channel_id>', methods=['DELETE'])
def remove_channel_user(channel_id):
    if not request.json or 'username' not in request.json:
        abort(400)

    dic = json.loads(request.json)
    # Verifica se existe o canal indicado
    channel = [ channel for channel in channels if channel['channel_id'] == channel_id ]
    if len(channel) == 0:
        abort(404)

    for user in channel[0]['users']:
        if user == str(dic['username']):
            # Remover o utilizador
            channel[0]['users'].remove(user)
            # Escrever no ficheiro os dados
            write_file('channels.txt', channels)
            return jsonify(channels), 201
    # Caso nao exista o utilizador
    abort(404)

#endregion

#region 3 - FICHEIROS

@app.route('/files/upload',  methods=['POST'])
@auth.login_required
def upload():
    if 'file' not in request.files:
        print("NO FILE")
        abort(400)

    username = auth.current_user()
    path = UPLOAD_PATH + username
    if not os.path.exists(path):
        os.makedirs(path)

    f = request.files['file']
    f.save(os.path.join(path, secure_filename(f.filename)))
    return jsonify("File saved"), 201

@app.route('/files/download/<string:file_name>',  methods=['GET'])
@auth.login_required
def download(file_name):
    username = auth.current_user()
    path = UPLOAD_PATH + username
    check_file_age(path)
    if not os.path.exists(path + "/" + file_name):
        abort(404)
    
    #return send_from_directory(path, file_name, as_attachment=True, mimetype='image/jpg')
    return send_file(path + "/" + file_name, as_attachment=True, attachment_filename='')

@app.route('/files/delete/<string:file_name>',  methods=['DELETE'])
@auth.login_required
def delete(file_name):
    username = auth.current_user()
    path = UPLOAD_PATH + username + "/" + file_name
    check_file_age(path)
    if not os.path.exists(path):
        abort(404)

    os.remove(path)

    return jsonify("File removed"), 200

@app.route('/files/list',  methods=['GET'])
@auth.login_required
def listfiles():
    username = auth.current_user()
    path = UPLOAD_PATH + username
    if not os.path.exists(path):
        abort(404)

    files = []
    for f in os.listdir(path):
        check_file_age(path + "/" + f)
        if os.path.isfile(os.path.join(path, f)):
            files.append(f)

    return jsonify(files), 200

#endregion

#region 4 - UTILIZADORES

@auth.get_password
def get_password(username):
    for user in users:
        if username == user['username']:
            return user['password']
    return None

@app.route('/users/create_account',  methods=['POST'])
def create_account():
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
        'password': str(dic['password']),
        'admin': False,
    }
    # Adiciona a estrutura princiapl o utilizador
    users.append(new_user)
    # Escreve em ficheiros a estrutura de dados
    write_file('users', users)
    return jsonify('Inserido com sucesso'), 201

@app.route('/users/add',  methods=['POST'])
@auth.login_required
def add_user():
    username = auth.current_user()
    permission = get_permission(username)

    if not request.json or 'username' and 'password' and 'admin' not in request.json or not permission:
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
        'password': str(dic['password']),
        'admin': bool(dic['admin']),
    }
    # Adiciona a estrutura princiapl o utilizador
    users.append(new_user)
    # Escreve em ficheiros a estrutura de dados
    write_file('users', users)
    return jsonify('Inserido com sucesso'), 201

@app.route('/users/change_password',  methods=['PUT'])
@auth.login_required
def change_password():
    username = auth.current_user()
    permission = get_permission(username)

    if not request.json or 'username' and 'password' not in request.json or not permission:
        abort(400)

    dic = json.loads(request.json)
    # Verificar se existe esse utilizador
    user = [user for user in users if user['username'] == str(dic['username'])]
    # Alterar password
    if len(user) != 0 and str(dic['password']) != "":
        user[0]['password'] = str(dic['password'])
    else: 
        abort(404)

    # Escreve em ficheiros a estrutura de dados
    write_file('users', users)
    return jsonify('Alterado com sucesso'), 201

@app.route('/users/remove',  methods=['DELETE'])
@auth.login_required
def remove_user():
    username = auth.current_user()
    permission = get_permission(username)

    if not request.json or 'username' not in request.json or not permission:
        abort(400)

    dic = json.loads(request.json)
    
    for user in users:
        if user['username'] == str(dic['username']):
            users.remove(user)
            path = UPLOAD_PATH + username
            if os.path.exists(path):
                shutil.rmtree(path)
            write_file('users', users)
            return jsonify('Removido com sucesso'), 201
            
    abort(404)

# Registar um canal
@app.route('/channels/create_channel', methods=['POST'])
@auth.login_required
def create_channel():
    username = auth.current_user()
    permission = get_permission(username)

    if not request.json or 'name' not in request.json or not permission:
        abort(400)

    dic = json.loads(request.json)
    new_channel = {
        'channel_id': len(channels) + 1,
        'name': str(dic['name']),
        'users': [ ],
    }

    # Adiciona outro canal aos ja existentes
    channels.append(new_channel)
    # Escreve os a estrutura de dados num ficheiro
    write_file('channels', channels)
    return jsonify(channels), 201

def get_permission(username):
    for user in users:
        if username == user['username']:
            return user['admin']

#endregion

if __name__ == '__main__':
    #app.run(debug=True)
    socketio.run(app, debug=True)