# Receipt Analyzer 📄💰

A powerful web application that analyzes grocery store receipts using OCR (Optical Character Recognition) to automatically extract items, prices, and quantities, then categorizes them for expense tracking and budgeting insights.

## Features ✨

- **Smart OCR Processing**: Upload receipt images and automatically extract text using advanced OCR
- **Intelligent Parsing**: Identifies items, quantities, and prices from receipt text
- **Auto-Categorization**: Automatically sorts items into categories (fruits, vegetables, meat, dairy, etc.)
- **Expense Tracking**: Track spending over time with beautiful charts and analytics
- **Category Analysis**: See spending breakdown by food categories
- **Modern Web Interface**: Clean, responsive design with drag-and-drop file upload
- **Data Persistence**: SQLite database stores all receipt data for historical analysis

## Categories Supported 🏷️

- **Fruits**: Apples, bananas, oranges, berries, etc.
- **Vegetables**: Carrots, lettuce, tomatoes, peppers, etc.
- **Meat**: Chicken, beef, pork, fish, seafood
- **Dairy**: Milk, cheese, yogurt, eggs
- **Grains**: Bread, rice, pasta, cereals
- **Beverages**: Water, juice, soda, coffee, tea
- **Snacks**: Chips, nuts, candy, cookies
- **Frozen**: Frozen meals, ice cream, frozen vegetables
- **Pantry**: Oils, spices, condiments, baking supplies
- **Canned Goods**: Canned vegetables, soups, sauces
- **Personal Care**: Shampoo, soap, toothpaste
- **Household**: Cleaning supplies, paper products
- **Bakery**: Fresh baked goods, pastries
- **Other**: Miscellaneous items

## Installation 🚀

### Prerequisites

- Python 3.8 or higher
- Tesseract OCR engine

### Install Tesseract OCR

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

### Install the Application

1. **Clone or download the application files**

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run the application:**
```bash
python app.py
```

4. **Access the application:**
Open your web browser and go to `http://localhost:5000`

## Usage 📱

### 1. Upload a Receipt
- Click "Upload Receipt" in the navigation
- Drag and drop an image file or click to browse
- Supported formats: JPG, PNG, GIF, BMP, TIFF
- Click "Analyze Receipt" to process

### 2. View Results
- See extracted items with categories, quantities, and prices
- Review the category breakdown chart
- Check the raw OCR text if needed

### 3. Browse Your Receipts
- View all uploaded receipts in "My Receipts"
- Click on any receipt to see detailed breakdown
- Delete receipts you no longer need

### 4. Analyze Spending
- Visit the "Analytics" page for insights
- View spending by category with pie charts
- See spending trends over time with line charts
- Filter by different time periods (7 days, 30 days, 3 months, 1 year)

## Tips for Best Results 📸

1. **Good Lighting**: Ensure receipts are well-lit and clearly visible
2. **Avoid Shadows**: Keep the receipt flat and avoid shadows or glare
3. **Clear Images**: Use high-resolution, non-blurry images
4. **Complete Receipt**: Include the entire receipt in the frame
5. **Straight Orientation**: Keep receipts as straight as possible

## Project Structure 📁

```
receipt-analyzer/
├── app.py                 # Main Flask application
├── receipt_parser.py      # OCR text parsing logic
├── item_categorizer.py    # Item categorization system
├── database.py           # SQLite database management
├── requirements.txt      # Python dependencies
├── templates/           # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── upload.html
│   ├── receipt_detail.html
│   ├── receipts.html
│   └── analytics.html
├── static/
│   └── css/
│       └── style.css    # Custom CSS styles
├── uploads/             # Uploaded receipt images (created automatically)
└── receipts.db         # SQLite database (created automatically)
```

## Technical Details 🔧

### OCR Processing
- Uses **pytesseract** for text extraction
- Applies image preprocessing with OpenCV for better OCR accuracy
- Handles various image formats and qualities

### Text Parsing
- Regular expressions to identify prices and quantities
- Smart filtering to remove non-item lines (totals, taxes, headers)
- Handles multiple price and quantity formats

### Categorization
- Rule-based categorization with 800+ predefined items
- Fuzzy string matching for similar items
- Fallback to keyword-based categorization
- Easily extensible category system

### Database Schema
```sql
-- Receipts table
receipts (id, filename, upload_date, raw_text, store_name, total_amount, item_count)

-- Items table  
items (id, receipt_id, name, category, quantity, unit_price, total_price, raw_line)

-- Categories table
categories (id, name, description, color)
```

## Customization 🔧

### Adding New Categories
Edit `item_categorizer.py` and add items to the `category_mappings` dictionary:

```python
'new_category': [
    'item1', 'item2', 'item3'
]
```

### Modifying Parsing Rules
Adjust patterns in `receipt_parser.py`:

```python
# Add new price patterns
self.price_patterns.append(r'new_pattern')

# Add new quantity patterns  
self.quantity_patterns.append(r'new_qty_pattern')
```

### Changing UI Colors
Modify color schemes in `static/css/style.css` and update category colors.

## Troubleshooting 🔍

### Common Issues

**OCR not working:**
- Ensure Tesseract is properly installed and in your PATH
- Try preprocessing images (better lighting, contrast)
- Check that pytesseract can find the Tesseract executable

**Poor parsing results:**
- Use clearer receipt images
- Check if receipt format is supported
- Review parsing patterns in `receipt_parser.py`

**Database errors:**
- Ensure write permissions in the application directory
- Check SQLite installation
- Delete `receipts.db` to reset the database

### Getting Help
- Check the console output for error messages
- Review the raw OCR text to understand parsing issues
- Test with different receipt formats and stores

## Contributing 🤝

Feel free to contribute by:
- Adding support for new receipt formats
- Improving OCR accuracy
- Expanding the categorization system
- Enhancing the user interface
- Adding new analytics features

## License 📄

This project is open source and available under the MIT License.

## Future Enhancements 🚀

- **Mobile App**: Native mobile applications for iOS and Android
- **Receipt Templates**: Support for specific store receipt formats
- **Budget Alerts**: Notifications when spending exceeds budgets
- **Export Features**: Export data to CSV, PDF, or other formats
- **Multi-User Support**: User accounts and data separation
- **Advanced Analytics**: Predictive spending analysis and recommendations
- **Barcode Recognition**: Extract product information from barcodes
- **Integration**: Connect with banking APIs and expense management tools

---

**Happy receipt tracking!** 📊💡
