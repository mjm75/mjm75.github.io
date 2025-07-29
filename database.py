import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import os

class DatabaseManager:
    def __init__(self, db_path: str = 'receipts.db'):
        self.db_path = db_path
        
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create receipts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_text TEXT,
                store_name TEXT,
                store_address TEXT,
                receipt_date TEXT,
                total_amount REAL,
                item_count INTEGER
            )
        ''')
        
        # Create items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_id INTEGER,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                unit_price REAL,
                total_price REAL,
                raw_line TEXT,
                FOREIGN KEY (receipt_id) REFERENCES receipts (id)
            )
        ''')
        
        # Create categories table for tracking category spending
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                color TEXT DEFAULT '#3498db'
            )
        ''')
        
        # Insert default categories
        default_categories = [
            ('fruits', 'Fresh and dried fruits', '#e74c3c'),
            ('vegetables', 'Fresh vegetables and produce', '#27ae60'),
            ('meat', 'Meat, poultry, and seafood', '#e67e22'),
            ('dairy', 'Milk, cheese, yogurt, and eggs', '#f39c12'),
            ('grains', 'Bread, rice, pasta, and cereals', '#d35400'),
            ('beverages', 'Drinks and beverages', '#3498db'),
            ('snacks', 'Snacks and treats', '#9b59b6'),
            ('frozen', 'Frozen foods', '#1abc9c'),
            ('pantry', 'Pantry staples and condiments', '#34495e'),
            ('canned_goods', 'Canned and jarred foods', '#95a5a6'),
            ('personal_care', 'Personal care items', '#e91e63'),
            ('household', 'Household and cleaning supplies', '#607d8b'),
            ('bakery', 'Bakery items', '#ff9800'),
            ('other', 'Miscellaneous items', '#795548')
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO categories (name, description, color) 
            VALUES (?, ?, ?)
        ''', default_categories)
        
        conn.commit()
        conn.close()
    
    def save_receipt(self, filename: str, raw_text: str, items: List[Dict]) -> int:
        """Save a receipt and its items to the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Calculate totals
        total_amount = sum(item.get('price', 0) for item in items)
        item_count = len(items)
        
        # Extract store info (you might want to enhance this)
        store_name = self._extract_store_name(raw_text)
        
        # Insert receipt
        cursor.execute('''
            INSERT INTO receipts (filename, raw_text, store_name, total_amount, item_count)
            VALUES (?, ?, ?, ?, ?)
        ''', (filename, raw_text, store_name, total_amount, item_count))
        
        receipt_id = cursor.lastrowid
        
        # Insert items
        for item in items:
            cursor.execute('''
                INSERT INTO items (receipt_id, name, category, quantity, unit_price, total_price, raw_line)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                receipt_id,
                item.get('name', ''),
                item.get('category', 'other'),
                item.get('quantity', 1),
                item.get('unit_price', 0),
                item.get('price', 0),
                item.get('raw_line', '')
            ))
        
        conn.commit()
        conn.close()
        
        return receipt_id
    
    def get_receipt(self, receipt_id: int) -> Optional[Dict]:
        """Get a receipt with its items"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get receipt info
        cursor.execute('''
            SELECT id, filename, upload_date, raw_text, store_name, store_address, 
                   receipt_date, total_amount, item_count
            FROM receipts WHERE id = ?
        ''', (receipt_id,))
        
        receipt_row = cursor.fetchone()
        if not receipt_row:
            conn.close()
            return None
        
        receipt = {
            'id': receipt_row[0],
            'filename': receipt_row[1],
            'upload_date': receipt_row[2],
            'raw_text': receipt_row[3],
            'store_name': receipt_row[4],
            'store_address': receipt_row[5],
            'receipt_date': receipt_row[6],
            'total_amount': receipt_row[7],
            'item_count': receipt_row[8]
        }
        
        # Get items for this receipt
        cursor.execute('''
            SELECT id, name, category, quantity, unit_price, total_price, raw_line
            FROM items WHERE receipt_id = ?
            ORDER BY name
        ''', (receipt_id,))
        
        items = []
        for item_row in cursor.fetchall():
            items.append({
                'id': item_row[0],
                'name': item_row[1],
                'category': item_row[2],
                'quantity': item_row[3],
                'unit_price': item_row[4],
                'total_price': item_row[5],
                'raw_line': item_row[6]
            })
        
        receipt['items'] = items
        conn.close()
        
        return receipt
    
    def get_all_receipts(self) -> List[Dict]:
        """Get all receipts (summary info only)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, filename, upload_date, store_name, total_amount, item_count
            FROM receipts 
            ORDER BY upload_date DESC
        ''')
        
        receipts = []
        for row in cursor.fetchall():
            receipts.append({
                'id': row[0],
                'filename': row[1],
                'upload_date': row[2],
                'store_name': row[3],
                'total_amount': row[4],
                'item_count': row[5]
            })
        
        conn.close()
        return receipts
    
    def get_spending_by_category(self, days: int = 30) -> List[Dict]:
        """Get spending by category for the last N days"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            SELECT i.category, SUM(i.total_price) as total_spent, COUNT(i.id) as item_count,
                   c.color
            FROM items i
            JOIN receipts r ON i.receipt_id = r.id
            LEFT JOIN categories c ON i.category = c.name
            WHERE r.upload_date >= ?
            GROUP BY i.category
            ORDER BY total_spent DESC
        ''', (cutoff_date.isoformat(),))
        
        categories = []
        for row in cursor.fetchall():
            categories.append({
                'category': row[0],
                'total_spent': round(row[1], 2),
                'item_count': row[2],
                'color': row[3] or '#3498db'
            })
        
        conn.close()
        return categories
    
    def get_spending_over_time(self, days: int = 30) -> List[Dict]:
        """Get daily spending over the last N days"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute('''
            SELECT DATE(r.upload_date) as date, SUM(r.total_amount) as daily_total
            FROM receipts r
            WHERE r.upload_date >= ?
            GROUP BY DATE(r.upload_date)
            ORDER BY date
        ''', (cutoff_date.isoformat(),))
        
        daily_spending = []
        for row in cursor.fetchall():
            daily_spending.append({
                'date': row[0],
                'total': round(row[1], 2)
            })
        
        conn.close()
        return daily_spending
    
    def get_recent_items(self, limit: int = 10) -> List[Dict]:
        """Get recently purchased items"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT i.name, i.category, i.total_price, r.upload_date, r.store_name
            FROM items i
            JOIN receipts r ON i.receipt_id = r.id
            ORDER BY r.upload_date DESC
            LIMIT ?
        ''', (limit,))
        
        recent_items = []
        for row in cursor.fetchall():
            recent_items.append({
                'name': row[0],
                'category': row[1],
                'price': row[2],
                'date': row[3],
                'store': row[4]
            })
        
        conn.close()
        return recent_items
    
    def get_top_items_by_frequency(self, limit: int = 10) -> List[Dict]:
        """Get most frequently purchased items"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, category, COUNT(*) as frequency, AVG(total_price) as avg_price
            FROM items
            GROUP BY LOWER(name), category
            ORDER BY frequency DESC
            LIMIT ?
        ''', (limit,))
        
        top_items = []
        for row in cursor.fetchall():
            top_items.append({
                'name': row[0],
                'category': row[1],
                'frequency': row[2],
                'avg_price': round(row[3], 2)
            })
        
        conn.close()
        return top_items
    
    def get_monthly_summary(self) -> Dict:
        """Get monthly spending summary"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Current month
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        cursor.execute('''
            SELECT COUNT(id) as receipt_count, SUM(total_amount) as total_spent
            FROM receipts
            WHERE upload_date >= ?
        ''', (current_month_start.isoformat(),))
        
        current_month = cursor.fetchone()
        
        # Previous month
        if current_month_start.month == 1:
            prev_month_start = current_month_start.replace(year=current_month_start.year-1, month=12)
        else:
            prev_month_start = current_month_start.replace(month=current_month_start.month-1)
        
        cursor.execute('''
            SELECT COUNT(id) as receipt_count, SUM(total_amount) as total_spent
            FROM receipts
            WHERE upload_date >= ? AND upload_date < ?
        ''', (prev_month_start.isoformat(), current_month_start.isoformat()))
        
        previous_month = cursor.fetchone()
        
        conn.close()
        
        return {
            'current_month': {
                'receipt_count': current_month[0] or 0,
                'total_spent': round(current_month[1] or 0, 2)
            },
            'previous_month': {
                'receipt_count': previous_month[0] or 0,
                'total_spent': round(previous_month[1] or 0, 2)
            }
        }
    
    def search_items(self, query: str) -> List[Dict]:
        """Search for items by name"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT i.name, i.category, i.total_price, r.upload_date, r.store_name
            FROM items i
            JOIN receipts r ON i.receipt_id = r.id
            WHERE i.name LIKE ?
            ORDER BY r.upload_date DESC
        ''', (f'%{query}%',))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'name': row[0],
                'category': row[1],
                'price': row[2],
                'date': row[3],
                'store': row[4]
            })
        
        conn.close()
        return results
    
    def _extract_store_name(self, raw_text: str) -> str:
        """Extract store name from receipt text (basic implementation)"""
        lines = raw_text.split('\n')[:5]  # Look in first 5 lines
        
        for line in lines:
            line = line.strip()
            if len(line) > 3 and not any(char.isdigit() for char in line):
                # Simple heuristic: first non-numeric line is likely store name
                return line
        
        return "Unknown Store"
    
    def delete_receipt(self, receipt_id: int) -> bool:
        """Delete a receipt and all its items"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Delete items first (due to foreign key constraint)
            cursor.execute('DELETE FROM items WHERE receipt_id = ?', (receipt_id,))
            
            # Delete receipt
            cursor.execute('DELETE FROM receipts WHERE id = ?', (receipt_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting receipt: {e}")
            conn.rollback()
            conn.close()
            return False