from flask import Flask,render_template, request, jsonify
from redis import Redis, ConnectionError
from flask_bootstrap import Bootstrap

app = Flask(__name__)
bootstrap = Bootstrap(app)
array_capitulos = [{"numero": 1, "titulo": "El Mandaloriano", "temporada": 1, "precio": 5.99},
    {"numero": 2, "titulo": "El Niño", "temporada": 1, "precio": 5.99},
    {"numero": 3, "titulo": "El Pecado", "temporada": 1, "precio": 5.99},
    { "numero": 4, "titulo": "Santuario", "temporada": 1, "precio": 5.99},
    {"numero": 5, "titulo": "El Pistolero", "temporada": 1, "precio": 5.99},
    {"numero": 6, "titulo": "El Prisionero", "temporada": 1, "precio": 5.99},
    {"numero": 7, "titulo": "El Ajuste de Cuentas", "temporada": 1, "precio": 5.99},
    {"numero": 8, "titulo": "Redención", "temporada": 1, "precio": 5.99},
    {"numero": 9, "titulo": "El Mariscal", "temporada": 2, "precio": 5.99},
    {"numero": 10, "titulo": "La Pasajera", "temporada": 2, "precio": 5.99},
    {"numero": 11, "titulo": "La Heredera", "temporada": 2, "precio": 5.99},
    {"numero": 12, "titulo": "El Asedio", "temporada": 2, "precio": 5.99},
    {"numero": 13, "titulo": "La Jedi", "temporada": 2, "precio": 5.99},
    {"numero": 14, "titulo": "La Tragedia", "temporada": 2, "precio": 5.99},
    {"numero": 15, "titulo": "El Creyente", "temporada": 2, "precio": 5.99},
    {"numero": 16, "titulo": "El Rescate", "temporada": 2, "precio": 5.99},
    {"numero": 17, "titulo": "El Apóstata", "temporada": 3, "precio": 5.99},
    {"numero": 18, "titulo": "Las Minas de Mandalore","temporada": 3, "precio": 5.99},
    {"numero": 19, "titulo": "El Converso", "temporada": 3, "precio": 5.99},
    {"numero": 20, "titulo": "El Huérfano", "temporada": 3, "precio": 5.99},
    {"numero": 21, "titulo": "El Pirata", "temporada": 3, "precio": 5.99},
    {"numero": 22, "titulo": "Pistoleros a Sueldo", "temporada": 3, "precio": 5.99},
    {"numero": 23, "titulo": "Los Espías", "temporada": 3, "precio": 5.99},
    {"numero": 24, "titulo": "El Retorno", "temporada": 3, "precio": 5.99}]

def connect_db():
    try:
        conexion = Redis(host='db-redis', port=6379, decode_responses=True)
        conexion.ping()
        print("Conectado a Redis")
        return conexion
    except ConnectionError as e:
        print("Error de conexión con Redis:", e)
        return None

def cargar_capitulos():
    con = connect_db()
    if con.dbsize() < 1:
        for cap in array_capitulos:
            con.hset(f'capitulo{cap["numero"]}', 'titulo', cap["titulo"])
            con.hset(f'capitulo{cap["numero"]}', 'temporada', cap["temporada"])
            con.hset(f'capitulo{cap["numero"]}', 'precio', cap["precio"])
            con.lpush('capitulos', cap["numero"])

cargar_capitulos()

@app.route('/')
def index():
    con = connect_db()
    capitulos = con.sort("capitulos")
    lista_capitulos = []
    for capitulo in capitulos:
        if con.exists(capitulo) > 0:
            disponibilidad = con.get(capitulo)
        else:
            disponibilidad = "Disponible"
        lista_capitulos.append({
            "numero": capitulo,
            "titulo": con.hget(f'capitulo{capitulo}', "titulo"),
            "temporada": con.hget(f'capitulo{capitulo}', "temporada"),
            "precio": con.hget(f'capitulo{capitulo}', "precio"),
            "disponibilidad": disponibilidad
        })
    return render_template('index.html', lista_capitulos=lista_capitulos)

@app.route('/reservar_capitulo', methods=['GET'])
def reservar_capitulo():
    numero_capitulo = request.args.get("numero")
    capitulo={}
    if request.method == 'GET':
        con = connect_db()
        if con.get(numero_capitulo) not in ["Reservado", "Alquilado"]:
            con.setex(numero_capitulo, 240, "Reservado")
            capitulo['numero'] = numero_capitulo
            capitulo['titulo'] = request.args.get("titulo")
            capitulo['temporada'] = con.hget(f'capitulo{numero_capitulo}', 'temporada')
            capitulo['disponibilidad'] = con.get(numero_capitulo)
            capitulo['precio'] = con.hget(f'capitulo{numero_capitulo}', 'precio')
        print(capitulo)
    return render_template('info_capitulo.html', capitulo=capitulo)


@app.route('/confirmar_pago', methods=['GET'])
def confirmar_pago():
    if request.method == 'GET':
        con = connect_db()
        numero_capitulo = request.args.get("numero")
        precio = request.args.get("precio")
        if con.get(numero_capitulo) == "Reservado":
            con.setex(numero_capitulo, 86400, "Alquilado")
            if con.get(numero_capitulo) == "Alquilado":
                res = "Confirmado"
        else:
            res = "No confirmado"
    return render_template('confirmacion.html', res=res)

if __name__ == '__main__':
    app.run(host='web-api-flask', port='5000', debug=True)
