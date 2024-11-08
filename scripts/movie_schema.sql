-- movie_schema.sql 
-- Authors: Anthony Roca, Dario Santiago Lopez, and ChatGPT-4o 
-- Overview: The following SQL script is used to integrate new data from IMBD's top 1000 movies dataset 
-- into our current data set from Assignment 2 

-- BEFORE YOU RUN THESE SCRIPTS CLEAR movies.db IF NEEDED
-- Step 1: Create 'movie' table to store basic movie details
CREATE TABLE movie (
    mov_id INT PRIMARY KEY,
    mov_orig_title VARCHAR(256) NOT NULL,
    mov_eng_title VARCHAR(256) NOT NULL,
    released_year INT, -- this and the following are part of imdb schema
    certificate VARCHAR(64),
    runtime INT,
    imdb_rating FLOAT CHECK (imdb_rating >= 0 AND imdb_rating <= 10),
    overview TEXT,
    meta_score INT CHECK (meta_score >= 0 AND meta_score <= 100),
    director VARCHAR(256),
    gross BIGINT CHECK (gross >= 0)
);

-- Step 2: Create 'genre' table to store genre details
CREATE TABLE genre (
    gen_id INT PRIMARY KEY,
    gen_name VARCHAR(256) UNIQUE NOT NULL
);

-- Step 3: Create 'movie_genre' table to link movies with multiple genres
CREATE TABLE movie_genre (
    mov_id INT,
    gen_id INT,
    PRIMARY KEY (mov_id, gen_id),
    FOREIGN KEY (mov_id) REFERENCES movie (mov_id),
    FOREIGN KEY (gen_id) REFERENCES genre (gen_id)
);

-- Step 4: Create 'rating' table to store user ratings for movies
CREATE TABLE rating (
    user_id INT NOT NULL,
    mov_id INT NOT NULL,
    rat_score FLOAT NOT NULL CHECK (rat_score >= 0 AND rat_score <= 5),
    PRIMARY KEY (user_id, mov_id),
    FOREIGN KEY (mov_id) REFERENCES movie (mov_id) ON DELETE CASCADE
);

-- Now we're updating the script to integrate fields from the imdb_top_1000.csv 
-- Step 5:Create 'star' table to store information about actors in movies
CREATE TABLE star (
    star_id INT PRIMARY KEY,
    star_name VARCHAR(256) UNIQUE NOT NULL
);

-- Step 6: Create 'movie_star' table to link movies with multiple stars
CREATE TABLE movie_star (
    mov_id INT,
    star_id INT,
    PRIMARY KEY (mov_id, star_id),
    FOREIGN KEY (mov_id) REFERENCES movie (mov_id) ON DELETE CASCADE,
    FOREIGN KEY (star_id) REFERENCES star (star_id) ON DELETE CASCADE
);

-- Step 7: Add necessary indexes to optimize performance
CREATE INDEX idx_movie_title ON movie (mov_orig_title);
CREATE INDEX idx_genre_name ON genre (gen_name);
CREATE INDEX idx_director_name ON movie (director);
CREATE INDEX idx_star_name ON star (star_name);