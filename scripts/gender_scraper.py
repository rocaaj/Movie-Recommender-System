import pandas as pd
import sqlite3

# Paths to your CSV file and database
csv_file = "Persons.csv"
db_file = "movies.db"

# Load Person.csv into a Pandas DataFrame
df = pd.read_csv(csv_file)

# Connect to the SQLite database
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Iterate over the CSV data and update gender in stars table
for _, row in df.iterrows():
    name = row['Name']
    gender = row['Gender']

    # Update the stars table if the name exists
    cursor.execute("""
        UPDATE star
        SET star_gender = ?
        WHERE star_name = ?
    """, (gender, name))

# Commit and close the connection
conn.commit()
conn.close()
