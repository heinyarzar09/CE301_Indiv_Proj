from app.models import Tool
from fractions import Fraction

def convert_measurement(amount, from_unit, to_unit, capacity=None):
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

    if from_unit == to_unit:
        return amount
    
    if from_unit in conversions and to_unit in conversions[from_unit]:
        return amount * conversions[from_unit][to_unit]
    
    # For conversions that require multiple steps
    for intermediate_unit in conversions[from_unit]:
        if intermediate_unit in conversions and to_unit in conversions[intermediate_unit]:
            return amount * conversions[from_unit][intermediate_unit] * conversions[intermediate_unit][to_unit]
    
    raise ValueError(f"Conversion from {from_unit} to {to_unit} not supported.")

def process_recipe(recipe_text, to_unit, user_id):
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
    
    user_tools = Tool.query.filter_by(user_id=user_id).all()
    tool_units = {tool.name: tool.unit for tool in user_tools}
    tool_capacities = {tool.name: tool.capacity for tool in user_tools}

    def convert_amount(amount, unit, target_tool):
        normalized_unit = normalize_unit(unit)
        if target_tool in tool_units and normalized_unit in conversions:
            target_unit = tool_units[target_tool]
            if target_unit in conversions[normalized_unit]:
                converted_amount = amount * conversions[normalized_unit][target_unit] / tool_capacities[target_tool]
                return f"{converted_amount} {target_tool} ({tool_capacities[target_tool]} {target_unit})"
        raise ValueError(f"Conversion from {unit} to {target_tool} not supported.")

    words = recipe_text.split()
    result = []
    quantity = 0
    unit = ''
    for word in words:
        try:
            quantity = float(Fraction(word))
        except ValueError:
            if word in tool_units.values():
                unit = word
                try:
                    converted_result = convert_amount(quantity, unit, to_unit)
                    result.append(converted_result)
                except ValueError:
                    result.append(f"{quantity} {unit}")
            else:
                result.append(word)
    return ' '.join(result) if result else None

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

def normalize_unit(unit):
    return UNIT_MAPPING.get(unit.lower(), unit)
