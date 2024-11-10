"""
Author: Anthony Roca
Date: October 25, 2024

Project: Movie Recommendation System

Description:
    This script implements a movie recommendation system based on a user's ratings and genre preferences. 
    It connects to an SQLite database to retrieve movie and rating information, calculates a user-preference 
    vector using the softmax normalization function, and recommends movies that the user has not yet rated.
    The system includes dynamic user selection, recommendation thresholding, and efficient data handling 
    for scalability and robustness.

Acknowledgments:
    Assistance provided by ChatGPT-4o in refining and debugging the code. Collaborated with Brayden Miller,
    Dario Santiago, and Osvaldo Hernandes for brainstorming and debugging.

    This project was developed as part of the CSC 321 course assignment on database-driven applications 
    and recommendation systems.

"""

import numpy as np
import sqlite3
import random
import time

def connect_to_db(db_path):
    con = None
    try:
        con = sqlite3.connect(db_path)
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
    
    return con

def get_user_ratings(con, user_id):
    """
    Retrieve user ratings for a given user from the SQLite database.

    Parameters:
    con (sqlite3.Connection): Database connection object.
    user_id (int): ID of the user for whom data is being retrieved.

    Returns:
    numpy array: A 1D array of the user's ratings for rated movies.
    """
    cursor = con.cursor()
    user_ratings_query = """
    SELECT r.mov_id, r.rat_score
    FROM rating as r
    WHERE r.user_id = ?
    """
    cursor.execute(user_ratings_query, (user_id,))
    user_ratings_data = cursor.fetchall()

    movie_ids = [row[0] for row in user_ratings_data]
    user_ratings = np.array([row[1] for row in user_ratings_data])

    return movie_ids, user_ratings

def get_genre_matrix(con, movie_ids):
    """
    Retrieve the genre matrix for given movies from the SQLite database.

    Parameters:
    con (sqlite3.Connection): Database connection object.
    movie_ids (list): List of movie IDs.

    Returns:
    numpy array: A 2D binary array representing genres of the rated movies (rows: movies, columns: genres).
    """
    cursor = con.cursor()

    # query to get all genres
    genres_query = """
    SELECT gen_id, gen_name FROM genre
    """
    cursor.execute(genres_query)
    genres = cursor.fetchall()
    genre_dict = {row[0]: index for index, row in enumerate(genres)}  # map genre ID to index

    # initialize genre matrix (movies x genres)
    genre_matrix = np.zeros((len(movie_ids), len(genre_dict)))

    # query to get the genres for each rated movie
    movie_genre_query = """
    SELECT mg.mov_id, mg.gen_id
    FROM movie_genre mg
    WHERE mg.mov_id IN ({})
    """.format(','.join('?' * len(movie_ids)))
    
    cursor.execute(movie_genre_query, movie_ids)
    movie_genre_data = cursor.fetchall()

    # populate the genre matrix
    for mov_id, gen_id in movie_genre_data:
        if mov_id in movie_ids:
            row_index = movie_ids.index(mov_id)
            col_index = genre_dict[gen_id]
            genre_matrix[row_index, col_index] = 1

    return genre_matrix

# user-preference function
def calculate_user_preference(user_ratings, genre_matrix):
    """
    Calculate a user preference vector from a user rating vector and a binary movie-genre matrix.
    
    Parameters:
    user_ratings (numpy array): A 1D array containing user ratings for each movie.
    genre_matrix (numpy array): A 2D binary array representing the genres for each movie (rows: movies, columns: genres).
    
    Returns:
    numpy array: A 1D array representing the user's preference for each genre.
    """
    # normalize user ratings by ensuring they are all positive and scale them between 0 and 5
    user_ratings = np.clip(user_ratings, 0, 5)
    
    # compute user preference vector by averaging genre columns weighted by the ratings
    user_preference = np.dot(user_ratings, genre_matrix)  # weighted sum of genres

    # normalize preferences only if the sum of ratings is not zero
    rating_sum = np.sum(user_ratings)
    if rating_sum > 0:
        user_preference = user_preference / rating_sum
    else:
        user_preference = np.zeros_like(user_preference)  # set preferences to zero if no ratings are given

    return user_preference

