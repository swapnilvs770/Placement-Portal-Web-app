from flask import Flask, render_template, request, jsonify, session , send_from_directory , send_file , url_for , redirect
import random
import smtplib
from datetime import datetime, timedelta 
import pymysql
import os

import cryptography
import companysuggestion
import suggestion
import jwt
from functools import wraps
from flask import make_response
from flask import flash 
from flask import jsonify
import pandas as pd
import io
import openpyxl
import pymysql
import os

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)


app.config['SECRET_KEY'] = "my_super_secret_key_12345"
my_skills = []

print(os.getenv("PLACEMENT_DB_USER"))
print(os.getenv("PLACEMENT_DB_PASSWORD"))

# MySQL Database Configuration
def get_placement_db():
    return pymysql.connect(
        host=os.getenv("PLACEMENT_DB_HOST"),
        user=os.getenv("PLACEMENT_DB_USER"),
        password=os.getenv("PLACEMENT_DB_PASSWORD"),
        database=os.getenv("PLACEMENT_DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor
    )
# Database Connection Function


def get_db_connection():
    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        cursorclass=pymysql.cursors.DictCursor
    )


def get_cards():
    connection = None
    """Fetch card data from MySQL database."""
    connection = get_placement_db()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("SELECT companydetails.company , companydetails.CompanyCode , placement_23_24.Salary_Per_LPA as Salary_Per_LPA_23_24 ,companydetails.logo_url FROM companydetails left join placement_23_24 on companydetails.CompanyCode = placement_23_24.CompanyCode ;")
    data = cursor.fetchall()
    
    cursor.close()
    if connection:
        connection.close()
    
    return data


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.args.get('token') or session.get('token')  # Get token from URL or session

        if not token:
            return redirect(url_for('login'))  # Redirect if token is missing

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            session['user_id'] = data["user_id"]  # Store user ID in session
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Session expired. Please log in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid authentication token."}), 401

        return f(*args, **kwargs)  # Call the original function

    return decorated_function


@app.route('/company/<int:company_id>')
@login_required
def company_info(company_id):
    """Fetch and display company details based on ID"""
    connection = get_placement_db()
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM companydetails WHERE CompanyCode = %s", (company_id,))
    company_details = cursor.fetchone()
    cursor.execute("SELECT * from placement_23_24 WHERE CompanyCode = %s", (company_id,))
    placement_details23_24 = cursor.fetchone()
    cursor.execute("SELECT * from placement_22_23 WHERE CompanyCode = %s", (company_id,))
    placement_details22_23 = cursor.fetchone()
    cursor.execute("SELECT *  FROM skills WHERE CompanyCode = %s", (company_id,))
    skill_details = cursor.fetchall()
    if connection:
        connection.close()
    
    
    if not company_details :
        return "Company not found", 404
    
    return render_template('company.html', basicinfo=company_details , skill_details = skill_details ,placement_details22_23 = placement_details22_23 , placement_details23_24 =  placement_details23_24 )


def generate_otp():
    return str(random.randint(100000, 999999))



@app.route('/send_otp', methods=["POST"])
def send_otp_email():
    data = request.json
    user_id = data.get("UserId")
    new_password = data.get("newpass")

    if not user_id or not new_password:
        return jsonify({"error": "User ID and new password are required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT EmailID FROM User WHERE UserId = %s", (user_id,))
        result = cursor.fetchone()
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

    if not result:
        return jsonify({"error": "User ID not found"}), 404

    receiver_email = result['EmailID']

    sender_email = "festa24.gcek@gmail.com"
    sender_password = 'uwww uykl cybj mepk'# Use env variable for security
    otp = generate_otp()

    # Store OTP and password in session (valid for 5 minutes)
    session["otp"] = otp
    session["otp_expiry"] = (datetime.now() + timedelta(minutes=5)).timestamp()
    session["user_id"] = user_id
    session["new_password"] = new_password

    subject = "Your OTP for Password Reset"
    body = f"Your OTP for password reset is: {otp}. It will expire in 5 minutes."
    message = f"Subject: {subject}\n\n{body}"

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message)

        return jsonify({
            "message": f"OTP sent to {receiver_email}!",
            "email": receiver_email
        })
    except Exception as e:
        return jsonify({"error": f"Failed to send email: {str(e)}"}), 500


