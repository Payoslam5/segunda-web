import random
import string
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "clave_super_secreta_123"  # Cambiar en producción

# Usuario de prueba
USUARIO_REAL = "admin"
PASSWORD_REAL = "1234"


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

    # Si el usuario desactiva todo excepto minúsculas
    if not caracteres:
        caracteres = string.ascii_lowercase

    return ''.join(random.choice(caracteres) for _ in range(longitud))


# =========================
# Login
# =========================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == USUARIO_REAL and password == PASSWORD_REAL:
            session.clear()
            session["user"] = username
            session["historial"] = []

            # Preferencias por defecto
            session["longitud"] = 16
            session["mayus"] = True
            session["numeros"] = True
            session["simbolos"] = True

            return redirect(url_for("dashboard"))
        else:
            return render_template("index.html", error="Usuario o contraseña incorrectos")

    return render_template("index.html")


# =========================
# Dashboard
# =========================
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    # Cargar preferencias guardadas
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

        # Guardar preferencias
        session["longitud"] = longitud
        session["mayus"] = usar_mayus
        session["numeros"] = usar_numeros
        session["simbolos"] = usar_simbolos

        password_generada = generar_password(
            longitud,
            usar_mayus,
            usar_numeros,
            usar_simbolos
        )

        # Guardar historial (máximo 5)
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
# Run
# =========================
if __name__ == "__main__":
    app.run()