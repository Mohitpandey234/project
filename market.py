from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import random
import string
from llm_service import llm_service, generate_response
import database as db
import re
from datetime import datetime
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

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

@app.route('/bill_history')
def bill_history():
    bills = db.get_bill_history()
    formatted_bills = [{
        'bill_hash': bill[0],
        'date': bill[1],
        'time': bill[2],
        'total': bill[3]
    } for bill in bills]
    return render_template('bill_history.html', bills=formatted_bills)

def create_bill_pdf(bill_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Add styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    
    # Add title and header info
    bill_hash = bill_data.get('bill_hash', 'N/A')
    elements.append(Paragraph(f"Bill #{bill_hash}", title_style))
    elements.append(Paragraph(f"Date: {bill_data['date']} {bill_data['time']}", styles['Normal']))
    elements.append(Paragraph("<br/><br/>", styles['Normal']))
    
    # Create items table
    table_data = [['Item', 'Quantity', 'Price', 'Total']]
    for item in bill_data['items']:
        table_data.append([
            item['name'],
            str(item['quantity']),
            f"${item['price']:.2f}",
            f"${item['total']:.2f}"
        ])
    
    # Add summary row
    table_data.append(['', '', 'Total:', f"${bill_data['total']:.2f}"])
    
    # Create table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.black),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer

@app.route('/download_bill/<bill_hash>')
def download_bill(bill_hash):
    bill_data = db.get_bill_by_hash(bill_hash)
    if not bill_data:
        return "Bill not found", 404
    
    pdf_buffer = create_bill_pdf(bill_data)
    return send_file(
        pdf_buffer,
        download_name=f'bill_{bill_hash}.pdf',
        as_attachment=True,
        mimetype='application/pdf'
    )

def parse_bill_command(command):
    """Parse chat commands related to bill management"""
    command = command.lower().strip()
    
    # Handle discount command
    discount_match = re.match(r'put (\d+)% discount on item (\d+)', command)
    if discount_match:
        discount, item_num = map(int, discount_match.groups())
        return {'action': 'discount', 'item': item_num - 1, 'discount': discount}
    
    # Handle quantity change command
    quantity_match = re.match(r'change quantity of item (\d+) from (\d+) to (\d+)', command)
    if quantity_match:
        item_num, old_qty, new_qty = map(int, quantity_match.groups())
        return {'action': 'quantity', 'item': item_num - 1, 'quantity': new_qty}
    
    # Handle print/done command
    if command in ['print', 'done']:
        return {'action': 'print'}
    
    return None

@app.route('/generate', methods=['POST'])
def generate():
    if 'email' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_input = request.json.get('message', '')
    current_bill = session.get('current_bill', {
        'items': [],
        'total': 0
    })
    
    # Try to parse item addition
    user_input = user_input.lower().strip()
    
    # Check for print/done command first
    if user_input in ['print', 'done']:
        command_result = {'action': 'print'}
        if not current_bill['items']:
            return jsonify({
                'response': "Cannot print empty bill. Please add items first.",
                'bill': current_bill
            })
        
        # Add timestamp and hash to bill
        now = datetime.now()
        current_bill.update({
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%H:%M:%S'),
        })
        
        # Save bill to database
        bill_hash = db.save_bill(current_bill)
        current_bill['bill_hash'] = bill_hash
        
        # Clear current bill from session
        session['current_bill'] = {'items': [], 'total': 0}
        
        return jsonify({
            'response': f"Bill saved with ID: {bill_hash}. You can download it from the bill history page.",
            'bill': None
        })

    # Check if it's a bill command
    command_result = parse_bill_command(user_input)
    if command_result:
        if command_result['action'] == 'discount':
            item_idx = command_result['item']
            if 0 <= item_idx < len(current_bill['items']):
                item = current_bill['items'][item_idx]
                discount = command_result['discount'] / 100
                item['total'] *= (1 - discount)
                current_bill['total'] = sum(item['total'] for item in current_bill['items'])
                # Update the session with the modified bill
                session['current_bill'] = current_bill
                return jsonify({
                    'response': f"Applied {command_result['discount']}% discount to item {item_idx + 1}",
                    'bill': current_bill
                })
        
        elif command_result['action'] == 'quantity':
            item_idx = command_result['item']
            if 0 <= item_idx < len(current_bill['items']):
                item = current_bill['items'][item_idx]
                item['quantity'] = command_result['quantity']
                item['total'] = item['price'] * item['quantity']
                current_bill['total'] = sum(item['total'] for item in current_bill['items'])
                # Update the session with the modified bill
                session['current_bill'] = current_bill
                return jsonify({
                    'response': f"Updated quantity for item {item_idx + 1}",
                    'bill': current_bill
                })
    
    # First pattern: quantity followed by item name (e.g., "2 dosa")
    item_match = re.match(r'(\d+)\s+(.+)', user_input)
    if not item_match:
        # Second pattern: item name followed by quantity (e.g., "dosa 2")
        item_match = re.match(r'([a-zA-Z\s]+)\s+(\d+)', user_input)
        if item_match:
            # Swap the groups since they're in reverse order
            item_name, quantity = item_match.groups()
            quantity = int(quantity)
            item_name = item_name.strip()
        else:
            # If no match found, pass to LLM for processing
            response = generate_response(user_input)
            return jsonify({
                'response': response,
                'bill': current_bill
            })
    else:
        quantity, item_name = item_match.groups()
        quantity = int(quantity)
        item_name = item_name.strip()
    
    # Search for item in inventory
    with db.get_db() as conn:
        cursor = conn.execute('SELECT item_name, price FROM inventory WHERE item_name LIKE ?', (f'%{item_name}%',))
        items = cursor.fetchall()
        
        if items:
            item = items[0]  # Take the first matching item
            total = item[1] * quantity
            current_bill['items'].append({
                'name': item[0],
                'quantity': quantity,
                'price': item[1],
                'total': total
            })
            current_bill['total'] = sum(item['total'] for item in current_bill['items'])
            # Update the session with the modified bill
            session['current_bill'] = current_bill
            
            return jsonify({
                'response': f"Added {quantity} {item[0]} to the bill.",
                'bill': current_bill
            })
        else:
            return jsonify({
                'response': f"Sorry, I couldn't find '{item_name}' in the inventory.",
                'bill': current_bill
            })

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