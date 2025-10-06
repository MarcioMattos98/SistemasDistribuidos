
from flask import Flask, request, jsonify, Response, render_template
from pymongo import MongoClient
from bson import json_util

app = Flask(__name__)

client = MongoClient('mongodb://localhost:27017/')
db = client['lista_contatos_db']
collection = db['contatos']


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/contatos', methods=['GET', 'POST', 'PUT', 'DELETE'])
def gerenciar_contatos():
    if request.method == 'GET':
        name = request.args.get('name')
        if name:
            contato = collection.find_one({'name': name})
            if contato:
                return Response(
                    json_util.dumps(contato),
                    mimetype='application/json'
                )
            else:
                return jsonify({'error': 'Contato não encontrado'}), 404
        else:
            contatos = list(collection.find({}))
            return Response(
                json_util.dumps(contatos),
                mimetype='application/json'
            )

    elif request.method == 'POST':
        data = request.get_json()
        if not data or 'name' not in data or 'email' not in data:
            return jsonify({'error': 'Dados inválidos. "name" e "email" são obrigatórios.'}), 400
        if collection.find_one({'name': data['name']}):
            return jsonify({'error': 'Contato com este nome já existe.'}), 409
        collection.insert_one(data)
        return jsonify({'success': f"Contato '{data['name']}' adicionado."}), 201

    elif request.method == 'PUT':
        data = request.get_json()
        if not data or 'name' not in data or 'email' not in data:
            return jsonify({'error': 'Dados inválidos. "name" e "email" são obrigatórios.'}), 400
        resultado = collection.update_one(
            {'name': data['name']},
            {'$set': {'email': data['email']}}
        )
        if resultado.matched_count > 0:
            return jsonify({'success': f"Contato '{data['name']}' atualizado."})
        else:
            return jsonify({'error': 'Contato não encontrado para atualizar.'}), 404

    elif request.method == 'DELETE':
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': '"name" é obrigatório para deletar.'}), 400
        resultado = collection.delete_one({'name': data['name']})
        if resultado.deleted_count > 0:
            return jsonify({'success': f"Contato '{data['name']}' removido."})
        else:
            return jsonify({'error': 'Contato não encontrado para remover.'}), 404

if __name__ == '__main__':
    app.run(debug=True)