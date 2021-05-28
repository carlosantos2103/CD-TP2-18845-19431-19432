import json
from flask.helpers import send_from_directory
from flask import Flask, jsonify, abort, request, make_response, render_template
from flask_httpauth import HTTPBasicAuth
from flask_cors import CORS
from flask_socketio import SocketIO, emit, send, join_room, leave_room

app = Flask(__name__, static_url_path="", template_folder='templates')
CORS(app)
app.config['SECRET_KEY'] = 'secret'
socketio = SocketIO(app)
auth = HTTPBasicAuth()

users = [
    {
        'username': 'ricardo',
        'password': '18845'
    },
]

channels = [
    {
        'channel_id': 1,
        'name': '',
        'users': ['miguel'],
    },
]

messages = [
    {
        'channel':  1,
        'sms': '',
        'username': '',
        'send': [],
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

# Ler os dados dos ficheiros
channels = read_file('channels.txt')

# Página Principal
@app.route('/',  methods=['GET'])
def root():
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



# Mostra as mensagens que o canal possui
@app.route('/get_messages/<int:channel_id>',  methods=['GET'])
@auth.login_required
def get_messages(channel_id):
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

# Registar um canal
@app.route('/create_channel', methods=['POST'])
@auth.login_required
def create_channel():
    username = auth.current_user()
    if not request.json or 'name' not in request.json:
        abort(400)

    dic = json.loads(request.json)
    new_channel = {
        'channel_id': len(channels) + 1,
        'name': str(dic['name']),
        'users': [ username ],
    }
    # Adiciona outro canal aos ja existentes
    channels.append(new_channel)
    # Escreve os a estrutura de dados num ficheiro
    write_file('channels.txt', channels)
    return jsonify(channels), 201

# Inserir um utilizador num canal
@app.route('/insert_user', methods=['POST'])
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

# Enviar mensagem para um canal
@app.route('/send_message/<int:channel_id>', methods=['POST'])
def send_message(channel_id):
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

# Apaga o utilizador caso exista do canal
@app.route('/remove_user/<int:channel_id>', methods=['DELETE'])
def remove_user(channel_id):
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

@socketio.on('message')
def handle_message(data):
    print('received message: ' + data)

@socketio.on('my event')
def handle_my_custom_event(json):
    print('received json: ' + str(json))

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    print(username)
    emit('sss', {'data': username + ' has entered the room.'}, to=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    send(username + ' has left the room.', to=room)

@socketio.on('connect')
def test_connect():
    emit('my response', {'data': 'Connected'})

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=True)