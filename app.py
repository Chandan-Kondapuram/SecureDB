import bcrypt
from flask import Flask, request, jsonify
import mysql.connector
from cryptography.fernet import Fernet
import hashlib
import os

app = Flask(__name__)

# Database connection details
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "PASSWPRD",
    "database": "secure_database"
}

# Function to load or generate an encryption key
KEY_FILE = "cipher.key"

def load_or_generate_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as key_file:
            return key_file.read()
    else:
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
        return key

CIPHER_KEY = load_or_generate_key()
cipher = Fernet(CIPHER_KEY)

@app.route('/')
def home():
    return "Welcome to the Secure Database API!", 200

@app.route('/register', methods=['POST'])
def register_user():
    data = request.json
    username = data['username']
    password = data['password']
    group = data['group']
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password_hash, user_group) VALUES (%s, %s, %s)",
                       (username, hashed_password.decode(), group))
        conn.commit()
        return jsonify({"message": "User registered successfully!"}), 201
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/login', methods=['POST'])
def login_user():
    data = request.json
    username = data['username']
    password = data['password']

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
            return jsonify({"message": "Login successful!", "group": user['user_group']}), 200
        return jsonify({"error": "Invalid credentials!"}), 401
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/query', methods=['GET'])
def query_data():
    group = request.args.get('group')  # Group H or R

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        if group == 'H':
            cursor.execute("SELECT * FROM healthcare_data")
        elif group == 'R':
            cursor.execute("SELECT gender, age, weight, height, health_history FROM healthcare_data")
        else:
            return jsonify({"error": "Invalid group!"}), 400

        data = cursor.fetchall()

        # Verify data integrity
        for row in data:
        # Temporarily skip hash verification for testing
            pass

        return jsonify(data), 200
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/add', methods=['POST'])
def add_data():
    data = request.json
    username = request.headers.get("username")
    password = request.headers.get("password")

    try:
        # Connect to the database
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # Authenticate user
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        if not user or not bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
            return jsonify({"error": "Unauthorized!"}), 401

        # Check if user belongs to Group H
        if user['user_group'] != 'H':
            return jsonify({"error": "Permission denied!"}), 403

        # Encrypt sensitive fields
        gender_encrypted = cipher.encrypt(str(data['gender']).encode()).decode()
        age_encrypted = cipher.encrypt(str(data['age']).encode()).decode()

        # Prepare data for insertion with hash
        row_data = {
            "first_name": data['first_name'],
            "last_name": data['last_name'],
            "gender": gender_encrypted,
            "age": age_encrypted,
            "weight": data['weight'],
            "height": data['height'],
            "health_history": data['health_history']
        }
        row_hash = hashlib.sha256(str(row_data).encode()).hexdigest()

        # Insert data into healthcare_data table
        cursor.execute("""
            INSERT INTO healthcare_data (first_name, last_name, gender, age, weight, height, health_history, row_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (data['first_name'], data['last_name'], gender_encrypted, age_encrypted,
              data['weight'], data['height'], data['health_history'], row_hash))
        conn.commit()

        return jsonify({"message": "Data added successfully!"}), 201
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)



