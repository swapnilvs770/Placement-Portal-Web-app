
import pandas as pd
import numpy as np
import joblib
import pymysql
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
loaded_model = joblib.load("company_recommendation_model.pkl")

# Load the saved vectorizer
loaded_vectorizer = joblib.load("skills_vectorizer.pkl")

# Predict for a new skill set
new_skills = ["devoops, dsa, full stack, cyber security"]
new_X = loaded_vectorizer.transform(new_skills)  # Convert skills to numerical form
probabilities = loaded_model.predict_proba(new_X)

# Get company names from the model's classes
companies = loaded_model.classes_

# Sort companies by highest probability
sorted_indices = np.argsort(probabilities[0])[::-1]  # Sort in descending order
sorted_companies = [(companies[i], probabilities[0][i]) for i in sorted_indices]

# Print all possible recommendations with probabilities
print("🔹 Recommended Companies (Ranked by Probability):")
for company, prob in sorted_companies[:20]:
    print(f"{company}: {prob*100:.2f}%")

