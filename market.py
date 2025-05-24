from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import random
import string
from llm_service import llm_service
import database as db
import re

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

@app.route('/inventory')
def inventory():
    if 'email' not in session:
        return redirect(url_for('auth'))
    items = db.get_all_items()
    return render_template('inventory.html', inventory=items)

@app.route('/inventory/command', methods=['POST'])
def inventory_command():
    if 'email' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    command = request.json.get('command', '').strip().lower()
    if not command:
        return jsonify({'error': 'No command provided'}), 400

    try:
        # Add item command
        if command.startswith('add '):
            match = re.match(r'add (.+) (\d+\.?\d*)', command)
            if match:
                item_name = match.group(1).strip()
                price = float(match.group(2))
                db.add_item(item_name, price)
                message = f"Added {item_name} with price ${price:.2f}"
            else:
                message = "Invalid format. Use: add [item name] [price]"

        # Update price command
        elif command.startswith('update price '):
            match = re.match(r'update price (.+) (\d+\.?\d*)', command)
            if match:
                item_name = match.group(1).strip()
                new_price = float(match.group(2))
                db.update_item_price(item_name, new_price)
                message = f"Updated price of {item_name} to ${new_price:.2f}"
            else:
                message = "Invalid format. Use: update price [item name] [new price]"

        # Update name command
        elif command.startswith('update name '):
            match = re.match(r'update name (.+) (.+)', command)
            if match:
                old_name = match.group(1).strip()
                new_name = match.group(2).strip()
                db.update_item_name(old_name, new_name)
                message = f"Updated item name from {old_name} to {new_name}"
            else:
                message = "Invalid format. Use: update name [old name] [new name]"

        # Delete command
        elif command.startswith('delete '):
            item_name = command[7:].strip()
            if item_name:
                db.delete_item(item_name)
                message = f"Deleted {item_name} from inventory"
            else:
                message = "Invalid format. Use: delete [item name]"

        else:
            message = "Unknown command. Available commands: add, update price, update name, delete"

        # Get updated inventory
        inventory = db.get_all_items()
        return jsonify({
            'message': message,
            'inventory': inventory
        })

    except Exception as e:
        return jsonify({
            'message': f"Error: {str(e)}",
            'inventory': db.get_all_items()
        })

if __name__ == '__main__':
    app.run(debug=True)