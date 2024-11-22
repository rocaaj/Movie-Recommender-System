"""
Author: Dario Santiago Lopez, Anthony Roca, ChatGPT 4o with Canvas
Date: November 7, 2024

Project: Gender Prediction for Movie Database

Description:
    This script predicts the gender of actors using the gender_guesser library. It extracts first names of actors from
    the SQLite database, predicts their gender, and stores these predictions in the database. Additionally,
    it evaluates the accuracy of these predictions.

Acknowledgments:
    This project was developed collaboratively by Dario Santiago Lopez, Anthony Roca, and ChatGPT 4o with Canvas.
    Special thanks to ChatGPT for assistance in developing and refining the prediction logic.
"""

import argparse
import sqlite3
import gender_guesser.detector as gender

# Create gender detector
gender_detector = gender.Detector()

def is_genderize_pred_empty(db_path):
    """Check if the genderize_pred column in the gender_prediction table is completely NULL."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) 
        FROM gender_prediction
        WHERE genderize_pred IS NOT NULL
    """)
    count = cursor.fetchone()[0]
    conn.close()
    return count == 0

def extract_first_names(db_path):
    """Extract first names of stars missing gender predictions."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT first_name
        FROM gender_prediction
        WHERE genderize_pred IS NULL
    """)
    stars = cursor.fetchall()
    conn.close()
    # Convert list of tuples to a list of names
    return [name[0] for name in stars]

def predict_gender(first_names):
    """Predict gender using the gender_guesser library."""
    gender_map = {
        'female': 1, 
        'male': 2, 
        'unknown': 3, 
        'andy': 3,  # Ambiguous names will be treated as unknown
        None: 3
    }
    predictions = []
    for first_name in first_names:
        try:
            prediction = gender_detector.get_gender(first_name)
            gender_value = gender_map.get(prediction, 3)
            predictions.append((first_name, gender_value))
        except Exception as e:
            print(f"Error predicting gender for {first_name}: {e}")
    return predictions

def store_predictions(db_path, predictions):
    """Store gender predictions in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    for first_name, gender_value in predictions:
        cursor.execute("""
            UPDATE gender_prediction
            SET genderize_pred = ?
            WHERE first_name = ?
        """, (gender_value, first_name))
    conn.commit()
    conn.close()

def evaluate_accuracy(db_path):
    """Evaluate the accuracy of gender predictions."""
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
    print(f"Gender prediction accuracy: {accuracy:.2f}%")

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Gender Prediction for Movie Database")
    parser.add_argument("db_file", help="Name of the SQLite database file")  # Path to `movies.db` file
    args = parser.parse_args()

    db_file = args.db_file

    if is_genderize_pred_empty(db_file):
        print("Genderize predictions are missing. Starting the extraction, prediction, and storage process...")
        
        # Extract first names
        first_names = extract_first_names(db_file)
        print(f"Extracted {len(first_names)} first names for prediction.")
        
        # Predict gender
        predictions = predict_gender(first_names)
        print(f"Total successful predictions: {len(predictions)}")
        
        # Store predictions
        if predictions:
            store_predictions(db_file, predictions)
            print("Predictions stored in the database.")
        else:
            print("No predictions were made to store in the database.")
    else:
        print("Genderize predictions already exist. Skipping extraction, prediction, and storage.")

    # Evaluate accuracy
    evaluate_accuracy(db_file)

if __name__ == "__main__":
    main()
