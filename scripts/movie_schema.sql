-- movie_schema.sql 
-- Authors: Anthony Roca, Dario Santiago Lopez, and ChatGPT-4o 
-- Date: November 7, 2024 
-- Updated: November 19, 2024
-- Overview: The following SQL script is used to integrate new data from IMBD's top 1000 movies dataset 
-- into our current data set from Assignment 2 and Assignment 4 

-- Acknowledgments:
-- This project was developed collaboratively by Anthony Roca, Dario Santiago Lopez, and ChatGPT-4o.
-- Special thanks to ChatGPT for assisting in refining the schema and ensuring data consistency throughout.

-- BEFORE YOU RUN THESE SCRIPTS CLEAR movies.db IF NEEDED
-- Step 1: Create 'movie' table to store basic movie details. If you are using movies.db from assignment 3 then 
-- just alter table movie and add the additional columns to the table
CREATE TABLE movie (
    mov_id INT PRIMARY KEY,
    mov_orig_title VARCHAR(256) NOT NULL,
    mov_eng_title VARCHAR(256) NOT NULL,
    released_year INT, -- this and the following are part of imdb schema
    certificate VARCHAR(64), -- may have to alter table
    runtime INT, -- may have to alter table
    imdb_rating FLOAT CHECK (imdb_rating >= 0 AND imdb_rating <= 10), -- may have to alter table
    overview TEXT, -- may have to alter table
    meta_score INT CHECK (meta_score >= 0 AND meta_score <= 100), -- may have to alter table
    director VARCHAR(256), -- may have to alter table
    gross BIGINT CHECK (gross >= 0), -- may have to alter table
    mov_homepage TEXT, -- was missing in assignment 4 (from assignment 2)
    mov_budget DECIMAL(15, 2) NOT NULL, -- was missing in assignment 4 (from assignment 2)
    mov_budget_class TEXT CHECK (mov_budget_class IN('low', 'medium', 'high')) 
    -- ^^^^^ was missing in assignment 4 (from assignment 2)
);
-- If you have to alter the table, uncomment the following queries.
-- ALTER TABLE movie ADD COLUMN released_year INT;
-- ALTER TABLE movie ADD COLUMN certificate VARCHAR(64);
-- ALTER TABLE movie ADD COLUMN runtime INT;
-- ALTER TABLE movie ADD COLUMN imdb_rating FLOAT CHECK (imdb_rating >= 0 AND imdb_rating <= 10);
-- ALTER TABLE movie ADD COLUMN overview TEXT;
-- ALTER TABLE movie ADD COLUMN meta_score INT CHECK (meta_score >= 0 AND meta_score <= 100);
-- ALTER TABLE movie ADD COLUMN director VARCHAR(256);
-- ALTER TABLE movie ADD COLUMN gross BIGINT CHECK (gross >= 0);
-- ALTER TABLE movie ADD COLUMN mov_homepage TEXT;
-- ALTER TABLE movie ADD COLUMN mov_budget DECIMAL(15, 2);
-- ALTER TABLE movie ADD COLUMN mov_budget_class TEXT CHECK (mov_budget_class IN ('low', 'medium', 'high'));

-- Step 2: Create 'genre' table to store genre details
CREATE TABLE genre (
    gen_id INT PRIMARY KEY,
    gen_name VARCHAR(256) UNIQUE NOT NULL
);

-- Step 3: Create 'movie_genre' table to link movies with multiple genres
CREATE TABLE movie_genre (
    mov_id INT,
    gen_id INT REFERENCES genre,
    PRIMARY KEY (mov_id, gen_id),
    FOREIGN KEY (mov_id) REFERENCES movie (mov_id),
    FOREIGN KEY (gen_id) REFERENCES genre (gen_id)
);

-- Step 4: Create 'rating' table to store user ratings for movies
CREATE TABLE rating (
    user_id INT NOT NULL,
    mov_id INT NOT NULL,
    rat_score FLOAT NOT NULL CHECK (rat_score >= 0 AND rat_score <= 5),
    rating_date DATE NOT NULL, -- missing in assignment 4 (from assignment 2) so you may have to alter table
    rat_id INT NOT NULL, -- missing in assignment 4 (from assignment 2) so you may have to alter table
    PRIMARY KEY (user_id, mov_id),  -- Composite primary key ensuring unique user-movie pair
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

-- Step 7: Create 'country' which was missing in assignment 4 (table originally from assignment 2)
CREATE TABLE country (
    country_code CHAR(2) PRIMARY KEY, 
    country_name TEXT NOT NULL
);

-- Step 8: Create 'movie_countries' which was missing in assignment 4 (table originally from assignment 2)
CREATE TABLE movie_countries (
    mov_id INTEGER, 
    country_code CHAR(2), 
    FOREIGN KEY (mov_id) REFERENCES movie(mov_id), 
    FOREIGN KEY (country_code) REFERENCES country(country_code), 
    PRIMARY KEY (mov_id, country_code)
);

-- Step 9: Create 'language' which was missing in assignment 4 (table originally from assignment 2)
CREATE TABLE language (
    lang_code CHAR(2) PRIMARY KEY, 
    eng_name TEXT NOT NULL 
);

-- Step 10: Create 'language' which was missing in assignment 4 (table originally from assignment 2)
CREATE TABLE movie_languages (
    mov_id INTEGER, 
    lang_code CHAR(2), 
    FOREIGN KEY (mov_id) REFERENCES movie(mov_id) ON DELETE CASCADE, 
    FOREIGN KEY (lang_code) REFERENCES language(lang_code), 
    PRIMARY KEY (mov_id, lang_code)
);

-- Step 11: Create 'actor' which was missing in assignment 4 (table originally from assignment 2)
-- we already had the table 'star' but that's specific to imdb's database. 
CREATE TABLE actor (
    act_id INTEGER PRIMARY KEY NOT NULL,
    act_name TEXT NOT NULL, 
    act_gender INTEGER CHECK(act_gender IN (1, 2, 3)),
    country_code CHAR(2), 
    FOREIGN KEY (country_code) REFERENCES country(country_code)
);

-- Step 12: Create 'cast' which was missing in assignment 4 (table originally from assignment 2)
-- we already had the table 'star' but that's specific to imdb's database
CREATE TABLE cast (
    mov_id INTEGER, 
    act_id INTEGER, 
    act_role TEXT NOT NULL,
    FOREIGN KEY (mov_id) REFERENCES movie(mov_id) ON DELETE CASCADE,
    FOREIGN KEY (act_id) REFERENCES actor(act_id) ON DELETE CASCADE,
    PRIMARY KEY (mov_id, act_id)
);

-- Step 13: Add necessary indexes to optimize performance
CREATE INDEX idx_movie_title ON movie (mov_orig_title);
CREATE INDEX idx_genre_name ON genre (gen_name);
CREATE INDEX idx_director_name ON movie (director);
CREATE INDEX idx_star_name ON star (star_name);
-- These are new indexes which were missing in assignment 4
CREATE INDEX idx_movie_id ON movie_genre (mov_id);
CREATE INDEX idx_genre_id ON movie_genre (gen_id);
CREATE INDEX idx_rating_mov_id ON rating (mov_id);
CREATE INDEX idx_rating_user_id ON rating (user_id);