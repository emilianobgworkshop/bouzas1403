from flask import Flask, render_template_string, request, redirect, session
import json
import os

app = Flask(__name__)
app.secret_key = "clave_secreta"

ARCHIVO_INVENTARIO = "inventario.json"

usuarios = {
    "admin": {"password": "admin123", "rol": "admin"},
    "alumno1": {"password": "1234", "rol": "alumno"}
}

def cargar_inventario():
    if os.path.exists(ARCHIVO_INVENTARIO):
        with open(ARCHIVO_INVENTARIO, "r") as f:
            return json.load(f)
    else:
        return [
            {"id": 0, "nombre": "Probetas", "cantidad": 10, "categoria": "Consumible", "estado": "blanco", "solicitado": 0, "usuario": "", "minimo": 0},
            {"id": 1, "nombre": "Microscopio", "cantidad": 5, "categoria": "Equipo", "estado": "blanco", "solicitado": 0, "usuario": "", "minimo": 0}
        ]

def guardar_inventario():
    with open(ARCHIVO_INVENTARIO, "w") as f:
        json.dump(inventario, f, indent=4)

inventario = cargar_inventario()


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["usuario"]
        password = request.form["password"]

        if user in usuarios and usuarios[user]["password"] == password:
            session["usuario"] = user
            session["rol"] = usuarios[user]["rol"]
            print(f"{user} inició sesión")
            return redirect("/inventario")
        else:
            return "Usuario o contraseña incorrectos"

    return """
    <h2>Login</h2>
    <form method="post">
        Usuario: <input name="usuario"><br>
        Contraseña: <input name="password" type="password"><br><br>
        <button type="submit">Entrar</button>
    </form>
    """


@app.route("/logout")
def logout():
    usuario = session.get("usuario", "")
    session.clear()
    print(f"{usuario} cerró sesión")
    return redirect("/")


@app.route("/inventario")
def ver_inventario():
    if "usuario" not in session:
        return redirect("/")

    html = """
    <h1>Inventario del laboratorio</h1>

    <p>
    Usuario: {{usuario}} ({{rol}})
    <a href="/logout"><button>Cerrar sesión</button></a>

    {% if rol == "admin" %}
    <a href="/admin"><button>Administrar inventario</button></a>
    {% endif %}
    </p>

    {% for item in inventario %}
    <div style="
        padding:10px;
        margin:10px;
        background-color:
        {% if item.estado == 'rojo' %}#ffb3b3
        {% elif item.estado == 'amarillo' %}#fff0b3
        {% elif item.estado == 'verde' %}#b3ffb3
        {% elif item.get('minimo') is not none and item.cantidad <= item.get('minimo',0) %}#ffcc99
        {% else %}#f0f0f0
        {% endif %}
    ">
        <b>{{item.nombre}}</b><br>
        Categoría: {{item.categoria}}<br>
        Cantidad disponible: {{item.cantidad}}<br>
        Stock mínimo: {{item.get('minimo',0)}}<br>
        Solicitado: {{item.solicitado}}<br>
        Solicitado por: {{item.usuario}}<br><br>

        {% if rol == "alumno" %}
        <form action="/solicitar/{{item.id}}" method="post">
            Cantidad: <input name="cantidad" type="number" min="1">
            <button type="submit">Solicitar</button>
        </form>
        {% endif %}

        {% if rol == "admin" and item.estado == "rojo" %}
        <form action="/completar/{{item.id}}" method="post">
            <button type="submit">Completar</button>
        </form>
        {% endif %}

        {% if rol == "admin" and item.estado == "verde" %}
        <form action="/actualizar/{{item.id}}" method="post">
            <button type="submit">Actualizar</button>
        </form>
        {% endif %}
    </div>
    {% endfor %}
    """

    return render_template_string(html, inventario=inventario,
                                  usuario=session["usuario"],
                                  rol=session["rol"])


@app.route("/admin", methods=["GET", "POST"])
def panel_admin():
    if "usuario" not in session or session["rol"] != "admin":
        return redirect("/")

    if request.method == "POST":
        nombre = request.form["nombre"]
        cantidad = int(request.form["cantidad"])
        categoria = request.form["categoria"]

        nuevo_id = len(inventario)
        inventario.append({
            "id": nuevo_id,
            "nombre": nombre,
            "cantidad": cantidad,
            "categoria": categoria,
            "estado": "blanco",
            "solicitado": 0,
            "usuario": "",
            "minimo": 0
        })

        guardar_inventario()
        return redirect("/admin")

    html = """
    <h1>Panel de Administración</h1>

    <a href="/inventario"><button>Volver</button></a>
    <a href="/logout"><button>Cerrar sesión</button></a>

    <h2>Agregar objeto</h2>
    <form method="post">
        Nombre: <input name="nombre"><br>
        Cantidad: <input name="cantidad" type="number"><br>
        Categoría:
        <select name="categoria">
            <option value="Consumible">Consumible</option>
            <option value="Equipo">Equipo</option>
        </select><br><br>
        <button type="submit">Agregar</button>
    </form>

    <h2>Inventario actual</h2>
    {% for item in inventario %}
        <div style="margin:10px; padding:10px; border:1px solid gray;">
            <b>{{item.nombre}}</b><br>
            Cantidad: {{item.cantidad}}<br>
            Categoría: {{item.categoria}}<br>
            Mínimo: {{item.get('minimo',0)}}<br>

            <form action="/editar/{{item.id}}" method="post">
                Nueva cantidad:
                <input name="cantidad" type="number"><br>

                Nivel mínimo alerta:
                <input name="minimo" type="number" value="{{item.get('minimo',0)}}"><br>

                <button type="submit">Actualizar</button>
            </form>

            <form action="/eliminar/{{item.id}}" method="post">
                <button type="submit">Eliminar</button>
            </form>
        </div>
    {% endfor %}
    """

    return render_template_string(html, inventario=inventario)


@app.route("/editar/<int:id>", methods=["POST"])
def editar(id):
    if session["rol"] != "admin":
        return redirect("/")

    nueva_cantidad = int(request.form["cantidad"])
    minimo = int(request.form.get("minimo", 0))

    inventario[id]["cantidad"] = nueva_cantidad
    inventario[id]["minimo"] = minimo

    guardar_inventario()
    return redirect("/admin")


@app.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    if session["rol"] != "admin":
        return redirect("/")

    inventario.pop(id)

    for i, item in enumerate(inventario):
        item["id"] = i

    guardar_inventario()
    return redirect("/admin")


@app.route("/solicitar/<int:id>", methods=["POST"])
def solicitar(id):
    if session["rol"] != "alumno":
        return redirect("/inventario")

    cantidad = int(request.form["cantidad"])
    inventario[id]["solicitado"] = cantidad
    inventario[id]["estado"] = "rojo"
    inventario[id]["usuario"] = session["usuario"]

    guardar_inventario()
    return redirect("/inventario")


@app.route("/completar/<int:id>", methods=["POST"])
def completar(id):
    if session["rol"] != "admin":
        return redirect("/inventario")

    inventario[id]["estado"] = "verde"
    guardar_inventario()
    return redirect("/inventario")


@app.route("/actualizar/<int:id>", methods=["POST"])
def actualizar(id):
    if session["rol"] != "admin":
        return redirect("/inventario")

    item = inventario[id]

    if item["categoria"] == "Consumible":
        item["cantidad"] -= item["solicitado"]

    item["solicitado"] = 0
    item["estado"] = "blanco"
    item["usuario"] = ""

    guardar_inventario()
    return redirect("/inventario")


if __name__ == "__main__":
    app.run()


