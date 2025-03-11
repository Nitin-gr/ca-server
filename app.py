from flask import Flask, request, render_template, redirect, url_for, session, flash
import toml
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change to something more secure!

ACL_PATH = './acl/acl.toml'

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'password123'

def load_acl():
    if not os.path.exists(ACL_PATH):
        return {'users': []}
    return toml.load(ACL_PATH)

def save_acl(data):
    with open(ACL_PATH, 'w') as f:
        toml.dump(data, f)

@app.route('/')
def home():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        flash('Invalid credentials!')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    acl_data = load_acl()
    return render_template('dashboard.html', users=acl_data['users'])

@app.route('/add-user', methods=['GET', 'POST'])
def add_user():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    success = False  # Flag to check if user was added

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        hosts_allowed = request.form['hosts'].split(',')
        validity = request.form['validity']

        acl_data = load_acl()
        acl_data['users'].append({
            'name': name,
            'email': email,
            'hosts_allowed': hosts_allowed,
            'validity': validity
        })
        save_acl(acl_data)

        success = True  # Set success flag to True

    return render_template('add_user.html', success=success)

@app.route('/edit-user/<name>', methods=['GET', 'POST'])
def edit_user(name):
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    acl_data = load_acl()
    user = next((user for user in acl_data['users'] if user['name'] == name), None)

    if not user:
        flash('User not found!')
        return redirect(url_for('dashboard'))

    success = False  # Flag to indicate if the update was successful

    if request.method == 'POST':
        user['email'] = request.form['email']
        user['hosts_allowed'] = request.form['hosts'].split(',')
        user['validity'] = request.form['validity']
        save_acl(acl_data)

        success = True  # Set success flag to True

    return render_template('edit_user.html', user=user, success=success)

@app.route('/delete-user/<name>', methods=['POST'])
def delete_user(name):
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    acl_data = load_acl()
    acl_data['users'] = [user for user in acl_data['users'] if user['name'] != name]
    save_acl(acl_data)

    flash(f'User {name} deleted successfully!')
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