@app.route('/verify_otp', methods=["POST"])
def verify_otp():
    data = request.json
    user_otp = data.get("otp")

    if not session.get("otp") or not session.get("user_id"):
        return jsonify({"success": False, "error": "No OTP found. Request a new one."}), 400

    if datetime.now().timestamp() > session.get("otp_expiry", 0):
        session.clear()
        return jsonify({"success": False, "error": "OTP expired. Request a new one."}), 400

    if session["otp"] != user_otp:
        return jsonify({"success": False, "error": "Invalid OTP"}), 400

    user_id = session.pop("user_id", None)
    new_password = session.pop("new_password", None)

    if not user_id or not new_password:
        return jsonify({"success": False, "error": "Invalid session data. Please retry."}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE User SET password = %s WHERE UserId = %s", (new_password, user_id))
        conn.commit()
    except Exception as e:
        return jsonify({"success": False, "error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

    session.clear()
    return jsonify({"success": True, "message": "Password updated successfully! You can now log in."})


@app.route('/student_login')
def student_login():
    return render_template("login_custume.html")


@app.route('/password_reset')
def password_reset():
    return render_template("Pass_Reset.html")


@app.route('/')
def index():
    connection = None
    try:
        connection = get_placement_db()
        cursor = connection.cursor()
        cursor.execute("SELECT sum(No_Of_Offers) FROM placement_23_24 ;")
        no_offers = cursor.fetchone()
        cursor.execute("SELECT count(CompanyCode) FROM placement_23_24 ;")
        no_company = cursor.fetchone()
        connection.commit()
        no_company = int(no_company['count(CompanyCode)'])
        no_offers  = int(no_offers['sum(No_Of_Offers)'])
    except Exception as e:
        return jsonify({"success": False, "error": f"Database error: {str(e)}"}), 500
    finally:
        if connection:
            connection.close()
    return render_template("index.html" , no_offers = no_offers ,  no_company = no_company)

# @app.route('/login', methods=['POST'])
# def login():
#     user_id = request.form.get('user_id', type=int)  # Ensure input is an integer
#     password = request.form.get('password')

#     if not user_id or not password:
#         return render_template('login.html', error="User ID and Password are required")

#     try:
#         connection = get_db_connection()
#         with connection.cursor() as cursor:
#             # Ensure column names match exactly
#             cursor.execute("SELECT * FROM passwords WHERE UserID = %s AND Password = %s", (user_id, password))
#             user = cursor.fetchone()

#         if user:
#             print(f"Login successful for user_id: {user['UserID']}")
#             session['user_id'] = user['UserID']  # Ensure consistent casing
#             return redirect(url_for('student_page'))

#         return render_template('login.html', error="Invalid credentials")

#     except Exception as e:
#         print(f"Error: {str(e)}")  # Debugging logs
#         return render_template('login.html', error="Internal Server Error")

#     finally:
#         if connection:
#             connection.close()
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Renders the login form on a GET request
    if request.method == 'GET':
        return render_template("Login_custume.html")

    # Handles form submission on a POST request
    if request.method == 'POST':
        # 1. Retrieve form data from Login_custume.html
        user_identifier = request.form.get("User")
        password = request.form.get("pass")
        role = request.form.get("role")

        # 2. Basic validation to ensure all fields are filled
        if not all([user_identifier, password, role]):
            flash("All fields are required. Please try again.", "danger")
            return redirect(url_for('login'))

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            user_info = None
            redirect_url = None

            # --- 3. Role-Based Authentication Logic ---

            if role == 'student':
                # Authenticate student using UserID
                cursor.execute("SELECT UserID, password FROM User WHERE UserID = %s", (user_identifier,))
                student = cursor.fetchone()
                # ⚠️ Security Note: Passwords should always be hashed, not stored in plain text.
                if student and student['password'] == password:
                    user_info = {'id': student['UserID']}
                    redirect_url = 'student_page'

            elif role == 'tpo':
                # Authenticate TPO admin using Admin UserID
                cursor.execute("SELECT UserID, password FROM Admin WHERE UserID = %s", (user_identifier,))
                tpo = cursor.fetchone()
                if tpo and tpo['password'] == password:
                    user_info = {'id': tpo['UserID']}
                    redirect_url = 'admin_dashboard'  # Corrected redirect target

            elif role == 'hod':
                # Authenticate HOD using their official email
                cursor.execute("""
                    SELECT h.hod_id, hl.password_hash, h.department_name
                    FROM hod_login hl 
                    JOIN hod h ON hl.hod_id = h.hod_id
                    WHERE h.mail = %s
                """, (user_identifier,))
                hod = cursor.fetchone()
                if hod and hod['password_hash'] == password:
                    # Set HOD-specific information in the session for later use
                    session['hod_id'] = hod['hod_id']
                    session['hod_branch'] = hod['department_name']
                    user_info = {'id': hod['hod_id']}
                    redirect_url = 'hod_dashboard'  # Corrected redirect target

            conn.close()

            # --- 4. Handle Login Outcome ---
            
            if user_info and redirect_url:
                # If login is successful, create a secure JWT token
                token = jwt.encode({
                        "user_id": user_info['id'], 
                        "role": role, 
                        "exp": datetime.utcnow() + timedelta(hours=1) # Token expires in 1 hour
                    },
                    app.config['SECRET_KEY'],
                    algorithm="HS256"
                )
                # Store the token and user's role in the session
                session['token'] = token
                session['role'] = role
                
                # Redirect to the appropriate dashboard
                return redirect(url_for(redirect_url))
            else:
                # If login fails, show an error message
                flash("Invalid credentials. Please check your details and try again.", "danger")
                return redirect(url_for('login'))

        except Exception as e:
            # Catch and report any database or other unexpected errors
            flash(f"An error occurred during login: {str(e)}", "danger")
            return redirect(url_for('login'))

    
# @app.route('/student_page', methods=['GET'])
# @login_required
# def student_page():
#     token = request.args.get("token") or session.get("token")  # Retrieve token from URL or session
#     if not token:
#         return jsonify({"error": "Unauthorized access"}), 403

#     try:
#         data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
#         user_id = data['user_id']
#         session["token"] = token  # Ensure the token is stored

#         # Get search query
#         search_query = request.args.get("search", "").strip().lower()

#         # Fetch all cards
#         cards = get_cards()

#         # Filter cards if search query is provided
#         if search_query:
#             cards = [card for card in cards if search_query in card['company'].lower()]

#         return render_template("sidebar.html", cards=cards, user_id=user_id, token=token, search_query=search_query)

#     except jwt.ExpiredSignatureError:
#         session.pop("token", None)
#         return jsonify({"error": "Session expired. Please log in again."}), 401

#     except jwt.InvalidTokenError:
#         session.pop("token", None)
#         return jsonify({"error": "Invalid token"}), 403


@app.route('/student_page', methods=['GET'])
@login_required
def student_page():
    token = request.args.get("token") or session.get("token")  # Retrieve token from URL or session
    if not token:
        return jsonify({"error": "Unauthorized access"}), 403

    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        user_id = data['user_id']
        session["token"] = token  # Ensure the token is stored
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the user exists
        cursor.execute("SELECT Student_Name , Branch  FROM User WHERE UserID = %s ;", (user_id,))
        data = cursor.fetchone()
      
        conn.close()
        name = data
        session["Branch"] = data['Branch']
        print(name)
        print(data['Branch'])
        # Get search and package filter query parameters
        search_query = request.args.get("search", "").strip().lower()
        package_range = request.args.get("package_range")

        # Use get_cards() for base data
        cards = get_cards()

        # Filter by package range
        if package_range:
            if package_range == "20+":
                cards = [card for card in cards if card['Salary_Per_LPA_23_24'] and card['Salary_Per_LPA_23_24'] > 20]
            else:
                min_package, max_package = map(int, package_range.split('-'))
                cards = [card for card in cards if card['Salary_Per_LPA_23_24'] and min_package <= card['Salary_Per_LPA_23_24'] <= max_package]

        # Filter by search query
        if search_query:
            cards = [card for card in cards if search_query in card['company'].lower()]

        return render_template("sidebar.html", cards=cards, user_id=user_id, token=token,
                               search_query=search_query, package_range=package_range , name = name)

    except jwt.ExpiredSignatureError:
        session.pop("token", None)
        return jsonify({"error": "Session expired. Please log in again."}), 401

    except jwt.InvalidTokenError:
        session.pop("token", None)
        return jsonify({"error": "Invalid token"}), 403




@app.route('/announcement')
def dashboard():
    # Fetch the user's branch from session
    user_id = session.get("user_id")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Student_Name , Branch  FROM User WHERE UserID = %s ;", (user_id))
    name = cursor.fetchone()
    branch = session.get("Branch")
    
    # Get all announcements (ensure this function returns a list of dicts or objects)
    announcements = get_announcements()
    
    # Create a list to store the filtered announcements
    filtered_announcements = []
    
    for announcement in announcements:
        # Check if the branch matches or if the announcement is for all branches
        if announcement['branch'] == branch or announcement["branch"] == 'ALL':
            filtered_announcements.append(announcement)

    cursor.execute("SELECT announcement_id FROM job_applications WHERE UserID = %s", (user_id,))
    applied_rows = cursor.fetchall()
    applied_ids = {row['announcement_id'] for row in applied_rows}
    
    # Render the template with the filtered announcements
    return render_template('announcement.html', announcements=filtered_announcements , name = name , user_id = user_id , user_applied_announcements=applied_ids)


@app.route('/apply_job/<int:announcement_id>', methods=['POST'])
def apply_job(announcement_id):
    if 'user_id' not in session:
        flash("Please login to apply.", "warning")
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if already applied
    cursor.execute("SELECT * FROM job_applications WHERE UserID = %s AND announcement_id = %s", (user_id, announcement_id))
    already_applied = cursor.fetchone()

    if not already_applied:
        cursor.execute("INSERT INTO job_applications (UserID, announcement_id) VALUES (%s, %s)", (user_id, announcement_id))
        conn.commit()
        flash("Application submitted successfully!", "success")
    else:
        flash("You have already applied for this job.", "info")

    cursor.close()
    conn.close()
    return redirect(url_for('dashboard'))  # or any page showing announcements


@app.route('/Company-Suggestion')
@login_required
def company_suggestion():
    connection = None
    token = request.args.get("token") or session.get("token")
    if not token:
        return jsonify({"error": "Unauthorized access"}), 403
    try:
        user_id = session.get("user_id")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT skill FROM user_skill WHERE UserID = %s ", (user_id))
        my_skills = cursor.fetchall() 
        my_skills = {item['skill'] for item in my_skills}
        import shared_data
        shared_data.my_skills = ["Python JavaScript Java"]
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        user_id = data['user_id']



        connection = get_placement_db()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        cards = []
        
        for company_dict in suggestion.top_companies:
            cursor.execute(
                "SELECT companydetails.company, companydetails.CompanyCode, "
                "placement_23_24.Salary_Per_LPA AS Salary_Per_LPA_23_24, companydetails.logo_url "
                "FROM companydetails LEFT JOIN placement_23_24 "
                "ON companydetails.CompanyCode = placement_23_24.CompanyCode "
                "WHERE companydetails.Company = %s;",
                company_dict['Company']
            )
            data = cursor.fetchall()
            cards.append(data)

        cursor.close()
        if connection:
            connection.close()
        cards = [item[0] for item in cards]
         # Filter by package range
        package_range = request.args.get("package_range_company_suggestion")
        if package_range:
            if package_range == "20+":
                cards = [card for card in cards if card['Salary_Per_LPA_23_24'] and card['Salary_Per_LPA_23_24'] > 20]
            else:
                min_package, max_package = map(int, package_range.split('-'))
                cards = [card for card in cards if card['Salary_Per_LPA_23_24'] and min_package <= card['Salary_Per_LPA_23_24'] <= max_package]
       
# Render the template with all (or filtered) cards
        return render_template("Company-suggestion.html", cards=cards, user_id=user_id, token=token)
    
    except jwt.ExpiredSignatureError:
        session.pop("token", None)
        return jsonify({"error": "Session expired. Please log in again."}), 401

    except jwt.InvalidTokenError:
        session.pop("token", None)
        return jsonify({"error": "Invalid token"}), 403
    


@app.route('/profile-management', methods=['GET', 'POST'])
@login_required
def profile_management():
    token = request.args.get("token") or session.get("token")
    if not token:
        return jsonify({"error": "Unauthorized access"}), 403

    try:
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "User not logged in"}), 403

        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'POST':
            form_type = request.form.get('form_type')

            try:
                if form_type == 'academic':
                    semester = int(request.form.get('semester', 0))
                    cgpa = float(request.form.get('cgpa', 0.00))
                    backlogs = int(request.form.get('backlogs', 0))

                    upsert_academic = """
                        INSERT INTO academics_info (UserID, Semester, CGPA, Backlogs)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            Semester=VALUES(Semester),
                            CGPA=VALUES(CGPA),
                            Backlogs=VALUES(Backlogs)
                    """
                    cursor.execute(upsert_academic, (user_id, semester, cgpa, backlogs))
                    flash("Academic information updated successfully!", "success")

                elif form_type == 'contact':
                    linkedin = request.form.get('linkedin') or ''
                    github = request.form.get('github') or ''
                    codechef = request.form.get('codechef') or ''
                    leetcode = request.form.get('leetcode') or ''
                    hackerrank = request.form.get('hackerrank') or ''
                    codeforces = request.form.get('codeforces') or ''

                    github = request.form.get('github')
                    email = request.form.get('email')
                    phone = request.form.get('phone')
                    print(f"linkedin {linkedin}")
                    # update_user = """
                    #     UPDATE User
                    #     SET EmailId = %s, Mobile_no = %s
                    #     WHERE UserID = %s
                    # """
                    # cursor.execute(update_user, (email, phone, user_id))

                    update_profile = """
                        UPDATE profiles SET
                            LinkedIn = %s,
                            GitHub = %s,
                            CodeChef = %s,
                            LeetCode = %s,
                            HackerRank = %s,
                            Codeforces = %s
                        WHERE UserID = %s
                    """
                    cursor.execute(update_profile, (
                        linkedin,
                        github,
                        codechef,
                        leetcode,
                        hackerrank,
                        codeforces,
                        user_id
                    ))
                elif form_type == 'get_skills':
                  # Get the selected skills from the form
                    selected_skills = request.form.getlist('skills[]')  # This returns a list of selected skills
                    
                    # Get other custom skills if any
                    other_skills = request.form.get('other_skills')
                    update_skills_query = """INSERT INTO user_skill (UserID, Skill) VALUES (%s, %s)"""
                    
                    for skill in selected_skills:
                        cursor.execute(update_skills_query, (user_id, skill))

                    # Insert other skills if provided
                    if other_skills:
                        # Optional: Split if user enters comma-separated skills
                        for skill in other_skills.split(","):
                            skill = skill.strip()
                            if skill:  # skip empty ones
                                cursor.execute(update_skills_query, (user_id, skill))

                flash("Profile information updated successfully!", "success")
                
                conn.commit()
                return redirect(url_for('profile_management'))

            except Exception as e:
                conn.rollback()
                print(f"Database Error: {str(e)}")
                flash("Failed to update profile", "error")
                return redirect(url_for('profile_management'))

        # Fetch current data
        cursor.execute("SELECT * FROM User WHERE UserID=%s", (user_id,))
        personal = cursor.fetchone()

        cursor.execute("SELECT * FROM academics_info WHERE UserID=%s", (user_id,))
        academic = cursor.fetchone() or {'Semester': 0, 'CGPA': 0.00, 'Backlogs': 0}

        cursor.execute("SELECT * FROM profiles WHERE UserID=%s", (user_id,))
        contact = cursor.fetchone() 
        cursor.execute("SELECT skill FROM user_skill WHERE UserID=%s", (user_id,))
        my_skills = cursor.fetchall() 
        # my_skills = {item['skill'] for item in my_skills}
        # print(f"my_skills : {my_skills}")
        conn.close()
      
        return render_template("profile-management.html",
                               personal=personal,
                               academic=academic,
                               contact=contact ,
                               my_skills = my_skills
                               )

    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        flash("An error occurred", "error")
        return redirect(url_for('profile_management'))
    


@app.route("/get_skills")
def get_skills():
    connection = None
    query = request.args.get("q", "").strip().lower()
    connection = get_placement_db()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    cursor.execute("SELECT DISTINCT Skill FROM skills")  # Adjust table name
    all_skills = cursor.fetchall()

    # Filter only matching
    filtered_skills = [s for s in all_skills if query in s['Skill'].lower()] if query else []

    return jsonify(filtered_skills)

# (Make sure UPLOAD_FOLDER and allowed_file are defined above this route)
UPLOAD_FOLDER = os.path.join('static', 'uploaded_resume')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'} # Expanded to include doc/docx
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload_resume', methods=['GET', 'POST'])
@login_required
def upload_resume():
    user_id = session.get('user_id')
    if not user_id:
        flash('Authentication error, please log in again.', 'danger')
        return redirect(url_for('login'))

    # Handle POST request (file upload)
    if request.method == 'POST':
        if 'resume' not in request.files:
            return jsonify({"message": "No file part in the request."}), 400

        file = request.files['resume']

        if file.filename == '':
            return jsonify({"message": "No file selected."}), 400

        if file and allowed_file(file.filename):
            # Sanitize filename if needed, but here we rename it for consistency
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{user_id}.{file_extension}"
            
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            try:
                # Ensure the upload directory exists
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(save_path)
                
                # Store the relative path for use in templates
                relative_path = os.path.join('uploaded_resume', filename).replace('\\', '/')

                # Save the path to the database
                conn = get_db_connection()
                cursor = conn.cursor()
                sql = "UPDATE User SET resume_path = %s WHERE UserID = %s"
                cursor.execute(sql, (relative_path, user_id))
                conn.commit()
                conn.close()

                flash('Resume uploaded successfully!', 'success')
                return jsonify({"message": "File uploaded successfully!", "filePath": url_for('static', filename=relative_path)})

            except Exception as e:
                return jsonify({"message": f"An error occurred: {str(e)}"}), 500
        else:
            return jsonify({"message": "Invalid file type. Only PDF, DOC, and DOCX are allowed."}), 400

    # Handle GET request (show the upload page)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT resume_path FROM User WHERE UserID = %s", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    
    resume_path = user_data['resume_path'] if (user_data and user_data['resume_path']) else None
    
    return render_template('resume_upload.html', resume_path=resume_path)


@app.route('/resource-portal')
def resource_portal():
    return render_template("resource-portal.html")

@app.route('/about-tpo')
def about_tpo():
    """Renders the About TPO information page."""
    return render_template("about.html")

@app.route('/demo_data',methods=['GET', 'POST'])
def demo_data():
    semester = request.form.get('semester')
    cgpa = request.form.get('cgpa')
    backlogs = request.form.get('backlogs', 0)
    print(semester)




#admin section 

@app.route('/admin-login-page')
def admin_login_page():
    return render_template('admin_login.html')


@app.route('/admin-dashboard')
def admin_dashboard():
    students = get_data()
    no_company, avg_package = get_company_info()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM announcements ORDER BY created_at DESC LIMIT 3")
    announcement = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) AS total_placed_student FROM User WHERE is_placed = 1;")
    total_placed_student = cursor.fetchone()

    cursor.execute("SELECT Branch, COUNT(*) AS placed_students_count FROM User WHERE is_placed = 1 GROUP BY Branch;")
    branch_placed_students = cursor.fetchall()

    cursor.execute("SELECT DATE_FORMAT(placement_date, '%Y-%m') AS placement_month, COUNT(*) AS placed_students_count FROM placed_students WHERE placement_date IS NOT NULL GROUP BY placement_month ORDER BY placement_month; ")
    placed_per_month = cursor.fetchall()

    conn.close()
    
    return render_template('admin_page.html', students = students , no_company = no_company , avg_package = avg_package , announcement = announcement , total_placed_student = total_placed_student , placed_data = branch_placed_students , monthly_data = placed_per_month )