# user-recommender function
def generate_recommendation(user_id, user_preference, genre_matrix, con):
    """
    Generate a recommendation vector using the user preference vector and the binary movie-genre matrix.
    
    Parameters:
    user_preference (numpy array): A 1D array representing the user's preference for each genre.
    genre_matrix (numpy array): A 2D binary array representing the genres for each movie (rows: movies, columns: genres).
    
    Returns:
    numpy array: A 1D array containing recommendation scores for each movie.
    """
    
    create_table_query = """CREATE TABLE IF NOT EXISTS user_recommendations (
    user_id INT NOT NULL,
    mov_id INT NOT NULL,
    rec_score FLOAT NOT NULL,
    PRIMARY KEY (user_id, mov_id),
    FOREIGN KEY (user_id) REFERENCES rating(user_id),
    FOREIGN KEY (mov_id) REFERENCES movie(mov_id)
    );"""

    cursor = con.cursor()
    cursor.execute(create_table_query)

    # Check if recommendations already exist for the user
    cursor.execute("SELECT user_id, mov_id, rec_score FROM user_recommendations WHERE user_id = ? ORDER BY rec_score DESC LIMIT 5",
                   (user_id,))
    recommendations = cursor.fetchall()

    if not recommendations:  # if no recommendations exist, compute and store them
        # compute recommendation vector by dot product of user preference and movie genres
        recommendation_vector = np.dot(genre_matrix, user_preference)

        # apply softmax to convert scores to probabilities
        exp_scores = np.exp(recommendation_vector)
        recommendation_probs = exp_scores / np.sum(exp_scores)

        # Store recommendations in the user_recommendations table
        cursor.executemany(
            "INSERT OR REPLACE INTO user_recommendations (user_id, mov_id, rec_score) VALUES (?, ?, ?)", recommendations
        )
        con.commit()
    else:
        recommendation_probs = np.array([rec[1] for rec in recommendations])
    return recommendation_probs

def get_user_ratings(con, user_id):
    """
    Retrieve the ratings for movies rated by the user.

    Parameters:
    con (sqlite3.Connection): Database connection object.
    user_id (int): ID of the user for whom data is being retrieved.

    Returns:
    numpy array: A 1D array of the user's ratings for rated movies.
    """
    cursor = con.cursor()
    cursor.execute("SELECT mov_id, rat_score FROM rating WHERE user_id = ?", (user_id,))
    rated_movies_data = cursor.fetchall()
    
    user_ratings = np.array([row[1] for row in rated_movies_data])
    return user_ratings, [row[0] for row in rated_movies_data]

def get_rated_genre_matrix(con, rated_movie_ids):
    """
    Retrieve the genre matrix for the movies rated by the user.

    Parameters:
    con (sqlite3.Connection): Database connection object.
    rated_movie_ids (list): List of movie IDs rated by the user.

    Returns:
    numpy array: A 2D binary array representing genres of the rated movies (rows: movies, columns: genres).
    """
    cursor = con.cursor()

    # fetch all genre IDs to build genre dictionary
    cursor.execute("SELECT gen_id FROM genre")
    genre_ids = [row[0] for row in cursor.fetchall()]
    genre_dict = {gen_id: index for index, gen_id in enumerate(genre_ids)}

    # fetch all movie-genre associations
    cursor.execute("SELECT mov_id, gen_id FROM movie_genre")
    all_movie_genres = cursor.fetchall()

    # initialize the genre matrix for rated movies
    rated_genre_matrix = np.zeros((len(rated_movie_ids), len(genre_dict)))

    # populate the genre matrix for rated movies
    for mov_id, gen_id in all_movie_genres:
        if mov_id in rated_movie_ids:
            row_index = rated_movie_ids.index(mov_id)
            col_index = genre_dict[gen_id]
            rated_genre_matrix[row_index, col_index] = 1

    return rated_genre_matrix

def get_unrated_genre_matrix(con, rated_movie_ids):
    """
    Retrieve the genre matrix for the movies not rated by the user.

    Parameters:
    con (sqlite3.Connection): Database connection object.
    rated_movie_ids (list): List of movie IDs rated by the user.

    Returns:
    numpy array: A 2D binary array representing genres of the unrated movies (rows: movies, columns: genres).
    """
    cursor = con.cursor()

    # fetch all genre IDs to build genre dictionary
    cursor.execute("SELECT gen_id FROM genre")
    genre_ids = [row[0] for row in cursor.fetchall()]
    genre_dict = {gen_id: index for index, gen_id in enumerate(genre_ids)}

    # movies not rated by the user
    cursor.execute("SELECT mov_id FROM movie WHERE mov_id NOT IN ({})".format(
        ','.join('?' * len(rated_movie_ids))
    ), rated_movie_ids)
    unrated_movie_ids = [row[0] for row in cursor.fetchall()]

    # fetch all movie-genre associations
    cursor.execute("SELECT mov_id, gen_id FROM movie_genre")
    all_movie_genres = cursor.fetchall()

    # initialize the genre matrix for unrated movies
    unrated_genre_matrix = np.zeros((len(unrated_movie_ids), len(genre_dict)))

    # populate the genre matrix for unrated movies
    for mov_id, gen_id in all_movie_genres:
        if mov_id in unrated_movie_ids:
            row_index = unrated_movie_ids.index(mov_id)
            col_index = genre_dict[gen_id]
            unrated_genre_matrix[row_index, col_index] = 1

    return unrated_genre_matrix

