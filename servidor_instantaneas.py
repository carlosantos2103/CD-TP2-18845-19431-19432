import six
import json
from flask import Flask, jsonify, abort, request, make_response, url_for
from flask_httpauth import HTTPBasicAuth
from flask_cors import CORS

app = Flask(__name__, static_url_path="")
CORS(app)
auth = HTTPBasicAuth()

# TODO: Fazer o login

@auth.get_password
def get_password(username):
    for user in login:
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

login = [
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

# Mostra as mensagens que o canal possui
@app.route('/see_messages/<int:channel_id>',  methods=['GET'])
def see_messages(channel_id):
    if not request.json or 'username' not in request.json:
        abort(400)
    channel = [channel for channel in channels if channel['channel_id'] == int(channel_id)]
    # Verificar se existe o canal
    if len(channel) == 0:
        abort(404)
    # Verificar se esse utilizador existe no canal
    for cha in channel:
        for user in cha['users']:
            # Verifica se existe esse utilizador
            if user == str(request.json['username']):
                new_messages = []
                for message in messages:
                    if message['username'] != str(request.json['username']):
                        new_message = {
                            'sms': str(message['sms']),
                            'username': str(message['username']),
                        }
                        new_messages.append(new_message)

                # Vai a estrutura principal e acrecenta a lista dos enviados 'send' o username a quem enviou
                for message in messages:
                    if message['channel'] == int(channel_id):
                        send = [send for send in message['send'] if send == str(request.json['username']) ]
                        # Verifica se o user ja esta inserido na estrutura de dados (para n inserir repetidos)
                        if send == 0:
                            # Acrescenta o user na lista
                            message['send'].append(request.json['username'])

                return jsonify(messages), 201
    abort(404)

# Registar num canal
@app.route('/create_register', methods=['POST'])
def create_register():
    if not request.json or 'name' and 'username' not in request.json:
        abort(400)
    new_channel = {
        'channel_id': len(channels) + 1,
        'name': str(request.json['name']),
        'users': [ str(request.json['username']) ],
    }
    # Adiciona outro canal aos ja existentes
    channels.append(new_channel)
    # Escreve os a estrutura de dados num ficheiro
    write_file('channels_data', channels)
    return jsonify(channels), 201


# Inserir um utilizador num canal
@app.route('/insert_user', methods=['POST'])
def insert_user():
    if not request.json or 'channel_id' and 'username' not in request.json:
        abort(400)

    # Verificar se existe o canal
    channel = [channel for channel in channels if channel['channel_id'] == int(request.json['channel_id'])]
    # Caso n exista o canal
    if len(channel) != 1:
        abort(404)

    user = [user for user in channel[0]['users'] if user == str(request.json['username'])]
    # Caso n exista o utilizador
    if len(user) != 0:
        abort(404)

    for channel in channels:
        if channel['channel_id'] == int(request.json['channel_id']):
            # Adiciona outro utilizador ao canal
            channel['users'].append(str(request.json['username']))

    # Escreve os a estrutura de dados num ficheiro
    write_file('channels_data', channels)
    return jsonify(channels), 201

@app.route('/send_message/<int:channel_id>', methods=['POST'])
def send_message_channel(channel_id):
    if not request.json or 'message' and 'username' not in request.json:
        abort(400)
    # Verifica se existe o canal
    channel = [ channel for channel in channels if channel['channel_id'] == int(channel_id) ]
    if len(channel) == 0:
        abort(404)

    user = [user for user in channel[0]['users'] if user == str(request.json['username'])]
    # Caso exista o utilizador
    if len(user) == 0:
        abort(404)

    # Criar a nova estrutura
    message = {
            'channel': int(channel_id),
            'sms': str(request.json['message']),
            'username': str(request.json['username']),
        }

    # Insere a nova mensagem na estrutura de dados
    messages.append(message)
    return jsonify(messages), 201

# Apaga o utilizador caso exista do canal
@app.route('/remove_user/<int:channel_id>', methods=['DELETE'])
def remove_user(channel_id):
    if not request.json or 'username' not in request.json:
        abort(400)

    # Verifica se existe o canal indicado
    channel = [ channel for channel in channels if channel['channel_id'] == channel_id ]
    if len(channel) == 0:
        abort(404)

    for user in channel[0]['users']:
        if user == request.json['username']:
            # Remover o utilizador
            channel[0]['users'].remove(user)
            # Escrever no ficheiro os dados
            write_file('channels_data', channels)
            return jsonify(channels), 201
    # Caso nao exista o utilizador
    abort(404)

if __name__ == '__main__':
    app.run(debug=True)