from flask import Flask,render_template, request, jsonify
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
    if con.dbsize() < 1:
        for cap in array_capitulos:
            con.hset(f'capitulo{cap["numero"]}', 'titulo', cap["titulo"])
            con.hset(f'capitulo{cap["numero"]}', 'temporada', cap["temporada"])
            con.hset(f'capitulo{cap["numero"]}', 'precio', cap["precio"])
            con.lpush('capitulos', cap["numero"])

cargar_capitulos() # Llama a la funcion para cargar los capitulos

def obtener_info_capitulo(con, numero):
    if con.exists(numero) > 0: # Verifica si existe esa clave en la base de datos
            disponibilidad = con.get(numero)
    else:
        disponibilidad = "Disponible"
    capitulo_info = {
        "numero": numero,
        "titulo": con.hget(f'capitulo{numero}', "titulo"),
        "temporada": con.hget(f'capitulo{numero}', "temporada"),
        "precio": con.hget(f'capitulo{numero}', "precio"),
        "disponibilidad": disponibilidad
    }
    return capitulo_info

@app.route('/') # Ruta principal de la aplicación
def index():
    con = connect_db()
    capitulos = con.sort("capitulos") # Obtiene los numeros de los capitulos ordenados
    lista_capitulos = []
    for capitulo in capitulos:
        capitulo_info = obtener_info_capitulo(con, capitulo)
        lista_capitulos.append(capitulo_info)
    return render_template('index.html', lista_capitulos=lista_capitulos)

@app.route('/reservar_capitulo', methods=['GET'])
def reservar_capitulo():
    numero_capitulo = request.args.get("numero") # Obtiene el numero de capitulo de la url
    capitulo={}
    if request.method == 'GET':
        con = connect_db()
        if con.get(numero_capitulo) not in ["Reservado", "Alquilado"]: # Verifica si el capitulo esta disponible para reservar
            con.setex(numero_capitulo, 240, "Reservado") # Reserva el capitulo por 240 segundos (4 minutos)
            capitulo = obtener_info_capitulo(con, numero_capitulo)
    return render_template('info_capitulo.html', capitulo=capitulo)


@app.route('/confirmar_pago', methods=['GET'])
def confirmar_pago():
    if request.method == 'GET':
        con = connect_db()
        # Obtiene el numero de capitulo y el precio de la solicitud
        numero_capitulo = request.args.get("numero")
        precio = request.args.get("precio")
        if con.get(numero_capitulo) == "Reservado": # Verifica si el capitulo esta reservado
            con.setex(numero_capitulo, 86400, "Alquilado") # Alquila el capítulo por 86400 segundos (1 día)
            if con.get(numero_capitulo) == "Alquilado": # Verificar si el capítulo se alquiló con éxito
                res = "Confirmado"
        else:
            res = "No confirmado"
    return render_template('confirmacion.html', res=res)

if __name__ == '__main__':
    app.run(host='web-api-flask', port='5000', debug=True)
