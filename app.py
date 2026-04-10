from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)  # Permite la comunicación con el HTML

# Configuración de MySQL
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'infopmmc',
    'database': 'sistema_impresion'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

from flask import send_from_directory
import os

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
        cursor.execute("INSERT INTO inventario (nombre, precio) VALUES (%s, %s)", 
                       (nuevo_prod['nombre'], nuevo_prod['precio']))
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
        # 1. Insertar la cabecera
        cursor.execute("INSERT INTO cotizaciones (total_general) VALUES (%s)", (data['total'],))
        cotizacion_id = cursor.lastrowid
        
        # 2. Insertar cada item de la tabla
        for item in data['items']:
            cursor.execute("""
                INSERT INTO cotizacion_detalle (cotizacion_id, descripcion, detalle_medida, subtotal)
                VALUES (%s, %s, %s, %s)
            """, (cotizacion_id, item['desc'], item['detalle'], item['sub']))
        
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
# IMPORTANTE: Esta sección SIEMPRE debe ir al final del archivo
if __name__ == '__main__':
    print("Servidor iniciado en http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)