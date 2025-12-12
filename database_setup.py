import mysql.connector
import random
import hashlib
from faker import Faker

# Initialize Faker and health conditions
fake = Faker()
health_conditions = [
    "No significant health issues", "Diabetes type 2", "Hypertension", "Asthma",
    "Cardiovascular disease", "Chronic back pain", "Arthritis", "History of migraines",
    "Seasonal allergies", "Chronic kidney disease", "History of smoking-related issues",
    "Liver dysfunction", "Ongoing cancer treatment", "Recovering from surgery",
    "Mental health therapy", "Substance abuse rehabilitation",
    "Frequent colds and infections", "Autoimmune disease management",
    "Underweight and nutritional deficiencies", "Pregnancy and prenatal care"
]

def setup_database():
    # Connect to MySQL
    conn = mysql.connector.connect(
        user='root', password='PASSWORD', host='localhost'
    )
    cursor = conn.cursor()

    # Create the database
    cursor.execute("CREATE DATABASE IF NOT EXISTS secure_database")
    cursor.execute("USE secure_database")

    # Create the healthcare_data table with a row_hash column
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS healthcare_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            gender BOOLEAN,
            age INT,
            weight FLOAT,
            height FLOAT,
            health_history TEXT,
            row_hash VARCHAR(255) NOT NULL
        )
    """)

    # Create the users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            user_group ENUM('H', 'R') NOT NULL
        )
    """)

    # Clear existing healthcare_data to prevent duplicates
    cursor.execute("DELETE FROM healthcare_data")

    # Generate and insert 150 rows of data with row_hash
    rows = []
    for _ in range(150):
        first_name = fake.first_name()
        last_name = fake.last_name()
        gender = random.choice([0, 1])  # 0 for Female, 1 for Male
        age = random.randint(18, 90)
        weight = round(random.uniform(50.0, 100.0), 1)
        height = round(random.uniform(150.0, 200.0), 1)
        health_history = random.choice(health_conditions)

        # Prepare data for row_hash calculation
        row_data = {
            "first_name": first_name,
            "last_name": last_name,
            "gender": gender,
            "age": age,
            "weight": weight,
            "height": height,
            "health_history": health_history
        }

        # Calculate the row hash
        row_hash = hashlib.sha256(str(row_data).encode()).hexdigest()

        # Append the row
        rows.append((first_name, last_name, gender, age, weight, height, health_history, row_hash))

    # Insert rows into the healthcare_data table
    cursor.executemany("""
        INSERT INTO healthcare_data (first_name, last_name, gender, age, weight, height, health_history, row_hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, rows)

    conn.commit()
    print("Database setup and data insertion complete!")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    setup_database()
