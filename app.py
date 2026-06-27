import sqlite3
import random
import os
from flask import Flask, render_template, request, redirect, session, url_for

app = Flask(__name__)
app.secret_key = 'binary_mlm_secure_key_v4'

# Database and Testing Data Setup
def init_db():
    conn = sqlite3.connect('binary_mlm.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        login_id TEXT UNIQUE,
                        password TEXT,
                        name TEXT,
                        address TEXT,
                        pincode TEXT,
                        parent_id TEXT,
                        position TEXT)''')
    
    # Reset database and inject fresh text data to avoid tuple brackets
    cursor.execute("DELETE FROM users")
    
    # 1. Main Root User (YOU)
    cursor.execute("INSERT INTO users (login_id, password, name, address, pincode, parent_id, position) VALUES ('swapnil-sanjay-khude-345', 'pass208', 'Swapnil Sanjay Khude', 'At Post Taluka District State', '411001', 'ADMIN', 'None')")
    
    # 2. Level 2 Under You (Left & Right Strings)
    cursor.execute("INSERT INTO users (login_id, password, name, address, pincode, parent_id, position) VALUES ('sanket789', 'pass789', 'Sanket Sanjay Khude', 'At Post Taluka District State', '411003', 'swapnil-sanjay-khude-345', 'Left')")
    cursor.execute("INSERT INTO users (login_id, password, name, address, pincode, parent_id, position) VALUES ('sanjay555', 'pass555', 'Sanjay Narayan Khude', 'At Post Taluka District State', '411005', 'swapnil-sanjay-khude-345', 'Right')")
    
    # 3. Level 3 Under Sanket & Sanjay
    cursor.execute("INSERT INTO users (login_id, password, name, address, pincode, parent_id, position) VALUES ('sheshu456', 'pass456', 'Sheshurao Kalyan', 'At Post Taluka District State', '411002', 'sanket789', 'Left')")
    cursor.execute("INSERT INTO users (login_id, password, name, address, pincode, parent_id, position) VALUES ('rohan111', 'pass111', 'Rohan Mane', 'At Post Taluka District State', '411004', 'sanjay555', 'Right')")
    
    conn.commit()
    conn.close()

# Recursive Network Tree Counter Logic
def get_team_counts(login_id):
    conn = sqlite3.connect('binary_mlm.db')
    cursor = conn.cursor()
    cursor.execute("SELECT login_id FROM users WHERE parent_id = ?", (login_id,))
    directs = [r[0] for r in cursor.fetchall()]
    ind_count = len(directs)
    
    all_team = []
    queue = list(directs)
    while queue:
        current = queue.pop(0)
        all_team.append(current)
        cursor.execute("SELECT login_id FROM users WHERE parent_id = ?", (current,))
        children = [r[0] for r in cursor.fetchall()]
        queue.extend(children)
        
    conn.close()
    return ind_count, len(all_team)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_id = request.form['login_id'].strip()
        password = request.form['password'].strip()
        
        conn = sqlite3.connect('binary_mlm.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE login_id = ? AND password = ?", (login_id, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = login_id
            session['history'] = []
            return redirect(url_for('dashboard', view_id=login_id))
        return "<h3>Invalid ID or Password! Please try again.</h3><a href='/'>Go Back</a>"
    return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    address = request.form['address']
    pincode = request.form['pincode']
    parent_id = request.form['parent_id'].strip()
    position = request.form['position']
    
    conn = sqlite3.connect('binary_mlm.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE parent_id = ? AND position = ?", (parent_id, position))
    if cursor.fetchone():
        conn.close()
        return f"<h3>Error: {position} position is already occupied under Parent ID {parent_id}!</h3><a href='/'>Go Back</a>"
    
    clean_name = name.replace(" ", "").lower() if name else "user"
    login_id = clean_name + str(random.randint(100, 999))
    password = "pass" + str(random.randint(100, 999))
    
    try:
        cursor.execute("INSERT INTO users (login_id, password, name, address, pincode, parent_id, position) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (login_id, password, name, address, pincode, parent_id, position))
        conn.commit()
        return f"<div style='font-family:sans-serif; padding:20px;'><h2>Registration Successful!</h2><p>Position: <b>Team {position}</b></p><p>Your Login ID: <b>{login_id}</b></p><p>Password: <b>{password}</b></p><br><a href='/'>Login Here</a></div>"
    except Exception as e:
        return "<h3>Error in fields or Sponsor ID!</h3><a href='/'>Go Back</a>"
    finally:
        conn.close()

@app.route('/dashboard/<view_id>')
def dashboard(view_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('binary_mlm.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, address, pincode FROM users WHERE login_id = ?", (view_id,))
    user_data = cursor.fetchone()
    
    if not user_data:
        conn.close()
        return "User not found!"
        
    # Extract strings correctly to completely eliminate tuple formatting in HTML
    cursor.execute("SELECT login_id, name FROM users WHERE parent_id = ? AND position = 'Left'", (view_id,))
    left_row = cursor.fetchone()
    left_id = left_row[0] if left_row else None
    left_name = left_row[1] if left_row else None
    
    cursor.execute("SELECT login_id, name FROM users WHERE parent_id = ? AND position = 'Right'", (view_id,))
    right_row = cursor.fetchone()
    right_id = right_row[0] if right_row else None
    right_name = right_row[1] if right_row else None
    conn.close()
    
    ind_count, team_count = get_team_counts(view_id)
    history = session.get('history', [])
            
    return render_template('dashboard.html', 
                           current_user=session['user_id'],
                           view_id=view_id,
                           name=user_data[0], 
                           address=user_data[1], 
                           pincode=user_data[2],
                           ind_count=ind_count,
                           team_count=team_count,
                           left_id=left_id,
                           left_name=left_name,
                           right_id=right_id,
                           right_name=right_name,
                           history_len=len(history))

@app.route('/navigate/<target_id>')
def navigate(target_id):
    history = session.get('history', [])
    current_view = request.args.get('current_view')
    if current_view and (not history or history[-1] != current_view):
        history.append(current_view)
    session['history'] = history
    return redirect(url_for('dashboard', view_id=target_id))

@app.route('/go-back')
def go_back():
    history = session.get('history', [])
    if history:
        prev_id = history.pop()
        session['history'] = history
        return redirect(url_for('dashboard', view_id=prev_id))
    return redirect(url_for('dashboard', view_id=session.get('user_id')))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)