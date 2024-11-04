CREATE TABLE movie(
  mov_id INT PRIMARY KEY,
  mov_orig_title VARCHAR(256) NOT NULL,
  mov_eng_title VARCHAR(256) NOT NULL);
CREATE TABLE genre(
  gen_id INT PRIMARY KEY,
  gen_name VARCHAR(256) UNIQUE NOT NULL
);
CREATE TABLE movie_genre(
  mov_id INT,
  gen_id INT REFERENCES genre,
  PRIMARY KEY(mov_id, gen_id)
  FOREIGN KEY (mov_id) REFERENCES movies (movie_id),
  FOREIGN KEY (gen_id) REFERENCES genre (genre_id)
);
CREATE TABLE rating(
  user_id INT NOT NULL,
  mov_id INT NOT NULL,
  rat_score FLOAT NOT NULL,
  PRIMARY KEY(user_id, mov_id)
  FOREIGN KEY (mov_id) REFERENCES movie(mov_id)
);
CREATE TABLE user_recommendations (
    user_id INT NOT NULL,
    mov_id INT NOT NULL,
    rec_score FLOAT NOT NULL,
    PRIMARY KEY (user_id, mov_id),
    FOREIGN KEY (user_id) REFERENCES rating(user_id),
    FOREIGN KEY (mov_id) REFERENCES movie(mov_id)
    );