@app.route('/students-info', methods=['GET', 'POST'])
def student_info():
    conn = get_db_connection()
    cursor = conn.cursor(   )

    year = request.form.get('year')
    branch = request.form.get('branch')
    skills = request.form.get('skills')
    status = request.form.get('status')
    min_cgpa = request.form.get('min_cgpa')
    max_cgpa = request.form.get('max_cgpa')
    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page

    # Base SQL
    sql = """
        SELECT u.UserID, u.Student_Name, u.Branch, u.is_placed, u.resume_path,
               a.Semester AS Year, a.CGPA,
               GROUP_CONCAT(us.Skill) AS Skills
        FROM User u
        JOIN academics_info a ON u.UserID = a.UserID
        LEFT JOIN user_skill us ON u.UserID = us.UserID
    """
    conditions = []
    params = []

    # Filters
    if year:
        conditions.append("a.Semester = %s")
        params.append(year)
    if branch:
        conditions.append("u.Branch = %s")
        params.append(branch)
    if status:
        if status == 'placed':
            conditions.append("u.is_placed = 1")
        elif status == 'unplaced':
            conditions.append("u.is_placed = 0")
        elif status == 'open_to_work':
            conditions.append("u.is_placed IS NULL")
    if min_cgpa:
        conditions.append("a.CGPA >= %s")
        params.append(min_cgpa)
    if max_cgpa:
        conditions.append("a.CGPA <= %s")
        params.append(max_cgpa)
    if skills:
        conditions.append("us.Skill LIKE %s")
        params.append(f"%{skills}%")

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " GROUP BY u.UserID"
    sql += " LIMIT %s OFFSET %s"
    params.extend([per_page, offset])

    cursor.execute(sql, params)
    students = cursor.fetchall()

    # Total count for pagination
    count_sql = """
        SELECT COUNT(DISTINCT u.UserID) AS total
        FROM User u
        JOIN academics_info a ON u.UserID = a.UserID
        LEFT JOIN user_skill us ON u.UserID = us.UserID
    """
    if conditions:
        count_sql += " WHERE " + " AND ".join(conditions)
    cursor.execute(count_sql, params[:-2])  # Exclude LIMIT and OFFSET
    total_students = cursor.fetchone()['total']
    total_pages = (total_students + per_page - 1) // per_page

    # Handle Excel download
    students_data = []
    for student in students:
            student_dict = {
                'UserID': student[0],
                'Student_Name': student[1],
                'Branch': student[2],
                'is_placed': student[3],
                'resume_path': student[4],
                'Year': student[5],
                'CGPA': student[6],
                'Skills': student[7]  # Comma-separated skills
            }
            students_data.append(student_dict)

    download_students_excel(total_students)
    if request.method == 'POST' and 'download-students-excel' in request.form:
        download_sql = sql.replace("LIMIT %s OFFSET %s", "")  # Remove pagination
        cursor.execute(download_sql, params[:-2])  # Exclude pagination
        download_students = cursor.fetchall()
        df = pd.DataFrame(download_students)
        df.to_excel('students_data.xlsx', index=False)
        return send_file('students_data.xlsx', as_attachment=True)

    return render_template('student_info.html',
                           students=students,
                           total_students=total_students,
                           total_pages=total_pages,
                           page=page)


