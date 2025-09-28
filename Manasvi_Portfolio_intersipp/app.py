import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import sqlite3
from werkzeug.utils import secure_filename

# --- Config ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
DIARY_DIR = os.path.join(UPLOAD_DIR, "diaries")
CERT_DIR = os.path.join(UPLOAD_DIR, "certificates")
DB_PATH = os.path.join(BASE_DIR, "internship.db")
ALLOWED = {"png", "jpg", "jpeg", "pdf"}

os.makedirs(DIARY_DIR, exist_ok=True)
os.makedirs(CERT_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = "replace-this-with-a-secure-key"

# --- DB helpers ---
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS internships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll TEXT NOT NULL,
            student_name TEXT NOT NULL,
            company TEXT,
            start_date TEXT,
            end_date TEXT,
            note TEXT,
            created_at TEXT
        )""")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS diaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll TEXT NOT NULL,
            title TEXT,
            date TEXT,
            filename TEXT,
            uploaded_at TEXT
        )""")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS certificates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll TEXT NOT NULL,
            cert_type TEXT,
            issued_by TEXT,
            date TEXT,
            filename TEXT,
            uploaded_at TEXT
        )""")
    conn.commit()
    conn.close()

def allowed_file(fn):
    return "." in fn and fn.rsplit(".", 1)[1].lower() in ALLOWED

# --- Routes ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    conn = get_db()
    rows = conn.execute("SELECT * FROM internships ORDER BY roll").fetchall()
    conn.close()
    return render_template("dashboard.html", internships=rows)

@app.route("/add", methods=("GET", "POST"))
def add_internship():
    if request.method == "POST":
        roll = request.form.get("roll").strip()
        student_name = request.form.get("student_name").strip()
        company = request.form.get("company")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        note = request.form.get("note")
        if not roll or not student_name:
            flash("Roll and Student name required", "danger")
            return redirect(url_for("add_internship"))
        conn = get_db()
        conn.execute(
            "INSERT INTO internships (roll, student_name, company, start_date, end_date, note, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (roll, student_name, company, start_date, end_date, note, datetime.utcnow().isoformat())
        )
        conn.commit()
        conn.close()
        flash("Internship added", "success")
        return redirect(url_for("dashboard"))
    return render_template("add_internship.html")

@app.route("/diary", methods=("GET", "POST"))
def diary_upload():
    if request.method == "POST":
        roll = request.form.get("roll").strip()
        title = request.form.get("title")
        date = request.form.get("date") or datetime.utcnow().strftime("%Y-%m-%d")
        file = request.files.get("file")
        if not roll or not file or not allowed_file(file.filename):
            flash("Valid roll and file required (png/jpg/pdf)", "danger")
            return redirect(url_for("diary_upload"))
        filename = secure_filename(f"{roll}_{int(datetime.utcnow().timestamp())}_{file.filename}")
        path = os.path.join(DIARY_DIR, filename)
        file.save(path)
        conn = get_db()
        conn.execute("INSERT INTO diaries (roll, title, date, filename, uploaded_at) VALUES (?, ?, ?, ?, ?)",
                     (roll, title, date, filename, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
        flash("Diary uploaded", "success")
        return redirect(url_for("diary_upload"))
    conn = get_db()
    diaries = conn.execute("SELECT * FROM diaries ORDER BY uploaded_at DESC LIMIT 50").fetchall()
    conn.close()
    return render_template("diary_upload.html", diaries=diaries)

@app.route("/certificates", methods=("GET", "POST"))
def certificates():
    if request.method == "POST":
        roll = request.form.get("roll").strip()
        cert_type = request.form.get("cert_type")
        issued_by = request.form.get("issued_by")
        date = request.form.get("date") or datetime.utcnow().strftime("%Y-%m-%d")
        file = request.files.get("file")
        if not roll or not file or not allowed_file(file.filename):
            flash("Valid roll and file required (png/jpg/pdf)", "danger")
            return redirect(url_for("certificates"))
        filename = secure_filename(f"{roll}_{int(datetime.utcnow().timestamp())}_{file.filename}")
        path = os.path.join(CERT_DIR, filename)
        file.save(path)
        conn = get_db()
        conn.execute("INSERT INTO certificates (roll, cert_type, issued_by, date, filename, uploaded_at) VALUES (?, ?, ?, ?, ?, ?)",
                     (roll, cert_type, issued_by, date, filename, datetime.utcnow().isoformat()))
        conn.commit()
        conn.close()
        flash("Certificate uploaded", "success")
        return redirect(url_for("certificates"))
    conn = get_db()
    certs = conn.execute("SELECT * FROM certificates ORDER BY uploaded_at DESC LIMIT 50").fetchall()
    conn.close()
    return render_template("certificates.html", certs=certs)

@app.route("/uploads/diaries/<filename>")
def uploaded_diary(filename):
    return send_from_directory(DIARY_DIR, filename)

@app.route("/uploads/certificates/<filename>")
def uploaded_cert(filename):
    return send_from_directory(CERT_DIR, filename)

# Printable for rolls 37-54
ROLLS_37_54 = [str(i) for i in range(37, 55)]

@app.route("/print/diary")
def print_diary():
    conn = get_db()
    diaries = conn.execute("SELECT * FROM diaries WHERE roll IN ({}) ORDER BY roll".format(",".join("?"*len(ROLLS_37_54))),
                           ROLLS_37_54).fetchall()
    conn.close()
    return render_template("printable_diary.html", diaries=diaries)

@app.route("/print/certificates")
def print_certificates():
    conn = get_db()
    certs = conn.execute("SELECT * FROM certificates WHERE roll IN ({}) ORDER BY roll".format(",".join("?"*len(ROLLS_37_54))),
                         ROLLS_37_54).fetchall()
    # create present map for checklist 37-54
    present = {r: False for r in ROLLS_37_54}
    for c in certs:
        present[c["roll"]] = True
    conn.close()
    return render_template("printable_certificates.html", present=present)
@app.route("/add")
def add():
    return render_template("add.html")

 




# --- Start ---
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
