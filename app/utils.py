# Import necessary modules
import re  # Regular expressions for parsing text
from fractions import Fraction  # Handling fractional values
from app.models import User, Friendship

# Mapping of units to their standardized abbreviations
UNIT_MAPPING = {
    'teaspoon': 'tsp',
    'teaspoons': 'tsp',
    'tbsp': 'tbsp',
    'tablespoon': 'tbsp',
    'tablespoons': 'tbsp',
    'cup': 'cup',
    'cups': 'cup',
    'fluid ounce': 'fl oz',
    'fluid ounces': 'fl oz',
    'fl oz': 'fl oz',
    'pint': 'pt',
    'pints': 'pt',
    'quart': 'qt',
    'quarts': 'qt',
    'gallon': 'gal',
    'gallons': 'gal',
    'ounce': 'oz',
    'ounces': 'oz',
    'lb': 'lb',
    'pound': 'lb',
    'pounds': 'lb',
    'milliliter': 'ml',
    'milliliters': 'ml',
    'ml': 'ml',
    'gram': 'g',
    'grams': 'g',
    'g': 'g'
}

# Function to normalize the unit by converting it to its standard abbreviation
def normalize_unit(unit):
    return UNIT_MAPPING.get(unit.lower(), unit)

# Function to convert a given measurement from one unit to another
def convert_measurement(amount, from_unit, to_unit):
    # Conversion rates between different units
    conversions = {
        'tsp': {'tbsp': 1/3, 'cup': 1/48, 'fl oz': 1/6, 'ml': 5},
        'tbsp': {'tsp': 3, 'cup': 1/16, 'fl oz': 1/2, 'ml': 15},
        'cup': {'tsp': 48, 'tbsp': 16, 'fl oz': 8, 'pt': 1/2, 'qt': 1/4, 'gal': 1/16, 'ml': 240},
        'fl oz': {'tsp': 6, 'tbsp': 2, 'cup': 1/8, 'pt': 1/16, 'qt': 1/32, 'gal': 1/128, 'ml': 30},
        'pt': {'cup': 2, 'fl oz': 16, 'qt': 1/2, 'gal': 1/8, 'ml': 480},
        'qt': {'cup': 4, 'fl oz': 32, 'pt': 2, 'gal': 1/4, 'ml': 960},
        'gal': {'cup': 16, 'fl oz': 128, 'pt': 8, 'qt': 4, 'ml': 3840},
        'oz': {'lb': 1/16, 'g': 28.35},
        'lb': {'oz': 16, 'g': 453.59},
        'ml': {'tsp': 1/5, 'tbsp': 1/15, 'cup': 1/240, 'fl oz': 1/30, 'pt': 1/480, 'qt': 1/960, 'gal': 1/3840, 'g': 1},
        'g': {'oz': 1/28.35, 'lb': 1/453.59, 'ml': 1},
    }

    # If the from and to units are the same, no conversion is needed
    if from_unit == to_unit:
        return amount

    # If a direct conversion exists, use it to calculate the result
    if from_unit in conversions and to_unit in conversions[from_unit]:
        return amount * conversions[from_unit][to_unit]

    # Handle cases where a multi-step conversion is needed (e.g., via an intermediate unit)
    for intermediate_unit in conversions[from_unit]:
        if intermediate_unit in conversions and to_unit in conversions[intermediate_unit]:
            return amount * conversions[from_unit][intermediate_unit] * conversions[intermediate_unit][to_unit]

    # If no valid conversion is found, raise an error
    raise ValueError(f"Conversion from {from_unit} to {to_unit} not supported.")

# Function to process a recipe and convert units to a desired unit
def process_recipe(recipe_text, to_unit, user_id):
    # Split the recipe text into words for easy parsing
    words = recipe_text.split()
    result = []  # List to store the final processed recipe text
    quantity = 0  # Variable to keep track of the current quantity
    unit = ''  # Variable to store the unit of the quantity

    # Iterate through each word in the recipe text
    for word in words:
        if re.match(r'^\d+/\d+$', word):  # If the word is a fraction (e.g., 1/2)
            quantity = float(Fraction(word))  # Convert it to a float using the Fraction class
        elif word.isdigit():  # If the word is a whole number
            quantity = float(word)  # Convert it to a float
        elif word in UNIT_MAPPING:  # If the word is a recognized unit
            unit = normalize_unit(word)  # Normalize the unit to its abbreviation
            try:
                # Attempt to convert the quantity to the desired unit
                converted_quantity = convert_measurement(quantity, unit, to_unit)
                # Append the converted quantity and unit to the result list
                result.append(f"{converted_quantity} {to_unit}")
            except ValueError:
                # If the conversion is not supported, append the original quantity and unit
                result.append(f"{quantity} {unit}")
        else:
            # If the word is not a quantity or unit, append it as is
            result.append(word)

    # Join the words in the result list into a final string and return it
    return ' '.join(result)


# Helper function to fetch all users except the current user
def get_all_users_except_current(current_user):
    return User.query.filter(User.id != current_user.id).all()

# Helper function to get a user's friends
def get_friends_for_user(user):
    return User.query.join(Friendship, Friendship.friend_id == User.id)\
                     .filter(Friendship.user_id == user.id, Friendship.status == 'accepted').all()

# Helper function to get pending friend requests (incoming)
def get_incoming_friend_requests(user):
    return Friendship.query.filter_by(friend_id=user.id, status='pending').all()

# Helper function to get outgoing friend requests (sent by the current user)
def get_outgoing_friend_requests(user):
    return Friendship.query.filter_by(user_id=user.id, status='pending').all()

# Helper function to get recent follows (accepted friendships)
def get_recent_follows(user, limit=10):
    return Friendship.query.filter_by(user_id=user.id, status='accepted')\
                           .order_by(Friendship.date_created.desc())\
                           .limit(limit).all()
