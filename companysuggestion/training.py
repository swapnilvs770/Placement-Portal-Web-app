import pandas as pd
import numpy as np
import joblib
import pymysql
import os
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score


def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password=os.getenv("DB_PASSWORD", "Amar@3142"),  # Use env variable for security
        database='placementdb',
        cursorclass=pymysql.cursors.DictCursor
    )
conn = get_db_connection()
cursor = conn.cursor()
cursor.execute("SELECT companydetails.Company , skills.Skill   from skills join companydetails on companydetails.CompanyCode = skills.CompanyCode;")
data = cursor.fetchall()



# Dictionary to store combined results
combined_data = defaultdict(list)

# Iterate over the list and group by 'Company'
for entry in data:
    combined_data[entry['Company']].append(entry['Skill'])

# Convert back to a list of dictionaries
result = [{'Company': company, 'Skills': skills} for company, skills in combined_data.items()]

# Output the combined list



# Convert to DataFrame
df = pd.DataFrame(result)

df["Skills"] = df["Skills"].apply(lambda x: " ".join(x)) 

print(df)
# Initialize TF-IDF Vectorizer
vectorizer = TfidfVectorizer()

# Convert skills into numerical form
X = vectorizer.fit_transform(df["Skills"]).toarray()

# Extract target labels (Company names)
y = df["Company"]

# Split data into 80% training and 20% testing
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize the model
model = RandomForestClassifier(n_estimators=100, random_state=42)

# Train the model
model.fit(X_train, y_train)

# Make predictions on test data
y_pred = model.predict(X_test)

# Calculate accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {accuracy * 100:.2f}%")

# New candidate's skills
new_skills = ["C++"]

# Convert skills to TF-IDF format
new_X = vectorizer.transform(new_skills).toarray()

# Predict the best company
predicted_company = model.predict(new_X)
print("Recommended Company:", predicted_company)

joblib.dump(model, "company_recommendation_model.pkl")
joblib.dump(vectorizer, "skills_vectorizer.pkl")

