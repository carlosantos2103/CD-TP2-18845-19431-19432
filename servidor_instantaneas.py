import six
from flask import Flask, jsonify, abort, request, make_response, url_for
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__, static_url_path="")
auth = HTTPBasicAuth()


# TODO: ver aqui as excecoes https://werkzeug.palletsprojects.com/en/1.0.x/exceptions/
# TODO: Fazer o login?

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
    {
        'username': 'miguel',
        'password': '12345'
    }
]

channels = [
    {
        'channel_id': 1,
        'users': ['miguel'],
    },
    {
        'channel_id': 12,
        'users': ['ricardo'],
    },
]

messages = [
    {
        'channel':  1,
        'sms': '',
        'username': '',
        'send': [],
    },
    {
        'channel':  12,
        'sms': '',
        'username': '',
        'send': [],
    },
]

def write_channel_files(filename, data):
    with open(filename, 'w') as file:
        file.truncate(0)
        for f in data:
            file.write(f'''channel: {f['channel_id']} \n''')
            for user in f['users']:
                file.write(f'''-> user: {user} \n''')
        file.close()

def read_channel_files(filename):
    with open(filename, 'w') as file:
        content = file.read()
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

# Registar num canal um utilizador
@app.route('/create_register', methods=['POST'])
@auth.login_required
def create_register():
    if not request.json or 'channel' and 'username' not in request.json:
        abort(400)

    # Verifica se existe o canal
    channel = [channel for channel in channels if channel['channel_id'] == int(request.json['channel'])]
    # Caso nao exista faz um canal novo
    if len(channel) == 0:
        new_channel1 = {
            'channel_id': int(request.json['channel']),
            'users': [str(request.json['username'])],
        }
        channels.append(new_channel1)
        # Escreve os a estrutura de dados num ficheiro
        write_channel_files('channels_data', channels)
        return jsonify(channels), 201

    # Caso ja exista adiciona o utilizador a lista de utilizadores do canal
    for cha in channel:
        for user in cha['users']:
            # Verifica se existe esse utilizador
            if user == str(request.json['username']):
                abort(404)

    new_canal = {
    'channel_id': int(request.json['channel']),
    'users': cha['users'],
    }
    new_canal['users'].append(request.json['username'])

    delete_channel(channels, int(request.json['channel']))
    channels.append(new_canal)
    # Escreve os a estrutura de dados num ficheiro
    write_channel_files('channels_data', channels)
    return jsonify(channels), 201

# Funcao auxliar para apagar o canal TODO: tentar substiuir por uma funcao imperativa -> channel = [channel for channel in channels if channel['channel_id'] == int(request.json['channel'])]
def delete_channel(canal, id):
    for channel in canal:
        if channel['channel_id'] == int(id):
            canal.remove(channel)

@app.route('/send_message/<int:channel_id>', methods=['POST'])
@auth.login_required
def send_message_channel(channel_id):
    if not request.json or 'message' and 'username' not in request.json:
        abort(400)
    # Verifica se existe o canal
    channel = [ channel for channel in channels if channel['channel_id'] == int(channel_id) ]
    if len(channel) == 0:
        abort(404)
    # TODO: alguma verificacao precisa ser feita?
    # Criar a nova estrutura
    message = {
            'channel': int(channel_id),
            'sms': str(request.json['message']),
            'username': str(request.json['username']),
            'send': [],
        }

    # Insere a nova mensagem na estrutura de dados
    messages.append(message)
    return jsonify(messages), 201

# Apaga o utilizador caso exista do canal
@app.route('/cancel_channel/<int:channel_id>', methods=['DELETE'])
def cancel_channel(channel_id):
    if not request.json or 'username' not in request.json:
        abort(400)

    channel = [ channel for channel in channels if channel['channel_id'] == channel_id ]
    # Verifica se existe o canal indicado
    if len(channel) == 0:
        abort(404)
    for cha in channel:
        for user in cha['users']:
            if user == request.json['username']:
                # Remover o utilizador
                cha['users'].remove(user)
                # Escrever no ficheiro os dados
                write_channel_files('channels_data', channels)
                return jsonify(channels), 201
    # Caso nao exista o utilizador
    abort(404)

if __name__ == '__main__':
    app.run(debug=True)