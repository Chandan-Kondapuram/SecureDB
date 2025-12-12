import mysql.connector
import hashlib

# Database connection details
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "PASSWORD",
    "database": "secure_database"
}

def recalculate_row_hashes():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Fetch all rows from the healthcare_data table
    cursor.execute("SELECT id, first_name, last_name, gender, age, weight, height, health_history FROM healthcare_data")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    if not rows:
        print("No rows found in the healthcare_data table!")
        return

    print(f"Found {len(rows)} rows. Recalculating row_hash...")

    for row in rows:
        row_dict = dict(zip(columns, row))

        # Debug: Print each row being processed
        print(f"Processing row ID {row_dict['id']}")

        # Prepare data for row_hash calculation (exclude 'id')
        row_data = {k: v for k, v in row_dict.items() if k != 'id'}
        calculated_hash = hashlib.sha256(str(row_data).encode()).hexdigest()

        # Debug: Print the calculated hash
        print(f"Calculated hash for row ID {row_dict['id']}: {calculated_hash}")

        # Update the row_hash in the database
        cursor.execute(
            "UPDATE healthcare_data SET row_hash = %s WHERE id = %s",
            (calculated_hash, row_dict['id'])
        )

    conn.commit()
    cursor.close()
    conn.close()
    print("Row hashes updated successfully!")

if __name__ == "__main__":
    recalculate_row_hashes()
