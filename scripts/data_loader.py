import sqlite3
import pandas as pd

con = sqlite3.connect("movie_recommender.db")
# instantiate a cursor object
cursor = con.cursor()

def extract_columns(df1, df2, column1, column2):
  df1_2 = df1[column1]
  df2_2 = df2[column2]
  extracted_df = pd.concat([df1_2, df2_2])

  return extracted_df


## delete existing table and its contents
# cur.execute('DROP TABLE "movie"')

# create relation schema for movie table with 3 attributes
# Create Movies table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Movies (
        MovieID INTEGER PRIMARY KEY,
        OriginalLanguage TEXT,
        OriginalTitle TEXT,
        EnglishTitle TEXT,
        Budget BIGINT,
        Revenue BIGINT,
        Homepage TEXT,
        Runtime INTEGER,
        ReleaseDate DATE,
        Genres TEXT,
        CastID TEXT,
        ProductionCompanies TEXT,
        ProductionCountries TEXT,
        SpokenLanguages TEXT
    )
''')

# Create Persons table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Persons (
        CastID TEXT PRIMARY KEY,
        MovieID INTEGER,
        Name TEXT,
        Gender INTEGER, 
        CharacterName TEXT,
        FOREIGN KEY (MovieID) REFERENCES Movies (MovieID)
    )
''')

# Create Ratings table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Ratings (
        UserID INTEGER,
        MovieID INTEGER,
        Rating REAL,
        RatingDate DATE,
        PRIMARY KEY (UserID, MovieID),
        FOREIGN KEY (MovieID) REFERENCES Movies (MovieID)
    )
''')

# Create Casts (plays in) table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS Casts (
        FOREIGN KEY (PersonID) REFERENCES Persons (PersonID)
        FOREIGN KEY (MovieID) REFERENCES Movies (MovieID)
    )
''')

# Commit table creation
cursor.commit()

# Load CSV files into pandas DataFrames
movies_df = pd.read_csv('Movies.csv')
persons_df = pd.read_csv('Persons.csv')
ratings_df = pd.read_csv('Ratings.csv')

# Insert data into Movies table
for index, row in movies_df.iterrows():
    cursor.execute('''
        INSERT OR IGNORE INTO Movies (MovieID, OriginalLanguage, OriginalTitle, EnglishTitle, Budget, Revenue, Homepage, Runtime, ReleaseDate, Genres, CastID, ProductionCompanies, ProductionCountries, SpokenLanguages)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        row['MovieID'],
        row['OriginalLanguage'],
        row['OriginalTitle'],
        row['EnglishTitle'],
        row['Budget'] if pd.notna(row['Budget']) else None,
        row['Revenue'] if pd.notna(row['Revenue']) else None,
        row['Homepage'] if pd.notna(row['Homepage']) else None,
        row['Runtime'] if pd.notna(row['Runtime']) else None,
        row['ReleaseDate'],
        row['Genres'],
        row['CastID'],
        row['ProductionCompanies'],
        row['ProductionCountries'],
        row['SpokenLanguages']
    ))

# Insert data into Persons table
for index, row in persons_df.iterrows():
    cursor.execute('''
        INSERT OR IGNORE INTO Persons (CastID, MovieID, Name, Gender, CharacterName)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        row['CastID'],
        row['MovieID'],
        row['Name'],
        row['Gender'] if pd.notna(row['Gender']) else None,
        row['Character']
    ))

# Insert data into Ratings table
for index, row in ratings_df.iterrows():
    cursor.execute('''
        INSERT OR IGNORE INTO Ratings (UserID, MovieID, Rating, RatingDate)
        VALUES (?, ?, ?, ?)
    ''', (
        row['UserID'],
        row['MovieID'],
        row['Rating'],
        row['Date']
    ))

extracted_data = extract_columns(movies_df, persons_df, "MovieID", "PersonsID")
unique_casts = extracted_data["MovieID", "PersonsID"].unique()

# Insert data into Casts table
for index, row in unique_casts.iterrows():
    cursor.execute('''
        INSERT OR IGNORE INTO Ratings (MovieID, PersonsID)
        VALUES (?, ?)
    ''', (
        row['MoviesID'],
        row['PersonsID']
    ))

# Commit data insertion
cursor.commit()

# Close the connection
cursor.close()

# ALWAYS close connection to database!
con.close()