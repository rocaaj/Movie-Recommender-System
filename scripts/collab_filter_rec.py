"""
Author: Dario Santiago Lopez, Anthony Roca, ChatGPT 4o with Canvas
Date: November 7, 2024

Project: Collaborative Filtering Movie Recommendation System

Description:
    This script implements a collaborative filtering approach for movie recommendations
    using user ratings data from the movies.db SQLite database. It calculates user similarities
    based on ratings and recommends movies to a specific user based on the preferences of similar users.

Acknowledgments:
    This project was developed collaboratively by Dario Santiago Lopez, Anthony Roca, and ChatGPT 4o with Canvas.
    Special thanks to ChatGPT for assistance in refining the implementation and improving recommendation logic.
"""

import argparse
import pandas as pd
import sqlite3
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import time 

# Set up argument parser
parser = argparse.ArgumentParser(description="Collaborative Filtering Movie Recommender using scikit-learn")
parser.add_argument("db_file", help="Name of the database file")  # Path to `movies.db` file
parser.add_argument("user_id", type=int, help="User ID to generate recommendations for")
parser.add_argument("--type", choices=["user", "item"], default="user", help="Type of collaborative filtering: 'user' or 'item'")
args = parser.parse_args()

print("\nArgs received from command line") 

# Extract arguments
db_file = args.db_file
user_id = args.user_id
cf_type = args.type

# Connect to the SQLite database
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

print(f"Connected to database: {db_file}")

# Load data from 'rating' table into a DataFrame
query = '''
    SELECT user_id, mov_id, rat_score
    FROM rating
'''
ratings_df = pd.read_sql_query(query, conn)

# Create a user-item matrix
user_item_matrix = ratings_df.pivot(index='user_id', columns='mov_id', values='rat_score').fillna(0)

#Start timing the algorithm 
start_time = time.time()

if cf_type == "user":
    # User-User Collaborative Filtering
    print(f"\nRunning User-User Collaborative Filtering for User ID: {user_id}")

    # Calculate user similarity using cosine similarity
    user_similarity = cosine_similarity(user_item_matrix)

    # Convert similarity to DataFrame for easier manipulation
    user_similarity_df = pd.DataFrame(user_similarity, index=user_item_matrix.index, columns=user_item_matrix.index)

    # Find similar users for the given user_id
    similar_users = user_similarity_df[user_id].sort_values(ascending=False).index.tolist()

    # Get a list of movies rated by the given user
    user_rated_movies = set(user_item_matrix.columns[user_item_matrix.loc[user_id] > 0])

    # Generate recommendations based on similar users
    recommended_movies = set()
    print("\nEntering for loop")

    for similar_user in similar_users:
        if similar_user == user_id:
            continue
        # Get movies rated by similar users that the current user hasn't rated
        unrated_movies = set(user_item_matrix.columns[user_item_matrix.loc[similar_user] > 0]) - user_rated_movies
        recommended_movies.update(unrated_movies)
        # Limit recommendations to 5 movies
        if len(recommended_movies) >= 5:
            break

    print("\nExited for loop successfully")

elif cf_type == "item":
    # Item-Item Collaborative Filtering
    print(f"\nRunning Item-Item Collaborative Filtering for User ID: {user_id}")

    # Transpose user-item matrix to create item-user matrix
    item_user_matrix = user_item_matrix.T

    # Calculate item similarity using cosine similarity
    item_similarity = cosine_similarity(item_user_matrix)

    # Convert similarity to DataFrame for easier manipulation
    item_similarity_df = pd.DataFrame(item_similarity, index=item_user_matrix.index, columns=item_user_matrix.index)

    # Get a list of movies rated by the given user
    user_rated_movies = user_item_matrix.loc[user_id]
    rated_movies = user_rated_movies[user_rated_movies > 0].index.tolist()

    # Generate recommendations based on similar items
    recommended_movies = set()
    for rated_movie in rated_movies:
        # Find similar movies to the ones the user has already rated
        similar_movies = item_similarity_df[rated_movie].sort_values(ascending=False).index.tolist()
        # Add similar movies that the user hasn't already rated
        for movie in similar_movies:
            if movie not in rated_movies:
                recommended_movies.add(movie)
            if len(recommended_movies) >= 5:
                break
        if len(recommended_movies) >= 5:
            break

# Stop timing the recommendation generation process
end_time = time.time()
execution_time = end_time - start_time

# Display recommended movies
if recommended_movies:
    cursor.execute('SELECT mov_id, mov_orig_title FROM movie WHERE mov_id IN ({})'.format(
        ','.join(['?'] * len(recommended_movies))
    ), list(recommended_movies))
    recommended_movies_info = cursor.fetchall()

    print(f"\nRecommended movies for user {user_id}:")
    for movie in recommended_movies_info:
        print(f"- {movie[1]} (Movie ID: {movie[0]})")
else:
    print(f"No recommendations available for user {user_id}")

# Print the time taken to generate recommendations
print(f"\nTime taken to generate recommendations: {execution_time:.2f} seconds")

# Close the connection
cursor.close()
conn.close()

print("\nRecommendation generation completed successfully.")
