import suggestion
import pymysql
import os
from flask import Flask, render_template, request, jsonify, session ,send_from_directory,send_file , url_for , redirect
import random
import smtplib
from datetime import datetime, timedelta
import pymysql
import os
import app
import cryptography
import companysuggestion

app = Flask(__name__)
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password=os.getenv("DB_PASSWORD", "Amar@3142"),  # Use env variable for security
        database='placementdb',
        cursorclass=pymysql.cursors.DictCursor
    )

# @app.route('/')
def Company_suggestion():
    conn = get_db_connection()
    cursor = conn.cursor()
    cards = []
    for company_dict in suggestion.top_companies:
        
       cursor.execute("SELECT companydetails.company , companydetails.CompanyCode , placement_23_24.Salary_Per_LPA as Salary_Per_LPA_23_24 ,companydetails.logo_url FROM companydetails left join placement_23_24 on companydetails.CompanyCode = placement_23_24.CompanyCode where companydetails.Company = %s;",company_dict['Company'])
       data = cursor.fetchall()
       cards.append(data)
    cursor.close()
    conn.close()
    cards = [item[0] for item in cards]
    print(cards)
    # return render_template("Company-suggestion.html" , cards = cards)
    
Company_suggestion()
# if __name__ == "__main__":
#     app.run(debug=True)
