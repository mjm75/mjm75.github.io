import os
import re
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import cv2
import numpy as np
from receipt_parser import ReceiptParser
from item_categorizer import ItemCategorizer
from database import DatabaseManager
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize components
db_manager = DatabaseManager()
receipt_parser = ReceiptParser()
item_categorizer = ItemCategorizer()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(image_path):
    """Preprocess image for better OCR results"""
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply gaussian blur to reduce noise
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Apply threshold to get better contrast
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return thresh

def extract_text_from_image(image_path):
    """Extract text from image using OCR"""
    try:
        # Preprocess the image
        processed_image = preprocess_image(image_path)
        
        # Use pytesseract to extract text
        text = pytesseract.image_to_string(processed_image, config='--psm 6')
        return text.strip()
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_receipt():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = timestamp + filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Extract text from image
            extracted_text = extract_text_from_image(filepath)
            
            if not extracted_text:
                flash('Could not extract text from image. Please try a clearer image.')
                return redirect(request.url)
            
            # Parse receipt text to extract items
            items = receipt_parser.parse_receipt(extracted_text)
            
            if not items:
                flash('Could not identify any items in the receipt. Please check the image quality.')
                return redirect(request.url)
            
            # Categorize items
            categorized_items = []
            for item in items:
                category = item_categorizer.categorize_item(item['name'])
                item['category'] = category
                categorized_items.append(item)
            
            # Save to database
            receipt_id = db_manager.save_receipt(filepath, extracted_text, categorized_items)
            
            flash(f'Receipt processed successfully! Found {len(categorized_items)} items.')
            return redirect(url_for('view_receipt', receipt_id=receipt_id))
        else:
            flash('Invalid file type. Please upload an image file.')
    
    return render_template('upload.html')

@app.route('/receipt/<int:receipt_id>')
def view_receipt(receipt_id):
    receipt_data = db_manager.get_receipt(receipt_id)
    if not receipt_data:
        flash('Receipt not found')
        return redirect(url_for('index'))
    
    return render_template('receipt_detail.html', receipt=receipt_data)

@app.route('/receipts')
def list_receipts():
    receipts = db_manager.get_all_receipts()
    return render_template('receipts.html', receipts=receipts)

@app.route('/analytics')
def analytics():
    # Get spending by category
    category_spending = db_manager.get_spending_by_category()
    
    # Get spending over time
    time_spending = db_manager.get_spending_over_time()
    
    # Get recent items
    recent_items = db_manager.get_recent_items(limit=10)
    
    return render_template('analytics.html', 
                         category_spending=category_spending,
                         time_spending=time_spending,
                         recent_items=recent_items)

@app.route('/api/spending_data')
def api_spending_data():
    """API endpoint for chart data"""
    days = request.args.get('days', 30, type=int)
    
    category_spending = db_manager.get_spending_by_category(days)
    time_spending = db_manager.get_spending_over_time(days)
    recent_items = db_manager.get_recent_items(limit=10)
    
    return jsonify({
        'category_spending': category_spending,
        'time_spending': time_spending,
        'recent_items': recent_items
    })

@app.route('/api/receipt/<int:receipt_id>', methods=['DELETE'])
def delete_receipt_api(receipt_id):
    """API endpoint to delete a receipt"""
    success = db_manager.delete_receipt(receipt_id)
    if success:
        return jsonify({'message': 'Receipt deleted successfully'}), 200
    else:
        return jsonify({'error': 'Failed to delete receipt'}), 500

if __name__ == '__main__':
    # Initialize database
    db_manager.init_database()
    app.run(debug=True, host='0.0.0.0', port=5000)