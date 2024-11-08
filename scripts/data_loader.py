import argparse
import pandas as pd
import sqlite3

# Set up argument parser
parser = argparse.ArgumentParser(description="Movie Recommender System Data Loader")
parser.add_argument("db_file", help="Name of the database file")  # Path to `movies.db` file
parser.add_argument("csv_file", help="Name of the csv file")  # Path to `imdb_top_1000.csv`
args = parser.parse_args()

# Extract arguments
db_file = args.db_file
csv_file = args.csv_file

# Connect to the SQLite database
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

print(f"Connected to database: {db_file}")

# Load data from CSV into DataFrame
df = pd.read_csv(csv_file)

# Insert data into 'movie' table
for index, row in df.iterrows():
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO movie (
                mov_id, mov_orig_title, mov_eng_title, released_year, certificate,
                runtime, imdb_rating, overview, meta_score, director, gross
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            index + 1,  # Assigning mov_id as index + 1 if it doesn't exist in the CSV
            row['Series_Title'],  # Assuming CSV contains this column
            row['Series_Title'],  # Using the same value for English title for simplicity
            row['Released_Year'],
            row['Certificate'] if pd.notna(row['Certificate']) else None,
            int(row['Runtime'].replace(' min', '')) if pd.notna(row['Runtime']) else None,
            row['IMDB_Rating'] if pd.notna(row['IMDB_Rating']) else None,
            row['Overview'] if pd.notna(row['Overview']) else None,
            int(row['Meta_score']) if pd.notna(row['Meta_score']) else None,
            row['Director'] if pd.notna(row['Director']) else None,
            int(row['Gross'].replace(',', '')) if pd.notna(row['Gross']) else None
        ))
    except Exception as e:
        print(f"Error inserting row {index}: {e}")

# Commit and close the connection
conn.commit()
cursor.close()
conn.close()

print("Data loading completed successfully.")