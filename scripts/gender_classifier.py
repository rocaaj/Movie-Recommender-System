"""
Author: Dario Santiago Lopez, Anthony Roca, ChatGPT 4o with Canvas
Date: November 7, 2024

Project: Custom Gender Predictor for Movie Database

Description:
    This script trains a custom gender predictor based on the first names of actors in the movie database.
    It uses TF-IDF for feature engineering and Multinomial Naive Bayes for classification.
    The script includes hold-out validation to evaluate the custom predictor's performance
    and compares it with the baseline predictor (gender_guesser library).

Acknowledgments:
    This project was developed collaboratively by Dario Santiago Lopez, Anthony Roca, and ChatGPT 4o with Canvas.
    Special thanks to ChatGPT for assistance in developing and refining the prediction logic.
"""

import argparse
import sqlite3
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB

# Step 1: Data Preparation
def load_training_data(db_path):
    """
    Load training data with only known genders (1 for female, 2 for male).
    Extracts first names and corresponding gender labels from the gender_prediction table in the database.
    """
    conn = sqlite3.connect(db_path)
    query = """
        SELECT first_name, gender 
        FROM gender_prediction 
        WHERE gender IN (1, 2)
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Step 2: Feature Engineering - Create Vectorizer
def create_vectorizer():
    """
    Create a TF-IDF vectorizer to convert first names into character-based n-grams.
    The n-grams range from 2 to 4 characters, providing a robust feature representation for names.
    """
    return TfidfVectorizer(analyzer='char', ngram_range=(2, 4))

# Step 3: Feature Engineering - Transform Features
def transform_features(data, vectorizer):
    """
    Transform the first names into TF-IDF feature vectors using the provided vectorizer.
    """
    X = vectorizer.fit_transform(data['first_name'])
    return X

# Step 4: Data Splitting
def split_data(X, y):
    """
    Split the dataset into training and testing sets.
    This is an 80-20 split to ensure sufficient data for model training and evaluation.
    """
    return train_test_split(X, y, test_size=0.2, random_state=42)

# Step 5: Model Training
def train_model(X_train, y_train):
    """
    Train a Multinomial Naive Bayes classifier using the training data.
    The model learns to classify gender based on TF-IDF features of first names.
    """
    model = MultinomialNB()
    model.fit(X_train, y_train)
    return model

# Step 6: Test Set Prediction
def evaluate_gender_guesser_accuracy(db_path):
    """
    Evaluate the accuracy of gender predictions using the gender_guesser library.
    Compares predicted values in the genderize_pred column against the actual gender values.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) AS total,
            SUM(CASE WHEN genderize_pred = gender THEN 1 ELSE 0 END) AS correct
        FROM gender_prediction
        WHERE gender IS NOT NULL
    """)
    total, correct = cursor.fetchone()
    conn.close()
    accuracy = (correct / total) * 100 if total > 0 else 0
    print(f"Gender-Guesser prediction accuracy: {accuracy:.2f}%")
    return accuracy

# Step 7: Evaluate Multinomial NB Model Accuracy
def evaluate_multinomial_nb_accuracy(y_true, y_pred):
    """
    Evaluate the accuracy of the Multinomial Naive Bayes model.
    Compares the predicted gender values against the true labels for the test set.
    """
    correct_predictions = sum(1 for true, pred in zip(y_true, y_pred) if true == pred)
    total = len(y_true)
    accuracy = (correct_predictions / total) * 100 if total > 0 else 0
    print(f"Multinomial Naive Bayes prediction accuracy: {accuracy:.2f}%")
    return accuracy

# Step 8: Store Predictions in Database
def store_ml_predictions(db_path, first_names, predictions, predicted_probs, threshold=0.1):
    """
    Store Multinomial Naive Bayes gender predictions in the database with a confidence threshold.
    When the model is uncertain (probability difference is below the threshold), 
    the prediction is marked as 'uncertain' (3).
    """
    gender_map = {0: 1, 1: 2, None: 3}  # Mapping 0 to 'female' (1), 1 to 'male' (2), and None to 'unknown' (3)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for first_name, gender, probs in zip(first_names, predictions, predicted_probs):
        prob_female = probs[0]
        prob_male = probs[1]

        # Determine if the model is unsure by checking both probabilities and applying a balanced threshold
        if abs(prob_female - prob_male) < threshold:
            gender_value = 3  # uncertain
        else:
            # Assign based on the higher probability
            if prob_female > prob_male:
                gender_value = 1  # female
            else:
                gender_value = 2  # male

        # Debugging statement to print the prediction and probability
        print(f"Predicted gender for {first_name}: {gender_value} (prob_female: {prob_female:.2f}, prob_male: {prob_male:.2f})")
        
        try:
            cursor.execute("""
                UPDATE gender_prediction
                SET ml_pred = ?
                WHERE first_name = ?
            """, (gender_value, first_name))
        except sqlite3.IntegrityError as e:
            print(f"Error storing prediction for {first_name}: {e}")
    
    conn.commit()
    conn.close()
    print("Multinomial Naive Bayes gender predictions stored in the database.")

# Step 9: Compare Baseline Accuracies
def baseline_comparison(gender_guesser_accuracy, multinomial_nb_accuracy):
    """
    Compare the accuracy of the gender-guesser baseline with the Multinomial Naive Bayes model.
    Outputs the accuracy for both models and indicates which one performed better.
    """
    print("\nBaseline Comparison:")
    print(f"Gender-Guesser Accuracy: {gender_guesser_accuracy:.2f}%")
    print(f"Multinomial Naive Bayes Accuracy: {multinomial_nb_accuracy:.2f}%")

    if multinomial_nb_accuracy > gender_guesser_accuracy:
        print("The Multinomial Naive Bayes model performed better than the gender-guesser baseline.")
    elif multinomial_nb_accuracy < gender_guesser_accuracy:
        print("The gender-guesser baseline performed better than the Multinomial Naive Bayes model.")
    else:
        print("Both models performed equally well.")


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Gender Prediction for Movie Database")
    parser.add_argument("db_file", help="Name of the SQLite database file")  # Path to `movies.db` file
    args = parser.parse_args()

    db_file = args.db_file

    # Step 1: Evaluate Gender-Guesser Baseline Accuracy
    print("\nStep 1: Evaluating Gender-Guesser Baseline Accuracy...")
    gender_guesser_accuracy = evaluate_gender_guesser_accuracy(db_file)

    # Step 2: Load Training Data
    print("\nStep 2: Loading Training Data...")
    df = load_training_data(db_file)
    first_names = df['first_name'].tolist()
    gender_labels = df['gender'].tolist()

    # Step 3: Split Data into Training and Testing Sets (80-20 Split)
    print("\nStep 3: Splitting Data into Training and Testing Sets...")
    X_train, X_test, y_train, y_test = train_test_split(first_names, gender_labels, test_size=0.2, random_state=42)

    # Step 4: Feature Engineering using Character-Based TF-IDF Vectorizer
    print("\nStep 4: Feature Engineering using TF-IDF Vectorizer...")
    vectorizer = create_vectorizer()
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    # Step 5: Train Multinomial Naive Bayes Classifier
    print("\nStep 5: Training Multinomial Naive Bayes Classifier...")
    model = train_model(X_train_tfidf, y_train)

    # Step 6: Predict on Test Set
    print("\nStep 6: Making Predictions on Test Set...")
    y_pred = model.predict(X_test_tfidf)

    # Step 7: Evaluate Multinomial Naive Bayes Accuracy
    print("\nStep 7: Evaluating Multinomial Naive Bayes Accuracy...")
    multinomial_nb_accuracy = evaluate_multinomial_nb_accuracy(y_test, y_pred)

    # Step 8: Store ML Predictions for All First Names
    print("\nStep 8: Making Predictions for All First Names and Storing Them...")
    X_all_tfidf = vectorizer.transform(first_names)
    y_all_pred = model.predict(X_all_tfidf)
    predicted_probs = model.predict_proba(X_all_tfidf)
    store_ml_predictions(db_file, first_names, y_all_pred, predicted_probs)

    # Step 9: Compare Baseline Accuracy and Multinomial Naive Bayes Accuracy
    print("\nStep 9: Comparing Baseline Accuracy and Multinomial Naive Bayes Accuracy...")
    baseline_comparison(gender_guesser_accuracy, multinomial_nb_accuracy)

if __name__ == "__main__":
    main()