from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = "inventarte_secret_key"

# Configuración de Cookies para evitar problemas de sesión
app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False, # Cambiar a True si usas HTTPS en producción
    SESSION_COOKIE_HTTPONLY=True
)

# Permitir credenciales es vital para que session['user'] funcione
CORS(app, supports_credentials=True)

# --- CONFIGURACIÓN DE BASE DE DATOS ---
db_config = {
    'host': 'mainline.proxy.rlwy.net',
    'user': 'root',
    'password': 'KfvWEynWDrziCgNCaUStMCCAXyPaaSGM',
    'database': 'railway',
    'port': 30898
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# --- RUTAS DE AUTENTICACIÓN ---

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    usuario = data.get('usuario')
    password = data.get('password')

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM usuarios WHERE usuario=%s AND password=%s",
            (usuario, password)
        )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            session['user'] = user['usuario']
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "Credenciales inválidas"}), 401
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/check-session')
def check_session():
    if 'user' in session:
        return jsonify({"logged": True, "user": session['user']})
    return jsonify({"logged": False})

@app.route('/logout')
def logout():
    session.clear()
    return jsonify({"status": "logout"})

# --- RUTAS DE INVENTARIO ---

@app.route('/inventario', methods=['GET'])
def get_inventario():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM inventario")
        productos = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(productos)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/inventario', methods=['POST'])
def add_producto():
    nuevo_prod = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO inventario (nombre, precio) VALUES (%s, %s)",
            (nuevo_prod['nombre'], nuevo_prod['precio'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "success"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/inventario/<int:id>', methods=['DELETE'])
def delete_producto(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inventario WHERE id = %s", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"status": "deleted"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- RUTAS DE COTIZACIÓN ---

@app.route('/guardar_cotizacion', methods=['POST'])
def guardar_cotizacion():
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Iniciar transacción manual para asegurar integridad
        cursor.execute("START TRANSACTION")
        
        cursor.execute(
            "INSERT INTO cotizaciones (total_general) VALUES (%s)",
            (data['total'],)
        )
        cotizacion_id = cursor.lastrowid

        for item in data['items']:
            cursor.execute("""
                INSERT INTO cotizacion_detalle 
                (cotizacion_id, descripcion, detalle_medida, subtotal)
                VALUES (%s, %s, %s, %s)
            """, (
                cotizacion_id,
                item['desc'],
                item['detalle'],
                item['sub']
            ))

        conn.commit()
        return jsonify({"status": "success", "id": cotizacion_id}), 201

    except Exception as e:
        conn.rollback() # Si algo falla, deshace los cambios en la DB
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# --- SERVIR ARCHIVOS ESTÁTICOS ---

@app.route('/')
def home():
    # Asegúrate de que el archivo HTML se llame exactamente así:
    return send_from_directory(os.getcwd(), 'Calcular precio impresion.html')

# --- INICIO DEL SERVIDOR ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)