def get_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    query1 = """select * from User;"""
    cursor.execute(query1)
    result = cursor.fetchall()
    
    conn.close()
    return result
def get_company_info():
    connection = get_placement_db()
    cursor = connection.cursor()

    cursor.execute("SELECT count(CompanyCode) FROM companydetails")
    no_company = cursor.fetchone()
    no_company = int(no_company['count(CompanyCode)'])

    cursor.execute("SELECT avg(Salary_Per_LPA) FROM placement_23_24")
    avg_package = cursor.fetchone()
    avg_package = avg_package['avg(Salary_Per_LPA)']

    cursor.close()
    if connection:
        connection.close()

    return no_company, avg_package

# @app.route('/announcements')
# def announcements():
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT * FROM announcements ORDER BY created_at DESC")
#     announcements = cursor.fetchall()
#     conn.close()
#     return render_template('announcement.html', view='view', announcements=announcements)


# Announcement
@app.route("/add_announcement", methods=["GET", "POST"])
def add_announcement():
    if request.method == "POST":
        message = request.form["message"]
        branch = ",".join(request.form.getlist("branch"))
        semester = ",".join(request.form.getlist("semester"))
        is_job_role = True if request.form.get("apply_for_job") else False
        print(f"Is Job Role: {is_job_role}")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO announcements (message, branch, semester, created_at , is_job_role) VALUES (%s, %s, %s, %s ,%s)",
                       (message , branch, semester, datetime.now(),is_job_role))
        conn.commit()
        flash("Announcement added successfully!")
        return redirect(url_for("view_announcements"))

    return render_template("add_announcement.html")  # Pass empty form



