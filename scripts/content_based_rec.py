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

# scrape user_ratings and genre matrix from db
def get_user_data_from_db(con, user_id):
    """
    Retrieve user ratings and movie-genre matrices for a given user from the SQLite database.

    Parameters:
    db_path (str): Path to the SQLite database.
    user_id (int): ID of the user for whom data is being retrieved.

    Returns:
    user_ratings (numpy array): A 1D array of the user's ratings for rated movies.
    genre_matrix (numpy array): A 2D binary array representing genres of the rated movies (rows: movies, columns: genres).
    """
    cursor = con.cursor()
    
    # query to get the user's ratings
    user_ratings_query = """
    SELECT r.mov_id, r.rat_score
    FROM rating as r
    WHERE r.user_id = ?
    """
    cursor.execute(user_ratings_query, (user_id,))
    user_ratings_data = cursor.fetchall()

    # extract movie IDs and ratings
    movie_ids = [row[0] for row in user_ratings_data]
    user_ratings = np.array([row[1] for row in user_ratings_data])

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

    
    return user_ratings, genre_matrix

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

def get_user_movies_data(con, user_id):
    """
    Retrieve movies rated by the user, movies not rated by the user, and their genres.

    Parameters:
    db_path (str): Path to the SQLite database.
    user_id (int): ID of the user for whom data is being retrieved.

    Returns:
    user_ratings (numpy array): A 1D array of the user's ratings for rated movies.
    rated_genre_matrix (numpy array): A 2D binary array representing genres of the rated movies (rows: movies, columns: genres).
    unrated_genre_matrix (numpy array): A 2D binary array representing genres of the unrated movies (rows: movies, columns: genres).
    """
    cursor = con.cursor()

    # fetch all movie IDs and genres
    cursor.execute("SELECT mov_id, gen_id FROM movie_genre")
    all_movie_genres = cursor.fetchall()

    # fetch all genre IDs to build genre dictionary
    cursor.execute("SELECT gen_id FROM genre")
    genre_ids = [row[0] for row in cursor.fetchall()]
    genre_dict = {gen_id: index for index, gen_id in enumerate(genre_ids)}

    # movies rated by the user
    cursor.execute("SELECT mov_id, rat_score FROM rating WHERE user_id = ?", (user_id,))
    rated_movies_data = cursor.fetchall()
    rated_movie_ids = [row[0] for row in rated_movies_data]
    user_ratings = np.array([row[1] for row in rated_movies_data])

    # movies not rated by the user
    cursor.execute("SELECT mov_id FROM movie WHERE mov_id NOT IN ({})".format(
        ','.join('?' * len(rated_movie_ids))
    ), rated_movie_ids)
    unrated_movie_ids = [row[0] for row in cursor.fetchall()]

    # initialize genre matrices for rated and unrated movies
    rated_genre_matrix = np.zeros((len(rated_movie_ids), len(genre_dict)))
    unrated_genre_matrix = np.zeros((len(unrated_movie_ids), len(genre_dict)))

    # populate genre matrices for rated movies
    for mov_id, gen_id in all_movie_genres:
        if mov_id in rated_movie_ids:
            row_index = rated_movie_ids.index(mov_id)
            col_index = genre_dict[gen_id]
            rated_genre_matrix[row_index, col_index] = 1
        elif mov_id in unrated_movie_ids:
            row_index = unrated_movie_ids.index(mov_id)
            col_index = genre_dict[gen_id]
            unrated_genre_matrix[row_index, col_index] = 1

    return user_ratings, rated_genre_matrix, unrated_genre_matrix

# random test single user
def test(con, user_id):
    cursor = con.cursor()
    
    user_ratings, genre_matrix = get_user_data_from_db(con, user_id)
    user_preference = calculate_user_preference(user_ratings, genre_matrix)
    recommendation_probs = generate_recommendation(user_id, user_preference, genre_matrix, con)

    top_movie_indices = recommendation_probs.argsort()[::-1][:5]

    # get the top movie IDs for recommendations
    unrated_movie_ids = [row[0] for row in cursor.execute("SELECT mov_id FROM movie WHERE mov_id NOT IN ({})".format(
        ','.join('?' * len(user_ratings))), user_ratings)]

    # retrieve movie titles for top recommendations
    top_movie_ids = [unrated_movie_ids[i] for i in top_movie_indices]
    cursor.execute("SELECT mov_eng_title FROM movie WHERE mov_id IN ({})".format(
        ','.join('?' * len(top_movie_ids))), top_movie_ids)
    top_movie_titles = [row[0] for row in cursor.fetchall()]

    return top_movie_titles

