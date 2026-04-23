import json
import os
import uuid

from flask import Flask, request, jsonify, render_template, redirect, url_for
from psycopg2.extras import RealDictCursor
from werkzeug.utils import secure_filename
from database import get_connection

app = Flask(__name__)

# CONFIG UPLOAD
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Teste API
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "API de catalogo de filmes"}), 200


# Ping
@app.route('/ping', methods=['GET'])
def ping():
    conn = get_connection()
    conn.close()
    return jsonify({"message": "pong! API Rodando!", "db": str(conn)}), 200


# Listar filmes
@app.route('/filmes', methods=['GET'])
def listar_filmes():
    sql = "SELECT * FROM filmes"
    try:
        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql)
        filmes = cursor.fetchall()
        conn.close()
        return render_template("index.html", filmes=filmes)
    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": "erro ao listar filmes"}), 500


# NOVO FILME (COM UPLOAD)
@app.route("/novo", methods=["GET", "POST"])
def novo_filme():
    sql = "INSERT INTO filmes (titulo, genero, ano, url_capa) VALUES (%s, %s, %s, %s)"
    try:
        if request.method == "POST":
            titulo = request.form["titulo"]
            genero = request.form["genero"]
            ano = request.form["ano"]

            print(request.files)
            file = request.files.get("capa")
            print("capa", file)

            if not file or file.filename == "":
                return "Nenhuma imagem enviada"

            if file and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                nome_unico = f"{uuid.uuid4()}.{ext}"

                caminho = f'{app.config['UPLOAD_FOLDER']}/{nome_unico}'
                print("caminho da foto", caminho)
                # caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_unico)
                print("caminho da imagem", caminho)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                # cria pasta se não existir
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

                file.save(caminho)

                url_capa = caminho
            else:
                return "Formato inválido (use jpg, jpeg ou png)"

            params = [titulo, genero, ano, url_capa]

            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            conn.close()

            return redirect(url_for("listar_filmes"))

        return render_template("novo_filme.html")

    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": "erro ao cadastrar filme"}), 500


# EDITAR FILME (COM UPLOAD OPCIONAL)
@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar_filme(id):
    try:
        conn = get_connection()

        if request.method == "POST":
            titulo = request.form["titulo"]
            genero = request.form["genero"]
            ano = request.form["ano"]

            file = request.files.get("imagem")

            if file and file.filename != "" and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                nome_unico = f"{uuid.uuid4()}.{ext}"

                caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_unico)

                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

                file.save(caminho)

                url_capa = caminho
            else:
                # mantém imagem antiga
                url_capa = request.form.get("url_capa_antiga")

            sql_update = """
                UPDATE filmes 
                SET titulo = %s, genero = %s, ano = %s, url_capa = %s 
                WHERE id = %s
            """

            params = [titulo, genero, ano, url_capa, id]

            cursor = conn.cursor()
            cursor.execute(sql_update, params)
            conn.commit()
            conn.close()

            return redirect(url_for("listar_filmes"))

        # GET
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM filmes WHERE id = %s", [id])
        filme = cursor.fetchone()
        conn.close()

        if filme is None:
            return redirect(url_for("listar_filmes"))

        return render_template("editar_filme.html", filme=filme)

    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": "erro ao editar filme"}), 500


# DELETAR
@app.route("/deletar/<int:id>", methods=["POST"])
def deletar_filme(id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM filmes WHERE id = %s", [id])

        conn.commit()
        conn.close()

        return redirect(url_for("listar_filmes"))

    except Exception as ex:
        print('erro: ', str(ex))
        return jsonify({"message": "erro ao deletar filme"}), 500


if __name__ == '__main__':
    app.run(debug=True)
