import re
from typing import List, Dict, Optional
import numpy as np

class ReceiptParser:
    def __init__(self):
        # Common patterns for prices
        self.price_patterns = [
            r'\$?(\d+\.\d{2})',  # Standard price format $12.34 or 12.34
            r'(\d+,\d{2})',      # European format 12,34
            r'(\d+\.\d{1})',     # Price with one decimal 12.3
        ]
        
        # Common quantity patterns
        self.quantity_patterns = [
            r'(\d+)\s*x\s*',     # 2x, 3 x
            r'(\d+)\s*@\s*',     # 2@, 3 @
            r'qty\s*(\d+)',      # qty 2, qty:2
            r'(\d+)\s*pc',       # 2pc, 3 pc
            r'(\d+)\s*pcs',      # 2pcs, 3 pcs
        ]
        
        # Words to ignore when parsing item names
        self.ignore_words = {
            'total', 'subtotal', 'tax', 'change', 'cash', 'credit', 'debit',
            'visa', 'mastercard', 'amex', 'discover', 'receipt', 'thank you',
            'thanks', 'store', 'location', 'date', 'time', 'cashier', 'clerk',
            'balance', 'tender', 'due', 'paid', 'amount'
        }
        
        # Common store section headers to ignore
        self.section_headers = {
            'grocery', 'produce', 'dairy', 'meat', 'bakery', 'frozen',
            'beverages', 'health', 'beauty', 'household', 'pharmacy'
        }

    def parse_receipt(self, text: str) -> List[Dict]:
        """Parse receipt text and extract items with quantities and prices"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        items = []
        
        for i, line in enumerate(lines):
            # Skip empty lines and common headers
            if not line or self._should_ignore_line(line):
                continue
            
            # Try to extract item information from this line
            item = self._parse_line(line)
            if item:
                items.append(item)
        
        # Post-process to clean up and validate items
        return self._clean_and_validate_items(items)

    def _should_ignore_line(self, line: str) -> bool:
        """Check if a line should be ignored"""
        line_lower = line.lower()
        
        # Ignore lines that are just numbers, dates, or times
        if re.match(r'^\d+$', line) or re.match(r'^\d{1,2}[:/]\d{1,2}', line):
            return True
        
        # Ignore lines with only special characters
        if re.match(r'^[^a-zA-Z0-9]*$', line):
            return True
        
        # Ignore common receipt headers/footers
        for word in self.ignore_words:
            if word in line_lower:
                return True
        
        # Ignore section headers
        for header in self.section_headers:
            if line_lower == header:
                return True
        
        return False

    def _parse_line(self, line: str) -> Optional[Dict]:
        """Parse a single line to extract item information"""
        # Look for price in the line
        price_match = self._find_price(line)
        if not price_match:
            return None
        
        price = float(price_match.group(1).replace(',', '.'))
        
        # Remove the price from the line to get the item name
        line_without_price = line[:price_match.start()] + line[price_match.end():]
        
        # Look for quantity
        quantity = 1
        quantity_match = self._find_quantity(line_without_price)
        if quantity_match:
            quantity = int(quantity_match.group(1))
            # Remove quantity from line
            line_without_price = line_without_price[:quantity_match.start()] + line_without_price[quantity_match.end():]
        
        # Clean up the item name
        item_name = self._clean_item_name(line_without_price)
        
        if not item_name or len(item_name) < 2:
            return None
        
        return {
            'name': item_name,
            'quantity': quantity,
            'price': price,
            'unit_price': round(price / quantity, 2) if quantity > 0 else price,
            'raw_line': line
        }

    def _find_price(self, line: str):
        """Find price pattern in line"""
        for pattern in self.price_patterns:
            match = re.search(pattern, line)
            if match:
                # Validate that this looks like a reasonable price
                try:
                    price_val = float(match.group(1).replace(',', '.'))
                    if 0.01 <= price_val <= 999.99:  # Reasonable price range
                        return match
                except ValueError:
                    continue
        return None

    def _find_quantity(self, line: str):
        """Find quantity pattern in line"""
        for pattern in self.quantity_patterns:
            match = re.search(pattern, line.lower())
            if match:
                try:
                    qty = int(match.group(1))
                    if 1 <= qty <= 99:  # Reasonable quantity range
                        return match
                except ValueError:
                    continue
        return None

    def _clean_item_name(self, name: str) -> str:
        """Clean and normalize item name"""
        # Remove extra whitespace and special characters
        name = re.sub(r'\s+', ' ', name.strip())
        name = re.sub(r'[^\w\s\-&]', '', name)
        
        # Remove common prefixes/suffixes
        name = re.sub(r'^(item|product)\s*:?\s*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s*(each|ea|pc|pcs)$', '', name, flags=re.IGNORECASE)
        
        # Title case for better readability
        name = name.title()
        
        return name.strip()

    def _clean_and_validate_items(self, items: List[Dict]) -> List[Dict]:
        """Clean up and validate the extracted items"""
        valid_items = []
        
        for item in items:
            # Skip items with unreasonable values
            if item['price'] <= 0 or item['price'] > 999.99:
                continue
            
            if item['quantity'] <= 0 or item['quantity'] > 99:
                continue
            
            if len(item['name']) < 2:
                continue
            
            # Skip items that look like totals or taxes
            name_lower = item['name'].lower()
            if any(word in name_lower for word in ['total', 'tax', 'subtotal', 'balance']):
                continue
            
            valid_items.append(item)
        
        return valid_items

    def extract_store_info(self, text: str) -> Dict:
        """Extract store information from receipt text"""
        lines = text.split('\n')
        store_info = {'name': '', 'address': '', 'phone': '', 'date': ''}
        
        # Try to find store name (usually in first few lines)
        for i, line in enumerate(lines[:5]):
            line = line.strip()
            if len(line) > 3 and not re.match(r'^\d', line):
                if not store_info['name']:
                    store_info['name'] = line
                elif not store_info['address'] and 'store' not in line.lower():
                    store_info['address'] = line
        
        # Look for phone number
        phone_pattern = r'(\(?[\d\-\.\s]{10,}\)?)'
        for line in lines:
            phone_match = re.search(phone_pattern, line)
            if phone_match:
                store_info['phone'] = phone_match.group(1)
                break
        
        # Look for date
        date_patterns = [
            r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})',
            r'(\d{2,4}[\/\-]\d{1,2}[\/\-]\d{1,2})',
        ]
        
        for line in lines:
            for pattern in date_patterns:
                date_match = re.search(pattern, line)
                if date_match:
                    store_info['date'] = date_match.group(1)
                    break
            if store_info['date']:
                break
        
        return store_info