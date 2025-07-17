# GIS Institute App with View Students + PDF Receipt (Browser UI)
import webview
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, send_file
import threading
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

# -------------------- Flask App Backend --------------------
app = Flask(__name__)
conn = sqlite3.connect("gis_institute.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        course TEXT,
        fees_total INTEGER,
        fees_paid INTEGER,
        date TEXT
    )
''')
conn.commit()

@app.route('/')
def index():
    return render_template_string(html_template)

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    name = data['name']
    email = data['email']
    phone = data['phone']
    course = data['course']
    fees_total = int(data['fees_total'])
    fees_paid = int(data['fees_paid'])
    date = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("INSERT INTO students (name, email, phone, course, fees_total, fees_paid, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                   (name, email, phone, course, fees_total, fees_paid, date))
    conn.commit()
    return jsonify({"message": "Student added successfully!", "name": name, "course": course, "fees_paid": fees_paid, "date": date})

@app.route('/receipt/<name>')
def download_receipt(name):
    cursor.execute("SELECT name, course, fees_paid, date FROM students WHERE name = ? ORDER BY id DESC LIMIT 1", (name,))
    row = cursor.fetchone()
    if row:
        filename = f"receipt_{name.replace(' ', '_')}.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        c.setFont("Helvetica", 14)
        c.drawString(100, 800, "GIS Institute Receipt")
        c.drawString(100, 770, f"Name: {row[0]}")
        c.drawString(100, 750, f"Course: {row[1]}")
        c.drawString(100, 730, f"Amount Paid: ₹{row[2]}")
        c.drawString(100, 710, f"Date: {row[3]}")
        c.save()
        return send_file(filename, as_attachment=True)
    return "Receipt not found", 404

@app.route('/students')
def view_students():
    cursor.execute("SELECT name, email, phone, course, fees_total, fees_paid, date FROM students ORDER BY id DESC")
    data = cursor.fetchall()
    return render_template_string(student_template, students=data)

html_template = '''
<!DOCTYPE html>
<html>
<head>
    <title>GIS Institute Admission</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        input, button { margin: 5px; padding: 8px; width: 300px; }
        #receipt-btn { display: none; margin-top: 10px; }
    </style>
</head>
<body>
    <h2>GIS Institute - Admission Form</h2>
    <input id="name" placeholder="Student Name"><br>
    <input id="email" placeholder="Email"><br>
    <input id="phone" placeholder="Phone"><br>
    <input id="course" placeholder="Course"><br>
    <input id="fees_total" placeholder="Total Fees"><br>
    <input id="fees_paid" placeholder="Fees Paid"><br>
    <button onclick="submitForm()">Submit</button>
    <p id="msg"></p>
    <a id="receipt-btn" href="#" target="_blank">Download Receipt</a>
    <br><br>
    <a href="/students" target="_blank">📄 View All Students</a>

<script>
function submitForm() {
    const data = {
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        phone: document.getElementById('phone').value,
        course: document.getElementById('course').value,
        fees_total: document.getElementById('fees_total').value,
        fees_paid: document.getElementById('fees_paid').value
    };
    fetch('/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }).then(res => res.json())
      .then(res => {
          document.getElementById('msg').innerText = res.message;
          const link = document.getElementById('receipt-btn');
          link.href = `/receipt/${data.name}`;
          link.style.display = 'inline';
          link.innerText = 'Download Receipt';
      })
      .catch(err => alert("Error submitting form."));
}
</script>
</body>
</html>
'''

student_template = '''
<!DOCTYPE html>
<html>
<head><title>All Students</title>
<style>
    table { width: 100%; border-collapse: collapse; }
    th, td { border: 1px solid #aaa; padding: 8px; text-align: left; }
    th { background: #ddd; }
</style>
</head>
<body>
    <h2>All Admitted Students</h2>
    <table>
        <tr>
            <th>Name</th><th>Email</th><th>Phone</th><th>Course</th><th>Total Fees</th><th>Fees Paid</th><th>Date</th>
        </tr>
        {% for s in students %}
        <tr>
            <td>{{s[0]}}</td><td>{{s[1]}}</td><td>{{s[2]}}</td><td>{{s[3]}}</td><td>{{s[4]}}</td><td>{{s[5]}}</td><td>{{s[6]}}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
'''

# -------------------- Launch WebView --------------------
def run_flask():
    app.run(debug=False, port=5001)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    webview.create_window("GIS Institute Admission", "http://localhost:5001")
