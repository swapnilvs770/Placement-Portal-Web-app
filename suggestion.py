
import pandas as pd
import numpy as np
import joblib
import pymysql
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import shared_data
loaded_model = joblib.load("company_recommendation_model.pkl")

# Load the saved vectorizer
loaded_vectorizer = joblib.load("skills_vectorizer.pkl")
print(shared_data.my_skills)
# Predict for a new skill set
new_skills = ["Python Flask Sql webdev cpp c ml image_processing"]
new_X = loaded_vectorizer.transform(new_skills)  # Convert skills to numerical form
probabilities = loaded_model.predict_proba(new_X)

# Get company names from the model's classes
companies = loaded_model.classes_

# Sort companies by highest probability
sorted_indices = np.argsort(probabilities[0])[::-1]  # Sort in descending order
sorted_companies = [(companies[i], probabilities[0][i]) for i in sorted_indices]

# Print all possible recommendations with probabilities
dict1={}

top_companies = []  # List to store company-probability data

for company, prob in sorted_companies[:20]:
    # print(f"{company}: {prob*100:.2f}%")
    proba = round(float(prob * 100), 2) 
    dict1 = {'Company': company, 'Probability': proba}  
    top_companies.append(dict1)  # Store each dictionary in a list

# Now, `top_companies` holds the top 20 companies with their probabilities.

