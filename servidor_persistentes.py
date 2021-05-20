import json
import six
from flask import Flask, jsonify, abort, request, make_response, url_for
from flask_httpauth import HTTPBasicAuth
from flask_cors import CORS

app = Flask(__name__, static_url_path="")
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


# Enviar uma mensagem para um utilizador - Feito
# Consultar as mensagens entretanto recebidas na caixa de mensagens. - Feito
# Distinguir entre as mensagens já lidas e as mensagens novas. - (+-) Feito
# Uma mensagem enviada para um grupo é equivalente a ser enviada para cada
# utilizador membro desse grupo.
# Listar o número de mensagens na caixa de mensagens
# Remover uma mensagem da caixa de mensagens.

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

# Ler os dados do ficheiro
messages = read_file('messages.txt')

# Ler os dados do ficheiro
#users = read_file('users.txt')

# Envia uma mensagem para um utilizador ou para um grupo de utilizadores
@app.route('/send_messages',  methods=['POST'])
def send_messages():
    if not request.json or 'message' and 'receiver' and 'username' not in request.json:
        abort(400)

    request_users = str(request.json['receiver'])
    receivers = request_users.split(',')

    if len([user for user in users if user['username'] == str(request.json['username'])]) == 0:
        abort(404)
    # Adicionar os utilizadores a quem deve enviar a mensagem
    for receiver in receivers:
        if [user for user in users if user['username'] == receiver]:
            new_message = {
                'id_sms': len(messages) + 1,
                'sms': str(request.json['message']),
                'sender': str(request.json['username']),
                'receiver': receiver,
                'status': 'NR',
            }
            # Adiciona a estrutura principal
            messages.append(new_message)
    # Escreve em ficheiros
    write_file('messages.txt', messages)
    return jsonify(messages), 201

@app.route('/get_messages/', methods=['GET'])
def get_messages():
    if not request.json or 'username'not in request.json:
        abort(400)
    all_messages = []
    # Verificar se existe mensagens para o utilizador
    for message in messages:
        if message['receiver'] == str(request.json['username']) and message['status'] != 'D':
            # Lista de todas as mensagens (tanto lidas como nao)
            all_messages.append( { 'id_sms': message['id_sms'], 'sms': message['sms'], 'sender': message['sender'], 'status': message['status'] } )
    return jsonify(all_messages), 201

@app.route('/get_messages/<int:message_id>', methods=['GET'])
def get_message(message_id):
    if not request.json or 'username'not in request.json:
        abort(400)
    # Verificar se existe mensagens para o utilizador
    for message in messages:
        if message['receiver'] == str(request.json['username']) and message['status'] != 'D':
            # Alterar o estado para lido
            message['status'] = 'R'
            # Lista de todas as mensagens (tanto lidas como nao)
            return jsonify({'id_sms': message['id_sms'], 'sms': message['sms'], 'sender': message['sender']}), 201

    abort(404)

@app.route('/remove_message/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    if not request.json or 'username' not in request.json:
        abort(400)
    # Verificar se existe mensagens para o utilizador
    for message in messages:
        if message['id_sms'] == message_id:
            if message['receiver'] == request.json['username'] and message['status'] != 'D':
                # Remover a mensagem enviada
                message['status'] = 'D'
                return jsonify(messages), 201
            else:
                abort(404)
    abort(404)

if __name__ == '__main__':
    app.run(debug=True)