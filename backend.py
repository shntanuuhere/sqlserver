from flask import Flask, request, jsonify, render_template
import pyodbc

# --- Configuration ---
# Make sure this matches your local SQL Server instance name.
CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=Shantanu-PC;"  # <--- IMPORTANT: VERIFY THIS IS YOUR SERVER NAME
    "DATABASE=CollegeDB;"
    "Trusted_Connection=yes;"
)

app = Flask(__name__)

# --- Helper Function to Connect to DB ---
def get_db_connection():
    try:
        conn = pyodbc.connect(CONNECTION_STRING)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

# --- API Routes ---

# Serves the main HTML page
@app.route('/')
def index():
    return render_template('index.html')

# GET all students with all new columns
@app.route('/api/students', methods=['GET'])
def get_students():
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor()
    # Fetch all the new columns
    cursor.execute("""
        SELECT StudentID, FirstName, LastName, Major, School, Grade, Board, PassingYear 
        FROM Students 
        ORDER BY StudentID
    """)
    # A more robust way to convert rows to dictionaries
    columns = [column[0] for column in cursor.description]
    students = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return jsonify(students)

# POST a new student with all new columns
@app.route('/api/students', methods=['POST'])
def add_student():
    new_student = request.get_json()
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    cursor = conn.cursor()
    # Updated INSERT statement
    sql = """
        INSERT INTO Students (StudentID, FirstName, LastName, Major, School, Grade, Board, PassingYear) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    values = (
        new_student.get('StudentID'), new_student.get('FirstName'), new_student.get('LastName'),
        new_student.get('Major'), new_student.get('School'), new_student.get('Grade'),
        new_student.get('Board'), new_student.get('PassingYear')
    )
    try:
        cursor.execute(sql, values)
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Student added successfully!"}), 201
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "message": str(e)}), 400

# UPDATE an existing student, identified by their original ID
@app.route('/api/students/<int:original_student_id>', methods=['PUT'])
def update_student(original_student_id):
    updated_data = request.get_json()
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    # This SQL now updates every field, including the StudentID itself
    sql = """
        UPDATE Students 
        SET StudentID = ?, FirstName = ?, LastName = ?, Major = ?, 
            School = ?, Grade = ?, Board = ?, PassingYear = ?
        WHERE StudentID = ?
    """
    values = (
        updated_data.get('StudentID'), updated_data.get('FirstName'), updated_data.get('LastName'),
        updated_data.get('Major'), updated_data.get('School'), updated_data.get('Grade'),
        updated_data.get('Board'), updated_data.get('PassingYear'),
        original_student_id  # Use the original ID in the WHERE clause to find the record
    )
    
    try:
        cursor.execute(sql, values)
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"success": False, "message": "Student not found"}), 404
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Student updated successfully!"})
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "message": str(e)}), 400

# DELETE a student
@app.route('/api/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({"error": "Database connection failed"}), 500
        
    cursor = conn.cursor()
    sql = "DELETE FROM Students WHERE StudentID = ?"
    
    try:
        cursor.execute(sql, student_id)
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({"success": False, "message": "Student not found"}), 404
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Student deleted successfully!"})
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "message": str(e)}), 400

# --- Run the App ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)

