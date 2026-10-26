
from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from sklearn.tree import DecisionTreeClassifier
from functools import wraps

app = Flask(__name__)
app.secret_key = "change-this-to-a-random-secret-key"

# Demo admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# Admin Login Protection
def admin_required(view_function):
    @wraps(view_function)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return view_function(*args, **kwargs)
    return wrapper


# Machine Learning Demo Model
X = [[5], [12], [18], [25], [35], [45], [55], [65], [75]]

y = [
    "General Physician",
    "General Physician",
    "Dermatologist",
    "Dermatologist",
    "General Physician",
    "Cardiologist",
    "Cardiologist",
    "Cardiologist",
    "General Physician"
]

model = DecisionTreeClassifier(random_state=42)
model.fit(X, y)


# Database Connection
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="patient_db"
    )


# Home Page
@app.route("/")
def home():
    return render_template("index.html")


# Appointment Form
@app.route("/appointment")
def appointment():
    return render_template("appointment.html")


# ML Prediction
@app.route("/predict", methods=["POST"])
def predict():
    age = int(request.form["age"])
    prediction = model.predict([[age]])[0]

    return render_template(
        "prediction.html",
        age=age,
        prediction=prediction
    )


# Book Appointment
@app.route("/book", methods=["POST"])
def book():
    name = request.form["name"]
    age = int(request.form["age"])
    doctor = request.form["doctor"]
    date = request.form["date"]

    db = get_connection()

    try:
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO patients
            (name, age, doctor, appointment_date)
            VALUES (%s, %s, %s, %s)
            """,
            (name, age, doctor, date)
        )
        db.commit()
    finally:
        cursor.close()
        db.close()

    return """
    <h2>Appointment Booked Successfully!</h2>
    <a href="/">Go Home</a>
    """


# View All Appointments
@app.route("/appointments")
def appointments():
    db = get_connection()

    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT id, name, age, doctor, appointment_date
            FROM patients
            ORDER BY id DESC
        """)
        records = cursor.fetchall()
    finally:
        cursor.close()
        db.close()

    return render_template("appointments.html", records=records)


# Admin Login
@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))

        return render_template(
            "admin_login.html",
            error="Invalid username or password!"
        )

    return render_template("admin_login.html")


# Admin Dashboard with Search and Status Filter
@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    search = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip()

    allowed_statuses = [
        "Pending", "Confirmed", "Completed", "Cancelled"
    ]

    db = get_connection()

    try:
        cursor = db.cursor(dictionary=True)

        query = """
            SELECT id, name, age, doctor, appointment_date, status
            FROM patients
            WHERE name LIKE %s
        """
        params = [f"%{search}%"]

        if status_filter in allowed_statuses:
            query += " AND status = %s"
            params.append(status_filter)

        query += " ORDER BY id DESC"

        cursor.execute(query, tuple(params))
        records = cursor.fetchall()

        # Dashboard Statistics
        cursor.execute("""
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(status = 'Pending'), 0) AS pending,
                COALESCE(SUM(status = 'Confirmed'), 0) AS confirmed,
                COALESCE(SUM(status = 'Completed'), 0) AS completed
            FROM patients
        """)
        stats = cursor.fetchone()

    finally:
        cursor.close()
        db.close()

    return render_template(
        "admin_dashboard.html",
        records=records,
        stats=stats,
        search=search,
        status_filter=status_filter
    )


# Admin Logout
@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


# Update Appointment Status
@app.route("/admin/update_status", methods=["POST"])
@admin_required
def update_status():
    appointment_id = request.form.get("appointment_id", "")
    new_status = request.form.get("status", "")

    allowed_statuses = [
        "Pending", "Confirmed", "Completed", "Cancelled"
    ]

    if not appointment_id.isdigit() or new_status not in allowed_statuses:
        return "Invalid appointment ID or status.", 400

    db = get_connection()

    try:
        cursor = db.cursor()
        cursor.execute(
            "UPDATE patients SET status = %s WHERE id = %s",
            (new_status, int(appointment_id))
        )
        db.commit()
    finally:
        cursor.close()
        db.close()

    return redirect(url_for("admin_dashboard"))


# Edit Appointment
@app.route("/admin/edit/<int:appointment_id>", methods=["GET", "POST"])
@admin_required
def edit_appointment(appointment_id):
    db = get_connection()

    try:
        cursor = db.cursor(dictionary=True)

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            age_text = request.form.get("age", "")
            doctor = request.form.get("doctor", "").strip()
            date = request.form.get("date", "")

            if (
                not name
                or not age_text.isdigit()
                or not doctor
                or not date
            ):
                cursor.execute(
                    "SELECT * FROM patients WHERE id = %s",
                    (appointment_id,)
                )
                record = cursor.fetchone()

                if not record:
                    return "Appointment not found.", 404

                return render_template(
                    "edit_appointment.html",
                    record=record,
                    error="Please enter valid appointment details."
                )

            age = int(age_text)

            if age < 1 or age > 120:
                cursor.execute(
                    "SELECT * FROM patients WHERE id = %s",
                    (appointment_id,)
                )
                record = cursor.fetchone()

                if not record:
                    return "Appointment not found.", 404

                return render_template(
                    "edit_appointment.html",
                    record=record,
                    error="Age must be between 1 and 120."
                )

            cursor.execute(
                """
                UPDATE patients
                SET name = %s,
                    age = %s,
                    doctor = %s,
                    appointment_date = %s
                WHERE id = %s
                """,
                (name, age, doctor, date, appointment_id)
            )
            db.commit()

            return redirect(url_for("admin_dashboard"))

        cursor.execute(
            "SELECT * FROM patients WHERE id = %s",
            (appointment_id,)
        )
        record = cursor.fetchone()

        if not record:
            return "Appointment not found.", 404

        return render_template(
            "edit_appointment.html",
            record=record
        )

    finally:
        cursor.close()
        db.close()


# Delete Appointment
@app.route("/admin/delete/<int:appointment_id>", methods=["POST"])
@admin_required
def delete_appointment(appointment_id):
    db = get_connection()

    try:
        cursor = db.cursor()
        cursor.execute(
            "DELETE FROM patients WHERE id = %s",
            (appointment_id,)
        )
        db.commit()
    finally:
        cursor.close()
        db.close()

    return redirect(url_for("admin_dashboard"))


# Start Flask Application
if __name__ == "__main__":
    app.run(debug=True)