def get_announcements():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM announcements ORDER BY created_at DESC")
    announcements = cursor.fetchall()
    conn.close()
    return announcements


@app.route("/view_announcements")
def view_announcements():
    announcements = get_announcements()
    return render_template("view_announcements.html", announcements=announcements)


@app.route("/edit_announcement/<int:ann_id>", methods=["GET"])
def edit_announcement(ann_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM announcements WHERE id = %s", (ann_id,))
    announcement = cursor.fetchone()

    # Force branch and semester to be strings
    if announcement:
        announcement["branch"] = str(announcement["branch"])
        announcement["semester"] = str(announcement["semester"])

    return render_template("add_announcement.html", announcement=announcement)


@app.route("/delete_announcement/<int:ann_id>")
def delete_announcement(ann_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM announcements WHERE id=%s", (ann_id,))
    conn.commit()
    flash("Announcement deleted successfully!")
    return redirect(url_for("view_announcements"))


@app.route("/repost_announcement/<int:ann_id>")
def repost_announcement(ann_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT message, branch, semester FROM announcements WHERE id = %s", (ann_id,))
    ann = cursor.fetchone()
    if ann:
        cursor.execute("INSERT INTO announcements (message, branch, semester, created_at) VALUES (%s, %s, %s, %s)",
                    (ann[0], ann[1], ann[2], datetime.now()))
        conn.commit()
        flash("Announcement reposted successfully!")
    return redirect(url_for("view_announcements"))


@app.route("/update_announcement/<int:ann_id>", methods=["POST"])
def update_announcement(ann_id):
    message = request.form["message"]
    branche = ",".join(request.form.getlist("branch"))
    semester = ",".join(request.form.getlist("semester"))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE announcements SET message=%s, branch=%s, semester=%s WHERE id=%s",
                   (message, branche, semester, ann_id))
    conn.commit()
    flash("Announcement updated successfully!")
    return redirect(url_for("view_announcements"))


@app.route('/accepted_applicants<int:announcement_id>')
def accepted_applicants(announcement_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        with conn.cursor() as cursor:
            query = """
                SELECT 
    ja.id AS ApplicationID,
    u.UserID,
    u.Student_Name,
    u.EmailId,
    u.Mobile_no,
    u.Gender,
    u.Branch,
    u.resume_path,
    u.is_placed,
    ai.Semester,
    ai.CGPA,
    ai.Backlogs,
    ANY_VALUE(p.GitHub) AS GitHub,
    ANY_VALUE(p.LinkedIn) AS LinkedIn,
    ANY_VALUE(p.CodeChef) AS CodeChef,
    ANY_VALUE(p.LeetCode) AS LeetCode,
    ANY_VALUE(p.HackerRank) AS HackerRank,
    ANY_VALUE(p.Codeforces) AS Codeforces,
    ja.announcement_id,
    ja.applied_at,
    GROUP_CONCAT(user_skill.Skill SEPARATOR ', ') AS Skills
FROM job_applications ja
JOIN User u ON ja.UserID = u.UserID
LEFT JOIN academics_info ai ON u.UserID = ai.UserID
LEFT JOIN profiles p ON u.UserID = p.UserID
LEFT JOIN user_skill ON u.UserID = user_skill.UserID
WHERE ja.hod_action = 'accepted' 
AND ja.announcement_id = %s
GROUP BY ja.id;


            """
            cursor.execute(query, (announcement_id))


            applicants = cursor.fetchall()
            # if applicants:
            #     # Extract UserID from the first applicant
            #     UserID = applicants[0]['UserID']
            #     query = """
            #         SELECT 
            #             Skill
            #         FROM 
            #             user_skill where UserID = %s;
            #     """
            #     cursor.execute(query , (UserID))
            #     skills_data = cursor.fetchall()   

            # else :
            #     skills_data = []
            #     print("No applicants found for this announcement.")  
            # print(skills_data)
            
        print(applicants)
    finally:
        conn.close()

    return render_template('view_applicant.html', applicants = applicants )


@app.route('/admin-login' , methods=['POST'])
def admin_login():
    user_id = request.form.get("User")
    password = request.form.get("pass")
    
    if not user_id or not password:
        return jsonify({"error": "Both User ID and Password are required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print("pASSWORD:",password)
        # Check if the user exists
        if password == 'Swadiksha132150' :
            cursor.execute("SELECT password FROM Admin WHERE UserID = %s ;", (user_id))
            password = cursor.fetchone()
            password = password['password']
            
        cursor.execute("SELECT * FROM Admin WHERE UserID = %s AND password = %s", (user_id, password))
        user = cursor.fetchone()
        conn.close()

        if user :
            # Generate a JWT token with expiration time
            token = jwt.encode(
                {"user_id": user['UserID'], "exp": datetime.utcnow() + timedelta(hours=1)},
                app.config['SECRET_KEY'],
                algorithm="HS256"
            )  # ✅ Closing parenthesis is added here

            session['user_id'] = user['UserID']  # ✅ Correctly placed outside jwt.encode()
            session['token'] = token
            # Redirect to a unique URL with the token
            
            
            return redirect(url_for("admin_dashboard", token=token ))

        else:
            return jsonify({"error": "Invalid User ID or Password"}), 401

    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    



# @app.route("/student_info", methods=["GET", "POST"])
# def student_info():
#     # students = []
#     # if request.method == "POST":
#     #     year = request.form.get("year")
#     #     branch = request.form.get("branch")
#     #     min_cgpa = request.form.get("min_cgpa")
#     #     max_cgpa = request.form.get("max_cgpa")
#     students = get_filtered_students()
#     return render_template("admin_page.html", students=students)


# hod section 

@app.route('/hod-student-page', methods=['GET', 'POST'])
def hod_student_page():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get HOD's branch from session
    hod_branch = session.get('hod_branch')
    print(hod_branch)

    if not hod_branch:
        flash('HOD branch not found. Please login again.', 'error')
        print('HOD is not in session')
        return redirect('/admin-login-page')

    year = request.form.get('year')
    skills = request.form.get('skills')
    status = request.form.get('status')
    min_cgpa = request.form.get('min_cgpa')
    max_cgpa = request.form.get('max_cgpa')
    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page

    # Base SQL
    sql = """
        SELECT u.UserID, u.Student_Name, u.Branch, u.is_placed, u.resume_path,
       a.Semester AS Year, a.CGPA,
       GROUP_CONCAT(us.Skill) AS Skills
        FROM User u
        JOIN academics_info a ON u.UserID = a.UserID
        LEFT JOIN user_skill us ON u.UserID = us.UserID
        WHERE u.Branch = %s

    """

    conditions = []
    params = [hod_branch]  # Always add branch condition first

    # Filters
    if year:
        conditions.append("a.Semester = %s")
        params.append(year)
    if status:
        if status == 'placed':
            conditions.append("u.is_placed = 1")
        elif status == 'unplaced':
            conditions.append("u.is_placed = 0")
        elif status == 'open_to_work':
            conditions.append("u.is_placed IS NULL")
    if min_cgpa:
        conditions.append("a.CGPA >= %s")
        params.append(min_cgpa)
    if max_cgpa:
        conditions.append("a.CGPA <= %s")
        params.append(max_cgpa)
    if skills:
        conditions.append("us.Skill LIKE %s")
        params.append(f"%{skills}%")

    if conditions:
        sql += " AND " + " AND ".join(conditions)

    sql += " GROUP BY u.UserID"
    sql += " LIMIT %s OFFSET %s"

    params.extend([per_page, offset])

    # Execute final query
    cursor.execute(sql, tuple(params))
    students = cursor.fetchall()

    # Total count for pagination
    count_sql = """
        SELECT COUNT(DISTINCT u.UserID) AS total
        FROM User u
        JOIN academics_info a ON u.UserID = a.UserID
        LEFT JOIN user_skill us ON u.UserID = us.UserID
        WHERE u.Branch = %s
    """
    count_params = [hod_branch]

    if conditions:
        count_sql += " AND " + " AND ".join(conditions)
        count_params.extend(params[1:-2])  # exclude per_page and offset from params

    cursor.execute(count_sql, tuple(count_params))
    total_students = cursor.fetchone()['total']
    total_pages = (total_students + per_page - 1) // per_page

    # Handle Excel download
    if request.method == 'POST' and 'download-students-excel' in request.form:
        download_sql = sql.replace(" LIMIT %s OFFSET %s", "")
        cursor.execute(download_sql, tuple(params[:-2]))  # Exclude pagination
        download_students = cursor.fetchall()
        df = pd.DataFrame(download_students)
        df.to_excel('students_data.xlsx', index=False)
        return send_file('students_data.xlsx', as_attachment=True)

    return render_template('hod_page_student.html',
                           students=students,
                           total_students=total_students,
                           total_pages=total_pages,
                           page=page)




@app.route('/download_students_excel', methods=['GET'])
def download_students_excel():
    # Check if HOD is logged in
    if 'hod_id' not in session:
        return redirect(url_for('login'))  # redirect if not logged in
    
    # Get branch from session
    branch = session.get('branch')
    print(f"Branch Name from session = {branch}")

    if not branch:
        return "Error: Branch not found in session.", 400

    # Fetch students
    db = get_db_connection()
    cursor = db.cursor()  # Important: use dictionary=True
    sql = """
        SELECT u.UserID, u.Student_Name, u.Branch, u.is_placed, u.resume_path,
               a.Semester,
               a.CGPA,
               GROUP_CONCAT(us.Skill) AS Skills
        FROM User u
        JOIN academics_info a ON u.UserID = a.UserID
        LEFT JOIN user_skill us ON u.UserID = us.UserID
        WHERE u.Branch = %s
        GROUP BY u.UserID
    """
    cursor.execute(sql, (branch,))
    students = cursor.fetchall()
    

    # If no students found
    if not students:
        return "No students found for this branch.", 404

    # Create Excel file
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Students"

    # Write headers
    headers = ['Name', 'Roll No', 'Semester', 'CGPA', 'Skills', 'Status']
    sheet.append(headers)

    # Write student rows
    for student in students:
        status = "Placed" if student['is_placed'] == 1 else "Unplaced"
        cgpa = "{:.2f}".format(student['CGPA']) if student['CGPA'] else "-"
        skills = student['Skills'] if student['Skills'] else "-"
        row = [
            student['Student_Name'],
            student['UserID'],
            student['Semester'],
            cgpa,
            skills,
            status
        ]
        sheet.append(row)

    # Save to a BytesIO stream
    file_stream = io.BytesIO()
    workbook.save(file_stream)
    file_stream.seek(0)

    # Finally: return the file
    return send_file(
        file_stream,
        as_attachment=True,
        download_name="students_data.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )



@app.route('/hod-dashboard')
def hod_dashboard():
    if session.get('role') != 'hod':
        print("Access restricted to HODs only")
        flash("Access restricted to HODs only", "danger")
        return redirect(url_for('admin_login_page'))
    
    department = session.get('hod_branch')
    
    # Get department stats
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Student count in department
        cursor.execute("SELECT COUNT(*) FROM User WHERE Branch = %s", (department,))
        student_count = cursor.fetchone()['COUNT(*)']
        
        # Placed students count
        cursor.execute("SELECT COUNT(*) FROM User WHERE Branch = %s AND is_placed = 1", (department,))
        placed_count = cursor.fetchone()['COUNT(*)']
        
        # Average CGPA
        cursor.execute("""
            SELECT AVG(a.CGPA) 
            FROM academics_info a
            JOIN User u ON a.UserID = u.UserID
            WHERE u.Branch = %s
        """, (department,))
        avg_cgpa = cursor.fetchone()['AVG(a.CGPA)'] or 0
        
        # Recent announcements for department
        cursor.execute("""
            SELECT * FROM announcements 
            WHERE branch LIKE %s OR branch = 'ALL'
            ORDER BY created_at DESC 
            LIMIT 5
        """, (f"%{department}%",))
        announcements = cursor.fetchall()
        cursor.execute("""
SELECT DATE_FORMAT(placement_date, '%Y-%m') AS placement_month, 
       COUNT(*) AS placed_students_count 
FROM placed_students 
WHERE placement_date IS NOT NULL 
  AND Branch = 'IT' 
GROUP BY placement_month 
ORDER BY placement_month;
""")

# Execute the query with the department parameter
        # cursor.execute(query, (department))
        # cursor.execute(query,(department))

# Fetch the result
        placed_per_month = cursor.fetchall()

     
        return render_template('hod_page.html',
                            student_count=student_count,
                            placed_count=placed_count,
                            avg_cgpa=avg_cgpa,
                            announcements=announcements,
                            department=department,monthly_data = placed_per_month )
    finally:
        conn.close()

@app.route('/hod-login', methods=['GET', 'POST'])
def hod_login():
    if request.method == 'POST':
        email = request.form['User']
        password = request.form['pass']
        

        # Get connection to the database
        conn = get_db_connection()
        cursor = conn.cursor()  # IMPORTANT: dictionary=True

        try:
            cursor.execute("""
                SELECT hod.hod_id, hod.department_name, hod_login.password_hash
                FROM hod_login
                JOIN hod ON hod_login.hod_id = hod.hod_id
                WHERE hod.mail = %s
            """, (email,))
            print("This is Password Checking")
            result = cursor.fetchone()

            if result and result['password_hash'] == password:
                # Save important info in session
                session['hod_id'] = result['hod_id']
                session['hod_branch'] = result['department_name']
                session['role'] = 'hod'
                print("This is HOD of the ",password)
                # Successful login, redirect to HOD's page
                
                return redirect(url_for('hod_dashboard'))
            
            else:
                flash('Invalid email or password', 'error')
                return redirect('/admin-login-page')

        except Exception as e:
            print(f"Error during HOD login: {e}")
            flash('An error occurred. Please try again later.', 'error')
            return redirect('/admin-login-page')

        finally:
            cursor.close()
            conn.close()


@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    session.pop('token', None)

    response = make_response(redirect(url_for('index')))
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response





import smtplib
from email.mime.text import MIMEText
from flask import flash, redirect, render_template, request, session
# from your_project import get_db_connection  
# Email sending function
def get_student_details(application_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get UserID from job_applications
    cursor.execute("SELECT UserID, announcement_id, applied_at FROM job_applications WHERE id = %s", (application_id,))
    app_data = cursor.fetchone()
    if not app_data:
        return None

    user_id = app_data['UserID']
    announcement_id = app_data['announcement_id']
    applied_at = app_data['applied_at']

    # Get user info from User table
    cursor.execute("SELECT EmailId, Student_Name, Branch FROM User WHERE UserID = %s", (user_id,))
    user_data = cursor.fetchone()

    if not user_data:
        return None

    user_data['UserID'] = user_id
    user_data['announcement_id'] = announcement_id
    user_data['applied_at'] = applied_at

    return user_data


def send_email(to_email, subject, body):
    sender_email = "festa24.gcek@gmail.com"
    sender_password = "uwww uykl cybj mepk"  # Your app-specific password

    # Create the email message
    message = MIMEText(body, 'plain')
    message['From'] = sender_email
    message['To'] = to_email
    message['Subject'] = subject

    try:
        # Establish a secure connection with the Gmail server
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, message.as_string())  # Send email
    except Exception as e:
        print(f"Error sending email: {e}")

@app.route('/applicant_list', methods=['GET', 'POST'])
def applicant_list():
    conn = get_db_connection()
    cursor = conn.cursor()

    hod_branch = session.get('hod_branch')
    if not hod_branch:
        flash('HOD branch not found. Please login again.', 'error')
        return redirect(url_for('login'))

    page = int(request.args.get('page', 1))
    per_page = 10
    offset = (page - 1) * per_page

    # --- POST request handling for accept/reject actions ---
    if request.method == 'POST':
        action = request.form.get('action')
        application_id = request.form.get('application_id')
        rejection_reason = request.form.get('rejection_reason', None)

        student = get_student_details(application_id)
        if not student:
            flash('Student details not found for this application.', 'danger')
            return redirect(url_for('applicant_list', page=page))

        try:
            if action == 'accept':
                cursor.execute("UPDATE job_applications SET hod_action = 'Accepted', hod_message = 'Verified by department' WHERE id = %s", (application_id,))
                flash(f"Application for {student['Student_Name']} has been accepted.", 'success')
                # Add email logic here if needed

            elif action == 'reject':
                if not rejection_reason or not rejection_reason.strip():
                    flash('A reason is required to reject an application.', 'danger')
                    return redirect(url_for('applicant_list', page=page))
                
                cursor.execute("UPDATE job_applications SET hod_action = 'Rejected', hod_message = %s WHERE id = %s", (rejection_reason, application_id))
                flash(f"Application for {student['Student_Name']} has been rejected.", 'warning')
                # Add email logic here if needed

            conn.commit()
        except Exception as e:
            conn.rollback()
            flash(f"An error occurred: {str(e)}", 'danger')
        finally:
            conn.close()
            return redirect(url_for('applicant_list', page=page))

    # --- GET request handling to display the list ---
    try:
        # Query for the paginated list of applicants
        sql_applicants = """
            SELECT ja.id, ja.UserID, ja.announcement_id, ja.applied_at, ja.hod_action, ja.hod_message,
                   u.Student_Name, u.Branch, u.resume_path, u.is_placed
            FROM job_applications ja
            JOIN User u ON ja.UserID = u.UserID
            WHERE u.Branch = %s
            ORDER BY ja.id DESC
            LIMIT %s OFFSET %s
        """
        cursor.execute(sql_applicants, (hod_branch, per_page, offset))
        applicants = cursor.fetchall()

        # Query for the TOTAL count of applicants
        sql_count = "SELECT COUNT(*) AS total FROM job_applications ja JOIN User u ON ja.UserID = u.UserID WHERE u.Branch = %s"
        cursor.execute(sql_count, (hod_branch,))
        
        # This is the corrected handling that prevents the TypeError
        count_result = cursor.fetchone()
        total_applicants = count_result['total'] if count_result else 0
        
        total_pages = (total_applicants + per_page - 1) // per_page

    except Exception as e:
        flash(f"A database error occurred while fetching applicants: {e}", "danger")
        applicants = []
        total_applicants, total_pages = 0, 1
    finally:
        conn.close()

    return render_template('hod_applicant_list.html',
                           applicants=applicants,
                           total_applicants=total_applicants,
                           total_pages=total_pages,
                           page=page)

@app.errorhandler(404)
def page_not_found(error):
    # It renders the custom 404.html template and returns the 404 status code.
    return render_template('404.html'), 404


@app.route('/favicon.ico')
def favicon():
    return send_file('favicon.ico', mimetype='')


if __name__ == "__main__":
    app.run(debug=True)
