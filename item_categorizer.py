from typing import Dict, List
from fuzzywuzzy import fuzz, process
import re

class ItemCategorizer:
    def __init__(self):
        # Define category mappings with common grocery items
        self.category_mappings = {
            'fruits': [
                'apple', 'apples', 'banana', 'bananas', 'orange', 'oranges', 'grape', 'grapes',
                'strawberry', 'strawberries', 'blueberry', 'blueberries', 'raspberry', 'raspberries',
                'mango', 'mangoes', 'pineapple', 'watermelon', 'cantaloupe', 'honeydew',
                'peach', 'peaches', 'pear', 'pears', 'plum', 'plums', 'cherry', 'cherries',
                'lemon', 'lemons', 'lime', 'limes', 'avocado', 'avocados', 'kiwi', 'papaya',
                'coconut', 'pomegranate', 'cranberry', 'cranberries', 'blackberry', 'blackberries'
            ],
            'vegetables': [
                'carrot', 'carrots', 'broccoli', 'cauliflower', 'spinach', 'lettuce', 'tomato', 'tomatoes',
                'cucumber', 'cucumber', 'bell pepper', 'peppers', 'onion', 'onions', 'garlic',
                'potato', 'potatoes', 'sweet potato', 'celery', 'zucchini', 'squash',
                'corn', 'peas', 'green beans', 'beans', 'asparagus', 'mushroom', 'mushrooms',
                'cabbage', 'kale', 'brussels sprouts', 'radish', 'beet', 'beets', 'turnip',
                'parsnip', 'leek', 'artichoke', 'eggplant', 'okra', 'jalapeno', 'serrano'
            ],
            'meat': [
                'chicken', 'beef', 'pork', 'turkey', 'lamb', 'fish', 'salmon', 'tuna', 'cod',
                'tilapia', 'shrimp', 'crab', 'lobster', 'bacon', 'ham', 'sausage', 'ground beef',
                'ground turkey', 'ground chicken', 'steak', 'roast', 'ribs', 'wings', 'thighs',
                'breast', 'drumstick', 'meatball', 'hot dog', 'deli meat', 'pepperoni', 'salami'
            ],
            'dairy': [
                'milk', 'cheese', 'butter', 'yogurt', 'cream', 'sour cream', 'cottage cheese',
                'mozzarella', 'cheddar', 'swiss', 'parmesan', 'feta', 'ricotta', 'cream cheese',
                'half and half', 'heavy cream', 'whipped cream', 'ice cream', 'frozen yogurt',
                'eggs', 'egg whites', 'egg substitute'
            ],
            'grains': [
                'bread', 'rice', 'pasta', 'cereal', 'oats', 'quinoa', 'barley', 'wheat', 'flour',
                'bagel', 'bagels', 'muffin', 'muffins', 'crackers', 'tortilla', 'tortillas',
                'noodles', 'spaghetti', 'macaroni', 'penne', 'linguine', 'rolls', 'baguette',
                'croissant', 'pancake mix', 'waffle', 'granola', 'oatmeal'
            ],
            'beverages': [
                'water', 'juice', 'soda', 'coffee', 'tea', 'beer', 'wine', 'energy drink',
                'sports drink', 'coconut water', 'almond milk', 'soy milk', 'oat milk',
                'sparkling water', 'lemonade', 'iced tea', 'kombucha', 'smoothie'
            ],
            'snacks': [
                'chips', 'popcorn', 'pretzels', 'nuts', 'peanuts', 'almonds', 'cashews', 'walnuts',
                'trail mix', 'granola bar', 'protein bar', 'candy', 'chocolate', 'cookies',
                'crackers', 'jerky', 'dried fruit', 'raisins', 'dates', 'gum', 'mints'
            ],
            'frozen': [
                'frozen pizza', 'frozen vegetables', 'frozen fruit', 'ice cream', 'frozen yogurt',
                'frozen meal', 'frozen dinner', 'frozen burrito', 'frozen chicken', 'frozen fish',
                'frozen shrimp', 'frozen berries', 'frozen peas', 'frozen corn', 'popsicle',
                'frozen waffle', 'frozen pancake', 'frozen bread'
            ],
            'pantry': [
                'oil', 'olive oil', 'vinegar', 'salt', 'pepper', 'sugar', 'honey', 'syrup',
                'vanilla', 'baking powder', 'baking soda', 'spices', 'herbs', 'garlic powder',
                'onion powder', 'paprika', 'cumin', 'oregano', 'basil', 'thyme', 'rosemary',
                'cinnamon', 'nutmeg', 'ginger', 'turmeric', 'curry powder', 'chili powder',
                'hot sauce', 'ketchup', 'mustard', 'mayo', 'mayonnaise', 'relish', 'pickles',
                'jam', 'jelly', 'peanut butter', 'almond butter', 'tahini', 'coconut oil'
            ],
            'canned_goods': [
                'canned tomatoes', 'tomato sauce', 'tomato paste', 'canned corn', 'canned beans',
                'black beans', 'kidney beans', 'chickpeas', 'lentils', 'canned tuna', 'canned salmon',
                'chicken broth', 'beef broth', 'vegetable broth', 'coconut milk', 'canned pumpkin',
                'canned peaches', 'canned pears', 'pasta sauce', 'salsa', 'soup', 'canned soup'
            ],
            'personal_care': [
                'shampoo', 'conditioner', 'soap', 'body wash', 'toothpaste', 'toothbrush',
                'deodorant', 'lotion', 'sunscreen', 'razor', 'shaving cream', 'tissue', 'tissues',
                'toilet paper', 'paper towels', 'cotton swabs', 'band aid', 'medicine', 'vitamins'
            ],
            'household': [
                'detergent', 'fabric softener', 'dish soap', 'sponge', 'paper plates', 'plastic bags',
                'aluminum foil', 'plastic wrap', 'parchment paper', 'cleaning supplies', 'bleach',
                'disinfectant', 'trash bags', 'light bulb', 'batteries', 'laundry pods'
            ],
            'bakery': [
                'cake', 'pie', 'donut', 'donuts', 'danish', 'pastry', 'cupcake', 'brownie',
                'cookie', 'bread loaf', 'dinner rolls', 'bagels', 'croissant', 'muffin'
            ]
        }
        
        # Create reverse mapping for faster lookup
        self.item_to_category = {}
        for category, items in self.category_mappings.items():
            for item in items:
                self.item_to_category[item.lower()] = category
        
        # Common words that might indicate specific categories
        self.category_keywords = {
            'organic': 'vegetables',  # Default organic items to vegetables unless found elsewhere
            'fresh': 'produce',
            'frozen': 'frozen',
            'canned': 'canned_goods',
            'whole': 'grains',
            'ground': 'meat'
        }

    def categorize_item(self, item_name: str) -> str:
        """Categorize a grocery item into a category"""
        if not item_name:
            return 'other'
        
        item_lower = item_name.lower().strip()
        
        # Direct lookup first
        if item_lower in self.item_to_category:
            return self.item_to_category[item_lower]
        
        # Check for partial matches within the item name
        best_category = self._find_best_category_match(item_lower)
        if best_category:
            return best_category
        
        # Check for category keywords
        for keyword, category in self.category_keywords.items():
            if keyword in item_lower:
                return category
        
        # Fuzzy matching as last resort
        fuzzy_category = self._fuzzy_match_category(item_lower)
        if fuzzy_category:
            return fuzzy_category
        
        return 'other'

    def _find_best_category_match(self, item_name: str) -> str:
        """Find the best category match using substring matching"""
        best_category = None
        best_score = 0
        
        for category, items in self.category_mappings.items():
            for category_item in items:
                # Check if category item is contained in the input item name
                if category_item in item_name:
                    score = len(category_item)  # Longer matches are better
                    if score > best_score:
                        best_score = score
                        best_category = category
                
                # Check if input item name is contained in category item
                if item_name in category_item:
                    score = len(item_name)
                    if score > best_score:
                        best_score = score
                        best_category = category
        
        return best_category

    def _fuzzy_match_category(self, item_name: str) -> str:
        """Use fuzzy matching to find the best category"""
        best_category = None
        best_score = 0
        threshold = 80  # Minimum similarity threshold
        
        for category, items in self.category_mappings.items():
            for category_item in items:
                # Calculate similarity
                score = fuzz.ratio(item_name, category_item)
                if score > best_score and score >= threshold:
                    best_score = score
                    best_category = category
        
        return best_category

    def get_all_categories(self) -> List[str]:
        """Get all available categories"""
        return list(self.category_mappings.keys()) + ['other']

    def add_custom_mapping(self, item_name: str, category: str):
        """Add a custom item-to-category mapping"""
        item_lower = item_name.lower().strip()
        if category in self.category_mappings:
            self.item_to_category[item_lower] = category
            if item_lower not in self.category_mappings[category]:
                self.category_mappings[category].append(item_lower)

    def get_category_stats(self, items: List[Dict]) -> Dict:
        """Get statistics about categorized items"""
        category_counts = {}
        category_totals = {}
        
        for item in items:
            category = item.get('category', 'other')
            price = item.get('price', 0)
            
            category_counts[category] = category_counts.get(category, 0) + 1
            category_totals[category] = category_totals.get(category, 0) + price
        
        return {
            'counts': category_counts,
            'totals': category_totals
        }

    def suggest_category_for_unknown_item(self, item_name: str, threshold: int = 70) -> List[tuple]:
        """Suggest possible categories for an unknown item"""
        suggestions = []
        item_lower = item_name.lower().strip()
        
        for category, items in self.category_mappings.items():
            for category_item in items:
                score = fuzz.ratio(item_lower, category_item)
                if score >= threshold:
                    suggestions.append((category, category_item, score))
        
        # Sort by score (highest first)
        suggestions.sort(key=lambda x: x[2], reverse=True)
        return suggestions[:5]  # Return top 5 suggestions