def stress_test(con, user_id):
    """
    Conducts a series of tests to study the scalability and limits of the recommender system.
    Outputs the time taken for each test case to demonstrate potential bottlenecks.

    Explanation of Each Test:
        Scalability with Increasing Movies:
        - Tests recommendation generation speed as the number of movies grows.
        - It queries different numbers of movies and times the recommendation function to assess scalability.
        
        Single Rated Movie:
        - Evaluates the system's behavior when a user has rated only one movie, which may lead to unbalanced or less meaningful preference vectors.
        
        Large Pool of Unrated Movies:
        - Simulates generating recommendations from a large pool of unrated movies (e.g., 5000).
        - This test identifies if the recommendation generation becomes sluggish with a substantial number of unrated movies to evaluate.
        
        Additional Features Beyond Genres:
        - Tests the system's ability to handle feature vectors with more dimensions, simulating the use of alternative features (e.g., director, year, actors) instead of just genres.
        - This assesses how well the system adapts to higher-dimensional feature data.
    
    Parameters:
    db_path (str): Path to the SQLite database.
    user_id (int): ID of the user for whom data is being retrieved.
    """
    print("Starting stress tests...\n")
    cursor = con.cursor()

    # Test 1: increasing number of movies
    print("Test 1: Scalability with an increasing number of movies")
    num_movies_list = [100, 500, 1000, 5000]  # number of movies to test
    for num_movies in num_movies_list:
        start_time = time.time()
        
        # query a limited number of movies
        cursor.execute("SELECT mov_id FROM movie LIMIT ?", (num_movies,))
        movie_ids = [row[0] for row in cursor.fetchall()]
        
        # generate a fake user preference for each movie
        genre_matrix = np.random.randint(0, 2, (num_movies, 10))  # Assume 10 genres for simplicity
        user_preference = np.random.rand(10)
        
        # generate recommendations
        recommendation_probs = generate_recommendation(user_id, user_preference, genre_matrix, con)
        end_time = time.time()
        
        print(f"Number of movies: {num_movies} - Time taken: {end_time - start_time:.4f} seconds")
        con.close()
    
    # Test 2: user with only 1 rated movie
    print("\nTest 2: User with only 1 rated movie")
    user_ratings = np.array([5])  # single rating
    genre_matrix = np.random.randint(0, 2, (1, 10))  # 1 movie with 10 genres
    start_time = time.time()
    user_preference = calculate_user_preference(user_ratings, genre_matrix)
    recommendation_probs = generate_recommendation(user_id, user_preference, genre_matrix, con)
    end_time = time.time()
    
    print(f"Single rated movie - Time taken: {end_time - start_time:.4f} seconds")
    
    # Test 3: large number of unrated movies
    print("\nTest 3: Evaluating large number of unrated movies")
    
    # assume we have already rated 10 movies and now have a large set of unrated movies
    cursor.execute("SELECT mov_id FROM movie WHERE mov_id NOT IN (SELECT mov_id FROM rating WHERE user_id = ?) LIMIT 5000", (user_id,))
    unrated_movie_ids = [row[0] for row in cursor.fetchall()]
    unrated_genre_matrix = np.random.randint(0, 2, (len(unrated_movie_ids), 10))  # 5000 unrated movies
    
    user_ratings, rated_genre_matrix = get_user_data_from_db(con, user_id)  # get user's actual ratings
    user_preference = calculate_user_preference(user_ratings, rated_genre_matrix)
    
    start_time = time.time()
    recommendation_probs = generate_recommendation(user_id, user_preference, unrated_genre_matrix, con)
    end_time = time.time()
    
    print(f"Evaluating 5000 unrated movies - Time taken: {end_time - start_time:.4f} seconds")
    con.close()

    # Test 4: alternative features (more features than just genres)
    print("\nTest 4: Using additional features beyond genres")
    num_features_list = [10, 50, 100]  # Increasing number of features
    for num_features in num_features_list:
        genre_matrix = np.random.randint(0, 2, (500, num_features))  # 500 movies with increased features
        user_preference = np.random.rand(num_features)
        
        start_time = time.time()
        recommendation_probs = generate_recommendation(user_id, user_preference, genre_matrix, con)
        end_time = time.time()
        
        print(f"Number of features: {num_features} - Time taken: {end_time - start_time:.4f} seconds")

    print("\nStress tests complete.")

def main():
    db_path = "movies.db"
    con = connect_to_db(db_path)
    cursor = con.cursor()
    
    #Start timing the algorithm 
    start_time = time.time()

    # testing 2 random users
    rand_test_id_1 = random.randint(1,270896)
    rand_test_id_2 = random.randint(1,270896)

    rec_titles_1 = test(con, rand_test_id_1)
    rec_titles_2 = test(con, rand_test_id_2)
    
    print("User ", rand_test_id_1, "'s recommended movies: ", rec_titles_1)
    print("User ", rand_test_id_2, "'s recommended movies: ", rec_titles_2)

    print()
    # testing 2 preselected users
    real_test_id_1 = 82899
    real_test_id_2 = 141520

    rec_titles_3 = test(con, real_test_id_1)
    rec_titles_4 = test(con, real_test_id_2)

    print("User ", real_test_id_1, "'s recommended movies: ", rec_titles_3)
    print("User ", real_test_id_2, "'s recommended movies: ", rec_titles_4)
    

    ## stress testing
    '''
    stress_test(con, 141520)
    '''

    # Stop timing the recommendation generation process
    end_time = time.time()
    execution_time = end_time - start_time

    # Print the time taken to generate recommendations
    print(f"\nTime taken to generate recommendations: {execution_time:.2f} seconds")

    # close the connection
    cursor.close()

    # ALWAYS close connection to database!
    con.close()

if __name__ == '__main__':
    main()