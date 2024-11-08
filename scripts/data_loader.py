import argparse
import pandas as pd
import sqlite3

# Set up argument parser
parser = argparse.ArgumentParser(description="Movie Recommender System Data Loader")
parser.add_argument("db_file", help="Path to the SQLite database file")  # Path to `movies.db` file
parser.add_argument("csv_file", help="Path to the CSV file to load data from")  # Path to `imdb_top_1000.csv`
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
            index + 1,  # Assigning mov_id as index + 1
            row['Series_Title'],
            row['Series_Title'],
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

# Insert data into 'genre' table
unique_genres = set()
for genres in df['Genre']:
    genre_list = genres.split(', ') if pd.notna(genres) else []
    unique_genres.update(genre_list)

for gen_id, genre_name in enumerate(unique_genres, start=1):
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO genre (gen_id, gen_name)
            VALUES (?, ?)
        ''', (gen_id, genre_name))
    except Exception as e:
        print(f"Error inserting genre '{genre_name}': {e}")

# Insert data into 'movie_genre' table
for index, row in df.iterrows():
    if pd.notna(row['Genre']):
        genres = row['Genre'].split(', ')
        mov_id = index + 1
        for genre_name in genres:
            cursor.execute('SELECT gen_id FROM genre WHERE gen_name = ?', (genre_name,))
            result = cursor.fetchone()
            if result:
                gen_id = result[0]
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO movie_genre (mov_id, gen_id)
                        VALUES (?, ?)
                    ''', (mov_id, gen_id))
                except Exception as e:
                    print(f"Error linking movie {mov_id} to genre '{genre_name}': {e}")

# Insert data into 'star' table
stars_set = set()
for i in range(1, 5):
    column_name = f'Star{i}'
    if column_name in df.columns:
        stars_set.update(df[column_name].dropna().unique())

for star_id, star_name in enumerate(stars_set, start=1):
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO star (star_id, star_name)
            VALUES (?, ?)
        ''', (star_id, star_name))
    except Exception as e:
        print(f"Error inserting star '{star_name}': {e}")

# Insert data into 'movie_star' table
for index, row in df.iterrows():
    mov_id = index + 1
    for i in range(1, 5):
        column_name = f'Star{i}'
        if column_name in df.columns and pd.notna(row[column_name]):
            star_name = row[column_name]
            cursor.execute('SELECT star_id FROM star WHERE star_name = ?', (star_name,))
            result = cursor.fetchone()
            if result:
                star_id = result[0]
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO movie_star (mov_id, star_id)
                        VALUES (?, ?)
                    ''', (mov_id, star_id))
                except Exception as e:
                    print(f"Error linking movie {mov_id} to star '{star_name}': {e}")

# Commit and close the connection
conn.commit()
cursor.close()
conn.close()

print("Data loading completed successfully.")