from flask import Flask, jsonify, request
from redis import Redis, ConnectionError

app = Flask(__name__)

def connect_db():
    try:
        conexion = Redis(host='db-redis', port=6379, decode_responses=True)
        conexion.ping()
        print("Conectado a Redis")
        return conexion
    except ConnectionError as e:
        print("Error de conexión con Redis:", e)
        return None

def get_list(db, nombre_lista):
    lista = db.lrange(nombre_lista, 0, -1)
    return lista

@app.route('/', methods=['GET'])
def index():
    """Retorna la página de inicio."""
    lista = None
    if request.method == 'GET':
        con = connect_db()
        if con:
            lista = get_list(con, "I")
    return jsonify(lista)

@app.route('/agregar_personaje', methods=['GET'])
def agregar_personaje():
    """Agrega un personaje a un episodio."""
    if request.method == 'GET':
        con = connect_db()
        if con:
            episode = request.args.get("episode")
            character_name = request.args.get("name")
            if episode and character_name:
                con.lpush(episode, character_name)
                return jsonify({"message": "Personaje agregado correctamente"})
            else:
                return jsonify({"error": "Se requieren el número de episodio y el nombre del personaje"}), 400
    return jsonify({"error": "No se pudo conectar a la base de datos Redis"}), 500

@app.route('/quitar_personaje', methods=['GET'])
def quitar_personaje():
    """Quita un personaje de un episodio."""
    if request.method == 'GET':
        con = connect_db()
        if con:
            episode = request.args.get("episode")
            character_name = request.args.get("name")
            lista = get_list(con, episode)
            if episode and character_name in lista:
                con.lrem(episode, 0, character_name)
                return jsonify({"message": "Personaje eliminado correctamente"})
            else:
                return jsonify({"error": "Se requieren el número de episodio y el nombre del personaje correspondiente"}), 400
    return jsonify({"error": "No se pudo conectar a la base de datos Redis"}), 500

@app.route('/listar_personajes', methods=['GET'])
def listar_personajes():
    """Lista los personajes de un episodio."""
    lista = None
    if request.method == 'GET':
        con = connect_db()
        if con:
            episode = request.args.get("episode")
            if episode:
                lista = get_list(con, episode)
            else:
                return jsonify({"error": "Se requiere el número de episodio"}), 400
    return jsonify(lista)

if __name__ == '__main__':
    app.run(host='web-api-flask', port='5000', debug=True)
