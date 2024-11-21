"""
Author: Dario Santiago Lopez, Anthony Roca, ChatGPT 4o with Canvas
Date: November 7, 2024 
Updated: November 18, 2024

Project: Movie Recommender System Data Loader

Description:
    This script loads data from a CSV file containing movie information into an SQLite database.
    It populates tables such as movie, genre, movie_genre, star, movie_star, and rating with
    data from the CSV, ensuring that relationships between movies, genres, and stars are properly
    established in the database.

Acknowledgments:
    This project was developed collaboratively by Dario Santiago Lopez, Anthony Roca, and ChatGPT 4o with Canvas.
    Special thanks to ChatGPT for assistance in developing and refining the data loading logic.
"""

import argparse
import pandas as pd
import sqlite3
import random
from datetime import datetime 

# To run the script, type into your terminal line: python movie_loader_db.py name_of_db.db name_of_csv.csv
# For example: python .\movie_loader_db.py movies.db imdb_top_1000.csv 

# Set up argument parser
parser = argparse.ArgumentParser(description="Movie Recommender System Data Loader")
parser.add_argument("db_file", help="Name of the database file")  # Path to `movies.db` file
parser.add_argument("csv_file", help="Name of the csv file")  # Path to `imdb_top_1000.csv`
args = parser.parse_args()

print("\nArgs received from command line") 

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
        #print(f"Row data: {row}")

# Insert data into 'genre' table
unique_genres = set()
for genres in df['Genre']:
    genre_list = genres.split(', ') if pd.notna(genres) else []
    unique_genres.update(genre_list)

for gen_id, genre_name in enumerate(unique_genres, start = 1):
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

for star_id, star_name in enumerate(stars_set, start = 1):
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

# Insert data into 'rating' table
# Assigning a default user_id and rat_id for simplicity
default_user_id = 1
for index, row in df.iterrows():
    mov_id = index + 1
    rat_id = index + 1  # Generating rat_id based on the index
    rating_date = datetime.now().strftime('%Y-%m-%d')
    rat_score = random.uniform(0.5, 5.0)  # Assigning a random rating between 0.5 and 5.0

    try:
        cursor.execute('''
            INSERT OR IGNORE INTO rating (
                user_id, mov_id, rat_score, rating_date, rat_id
            ) VALUES (?, ?, ?, ?, ?)
        ''', (default_user_id, mov_id, rat_score, rating_date, rat_id))
    except Exception as e:
        print(f"Error inserting rating for movie {mov_id}: {e}")

# Commit and close the connection
conn.commit()
cursor.close()
conn.close()

print("Data loading completed successfully.")