import random
import string
import os
import psycopg2
import threading
import requests
import time

from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.secret_key = "clave_super_secreta_123"

# Activar protección CSRF
csrf = CSRFProtect(app)

# =========================
# Conexión a la base de datos
# =========================
def get_db():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:  # fallback local
        import sqlite3
        return sqlite3.connect("usuarios.db")
    return psycopg2.connect(database_url)

# =========================
# Crear base de datos
# =========================
def crear_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

crear_db()

# =========================
# Generador de contraseña
# =========================
def generar_password(longitud, usar_mayus, usar_numeros, usar_simbolos):
    caracteres = string.ascii_lowercase
    if usar_mayus:
        caracteres += string.ascii_uppercase
    if usar_numeros:
        caracteres += string.digits
    if usar_simbolos:
        caracteres += string.punctuation
    if not caracteres:
        caracteres = string.ascii_lowercase
    return ''.join(random.choice(caracteres) for _ in range(longitud))

# =========================
# Login
# =========================
@app.route("/", methods=["GET", "POST"])
def login():
    intentos = session.get("intentos", 0)
    if intentos >= 5:
        return render_template("index.html", error="Demasiados intentos fallidos. Espere unos minutos.")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM usuarios WHERE username = %s", (username,))
        usuario = cursor.fetchone()
        conn.close()

        if usuario and check_password_hash(usuario[0], password):
            session.clear()
            session["user"] = username
            session["historial"] = []
            session["intentos"] = 0
            session["longitud"] = 16
            session["mayus"] = True
            session["numeros"] = True
            session["simbolos"] = True
            return redirect(url_for("dashboard"))
        else:
            session["intentos"] = intentos + 1
            return render_template("index.html", error="Usuario o contraseña incorrectos")

    return render_template("index.html")

# =========================
# Registro
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        password_hash = generate_password_hash(password)

        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO usuarios (username, password) VALUES (%s, %s)", (username, password_hash))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except:
            return render_template("register.html", error="El usuario ya existe")

    return render_template("register.html")

# =========================
# Dashboard
# =========================
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    longitud = session.get("longitud", 16)
    usar_mayus = session.get("mayus", True)
    usar_numeros = session.get("numeros", True)
    usar_simbolos = session.get("simbolos", True)
    password_generada = None

    if request.method == "POST":
        longitud = int(request.form.get("longitud", 16))
        usar_mayus = "mayus" in request.form
        usar_numeros = "numeros" in request.form
        usar_simbolos = "simbolos" in request.form

        session["longitud"] = longitud
        session["mayus"] = usar_mayus
        session["numeros"] = usar_numeros
        session["simbolos"] = usar_simbolos

        password_generada = generar_password(longitud, usar_mayus, usar_numeros, usar_simbolos)

        historial = session.get("historial", [])
        historial.insert(0, password_generada)
        session["historial"] = historial[:5]

    return render_template(
        "dashboard.html",
        user=session["user"],
        password=password_generada,
        historial=session.get("historial", []),
        longitud=longitud,
        mayus=usar_mayus,
        numeros=usar_numeros,
        simbolos=usar_simbolos
    )

# =========================
# Logout
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# =========================
# Ping interno para mantener la app despierta
# =========================
def mantener_despues_ping():
    url = os.environ.get("APP_URL")
    if not url:
        print("APP_URL no configurada, ping interno desactivado.")
        return
    while True:
        try:
            requests.get(url)
            print("Ping enviado a la app para mantenerla despierta.")
        except Exception as e:
            print("Error haciendo ping:", e)
        time.sleep(600)  # cada 10 minutos

# =========================
# Run
# =========================
if __name__ == "__main__":
    # Inicia ping interno en segundo plano
    threading.Thread(target=mantener_despues_ping, daemon=True).start()
    app.run(debug=True)