from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
import os

app = Flask(__name__)
CORS(app)

# Configuración de MySQL (Railway)
db_config = {
    'host': 'mainline.proxy.rlwy.net',
    'user': 'root',
    'password': 'KfvWEynWDrziCgNCaUStMCCAXyPaaSGM',
    'database': 'railway',
    'port': 30898
}


@app.route('/inventario', methods=['POST'])
def add_producto():
    nuevo_prod = request.json
    print("Datos recibidos:", nuevo_prod)  # 👈 agregar esto

def get_db_connection():
    return mysql.connector.connect(**db_config)

# Servir HTML
@app.route('/')
def home():
    return send_from_directory(os.getcwd(), 'Calcular precio impresion.html')

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
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/historial', methods=['GET'])
def get_historial():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM cotizaciones ORDER BY fecha DESC")
        historial = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(historial)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# --- INICIO DEL SERVIDOR ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)