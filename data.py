import pandas as pd

# Load CSV, treating first row as data
df = pd.read_csv("Civil_data.csv", header=0)

# Rename columns manually based on what we saw
df.columns = ["Adm_no", "Student_Name", "Gender", "Mobile_no", "EmailId"]

# Add Password and UserID columns
df["Password"] = "password123"
df["UserID"] = df["Adm_no"]

# Fill missing values (especially emails) with empty strings
df = df.fillna("")

# Generate SQL insert queries
queries = []
for _, row in df.iterrows():
    query = f"""INSERT INTO User (UserID, Password, EmailId, Mobile_no, Student_Name, Gender , Branch)
VALUES ('{row["UserID"]}', '{row["Password"]}', '{row["EmailId"]}', '{row["Mobile_no"]}', '{row["Student_Name"]}', '{row["Gender"]}' , '{'CIVIL'}');"""
    queries.append(query)

# Output all the queries
for q in queries:
    print(q)
