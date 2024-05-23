from flask import Flask, render_template, request, jsonify, json
from redis import Redis, ConnectionError
from flask_bootstrap import Bootstrap
from capitulos import array_capitulos


app = Flask(__name__)
bootstrap = Bootstrap(app)

def connect_db():
    """Función para conectar a la base de datos Redis"""
    try:
        conexion = Redis(host='db-redis', port=6379, decode_responses=True)
        conexion.ping()
        print("Conectado a Redis")
        return conexion
    except ConnectionError as e:
        print("Error de conexión con Redis:", e)
        return None

def cargar_capitulos():
    """Función para cargar los capítulos en la base de datos"""
    con = connect_db()
    if con and con.dbsize() == 0:
        for capitulo in array_capitulos:
            con.lpush('capitulos', json.dumps(capitulo))

cargar_capitulos()

@app.route('/') # Ruta principal de la aplicación
def index():
    con = connect_db()
    capitulos = con.lrange('capitulos', 0, -1)
    lista_capitulos = []
    for capitulo in capitulos:
        capitulo_info = json.loads(capitulo)
        numero=capitulo_info["numero"]
        disponibilidad = con.get(numero) if con.exists(numero) else "Disponible"
        capitulo_info["disponibilidad"] = disponibilidad
        lista_capitulos.append(capitulo_info)
    return render_template('index.html', lista_capitulos=lista_capitulos)

@app.route('/reservar_capitulo', methods=['GET'])
def reservar_capitulo():
    numero_capitulo = request.args.get("numero")  # Obtiene el número de capítulo de la URL
    capitulo = {}
    if request.method == 'GET':
        con = connect_db()
        disponibilidad = con.get(numero_capitulo) if con.exists(numero_capitulo) else "Disponible"
        if disponibilidad not in ["Reservado", "Alquilado"]:
            con.setex(numero_capitulo, 240, "Reservado")  # Reserva el capítulo por 240 segundos (4 minutos)
            capitulos = con.lrange("capitulos", 0, -1)
            for cap in capitulos:
                capitulo_info = json.loads(cap)
                if capitulo_info["numero"] == int(numero_capitulo):
                    capitulo = capitulo_info
                    break  
    return render_template('info_capitulo.html', capitulo=capitulo)

@app.route('/confirmar_pago', methods=['GET'])
def confirmar_pago():
    if request.method == 'GET':
        con = connect_db()
        numero_capitulo = request.args.get("numero")
        if con.get(numero_capitulo) == "Reservado": # Verifica si el capitulo esta reservado
            con.setex(numero_capitulo, 86400, "Alquilado") # Alquila el capítulo por 86400 segundos (1 día)
            if con.get(numero_capitulo) == "Alquilado": # Verificar si el capítulo se alquiló con éxito
                res = "Confirmado"
        else:
            res = "No confirmado"
    return render_template('confirmacion.html', res=res)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html', error="¡Ooops! La página que buscas no está en el servidor!"), 404

if __name__ == '__main__':
    app.run(host='web-api-flask', port='5000', debug=True)
