from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import string
from llm_service import llm_service

# Create the app instance
app = Flask(__name__)
app.secret_key = ''.join(random.choices(string.ascii_letters + string.digits, k=32))  # for session management

# Define a route for the home page
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/auth')
def auth():
    return render_template('auth.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Here you would typically validate the credentials
        # For demo purposes, we'll just store the email in session
        session['email'] = email
        
        # Generate a random 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))
        session['otp'] = otp
        
        # In a real application, you would send this OTP to the user's email
        print(f"Generated OTP for {email}: {otp}")  # For testing purposes
        
        return render_template('verify.html')
    return redirect(url_for('auth'))

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        if 'otp' not in session:
            return redirect(url_for('auth'))
        
        # Get all OTP digits from the form
        submitted_otp = ''.join([request.form.get(f'otp_{i}', '') for i in range(6)])
        
        if submitted_otp == session['otp']:
            # Clear the OTP from session after successful verification
            session.pop('otp', None)
            return render_template('dashboard.html')
        else:
            return redirect(url_for('verify'))
    
    # Allow direct access to dashboard if user is already verified
    if 'email' in session and 'otp' not in session:
        return render_template('dashboard.html')
    return redirect(url_for('auth'))

@app.route('/generate', methods=['POST'])
def generate():
    if 'email' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    prompt = request.json.get('prompt')
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    try:
        response = llm_service.generate_response(prompt)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)