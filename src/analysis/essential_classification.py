"""
Essential vs Non-Essential Item Classification

This module classifies commissary items as "essential" or "non-essential" based on
whether they are basic necessities that people cannot avoid purchasing, versus
discretionary/luxury items.

Classification is done at the item level, considering both category context and
item name patterns.
"""

# Categories that are generally essential
ESSENTIAL_CATEGORIES = {
    "HYGIENE",
    "MALE ONLY",  # Basic hygiene items
    "FEMALE ONLY",  # Some items are essential (pads, basic hygiene), some are not (makeup)
    "CLOTHING",  # Basic clothing items
    "SHOES",  # Basic footwear
    "OTC MEDICATIONS, VITAMINS, ETC",  # Health items
    "INSTANT FOODS",  # Basic food
    "PACKAGED MEAT",  # Basic food
    "CONDIMENTS",  # Basic food items
    "KOSHER ITEMS",  # Basic food (dietary requirement)
    "JUICES / WATER / TEA",  # Basic beverages
    "INSTANT DRINK MIX",  # Basic beverages (coffee, etc.)
    "INSTANT DRINK MIXES",  # Basic beverages
}

# Categories that are generally non-essential
NON_ESSENTIAL_CATEGORIES = {
    "CANDY",
    "SNACKS",
    "ART SUPPLIES",
    "GAMES",
    "ELECTRICAL",  # Entertainment items
    "ICE CREAM",
    "SODAS",  # Non-essential beverages
    "JEWELRY / RELIGIOUS",  # Religious items are important but not essential for survival
}

# Item name patterns that indicate essential items
ESSENTIAL_PATTERNS = [
    # Basic hygiene
    "soap", "toothpaste", "tooth brush", "shampoo", "deodorant", "antiperspirant",
    "toilet tissue", "toilet paper", "tissue", "razor", "shave",
    "pads", "pantiliners", "maxi", "tampon",  # Feminine hygiene
    "hygiene pack", "hygiene kit",
    
    # Basic clothing
    "socks", "underwear", "briefs", "boxer", "t-shirt", "tshirt", "shirt",
    "pants", "shorts", "bra", "sports bra",  # Basic undergarments
    
    # Basic food
    "ramen", "noodles", "rice", "beans", "chicken", "tuna", "salmon", "mackerel",
    "cereal", "pasta", "potato", "instant", "coffee", "tea",
    
    # Basic communication
    "stamp", "envelope", "pen", "pencil", "paper", "writing tablet",
    
    # Basic medications
    "aspirin", "ibuprofen", "antacid", "vitamin", "medication",
    
    # Basic beverages
    "water", "juice", "milk",
]

# Item name patterns that indicate non-essential items
NON_ESSENTIAL_PATTERNS = [
    # Candy and snacks
    "candy", "jawbreaker", "jolly rancher", "tootsie", "twix",
    "chips", "tortilla", "pork skins", "almonds", "sunflower",
    
    # Art and entertainment
    "coloring book", "colored pencil", "watercolor", "paint", "drawing pad",
    "chess", "game", "radio", "headphone", "earbud", "fan", "clock",
    "typewriter", "ribbon", "printwheel",
    
    # Luxury personal care
    "lipstick", "mascara", "eyeliner", "foundation", "makeup", "nail polish",
    "hair perm", "hair dryer", "hair gel", "cologne", "perfume",
    "fancy", "luxury",
    
    # Non-essential items
    "greeting card", "dictionary", "storage box", "medallion", "rune",
    "prayer oil", "soda", "pop", "ice cream",
]

# Items in FEMALE ONLY that are essential (feminine hygiene)
FEMALE_ESSENTIAL_ITEMS = [
    "pantiliners", "maxi pads", "always", "hygiene pack", "sports bra",
    "briefs", "panties",
]

# Items in FEMALE ONLY that are non-essential (cosmetics)
FEMALE_NON_ESSENTIAL_ITEMS = [
    "lipstick", "mascara", "eyeliner", "foundation", "makeup",
    "hair perm", "hair dryer", "nail", "tweezer",
]

# Items in CORRESPONDENCE that are essential (basic communication)
CORRESPONDENCE_ESSENTIAL_ITEMS = [
    "stamp", "envelope", "pen", "pencil", "paper", "writing tablet",
]

# Items in CORRESPONDENCE that are non-essential
CORRESPONDENCE_NON_ESSENTIAL_ITEMS = [
    "greeting card", "dictionary", "carbon paper", "eraser",
    "folder", "sharpener",
]


def classify_item_essential(item_name, category):
    """
    Classify an item as essential or non-essential.
    
    Args:
        item_name: Name of the item (string)
        category: Category of the item (string)
    
    Returns:
        "essential" or "non-essential"
    """
    item_name_lower = item_name.lower()
    category_upper = category.upper()
    
    # Check category-based rules first
    if category_upper in ESSENTIAL_CATEGORIES:
        # But check for exceptions in special categories
        if category_upper == "FEMALE ONLY":
            # Check if it's a cosmetic (non-essential) or hygiene item (essential)
            if any(pattern in item_name_lower for pattern in FEMALE_NON_ESSENTIAL_ITEMS):
                return "non-essential"
            if any(pattern in item_name_lower for pattern in FEMALE_ESSENTIAL_ITEMS):
                return "essential"
            # Default for FEMALE ONLY: if it's hygiene-related, essential; otherwise non-essential
            if any(pattern in item_name_lower for pattern in ["hygiene", "pad", "bra", "brief", "pantie"]):
                return "essential"
            return "non-essential"  # Default for cosmetics
        
        if category_upper == "CORRESPONDENCE":
            # Check if it's essential communication or non-essential
            if any(pattern in item_name_lower for pattern in CORRESPONDENCE_ESSENTIAL_ITEMS):
                return "essential"
            if any(pattern in item_name_lower for pattern in CORRESPONDENCE_NON_ESSENTIAL_ITEMS):
                return "non-essential"
            # Default: essential (basic communication needs)
            return "essential"
        
        # For other essential categories, check item name patterns
        if any(pattern in item_name_lower for pattern in NON_ESSENTIAL_PATTERNS):
            return "non-essential"
        return "essential"
    
    if category_upper in NON_ESSENTIAL_CATEGORIES:
        # Non-essential categories are generally non-essential
        # Only override if there's a very strong essential pattern match
        # and it's not clearly a non-essential item
        if any(pattern in item_name_lower for pattern in NON_ESSENTIAL_PATTERNS):
            return "non-essential"
        # Very few exceptions - most items in non-essential categories stay non-essential
        return "non-essential"
    
    # For ambiguous categories (MISCELLANEOUS, OTHER FOOD ITEMS, etc.)
    # Use item name patterns
    if any(pattern in item_name_lower for pattern in ESSENTIAL_PATTERNS):
        if any(pattern in item_name_lower for pattern in NON_ESSENTIAL_PATTERNS):
            # If both match, category takes precedence
            return "non-essential"
        return "essential"
    
    if any(pattern in item_name_lower for pattern in NON_ESSENTIAL_PATTERNS):
        return "non-essential"
    
    # Default for ambiguous items: classify based on category if available
    # Otherwise, default to non-essential (conservative approach)
    if category_upper in ["OTHER FOOD ITEMS"]:
        return "essential"  # Food items are generally essential
    
    return "non-essential"  # Default to non-essential for truly ambiguous items


def classify_dataframe(df, item_name_col='item_name', category_col='category'):
    """
    Classify all items in a DataFrame as essential or non-essential.
    
    Args:
        df: DataFrame with item data
        item_name_col: Name of the column containing item names
        category_col: Name of the column containing categories
    
    Returns:
        DataFrame with added 'essential_status' column
    """
    df = df.copy()
    df['essential_status'] = df.apply(
        lambda row: classify_item_essential(
            row[item_name_col],
            row[category_col]
        ),
        axis=1
    )
    return df


if __name__ == "__main__":
    # Test the classification with some examples
    test_items = [
        ("Colgate Toothpaste", "HYGIENE"),
        ("Twix Candy Bar", "CANDY"),
        ("T-Shirts", "CLOTHING"),
        ("Foundation-Asst Shades", "FEMALE ONLY"),
        ("Maxi Pads", "FEMALE ONLY"),
        ("Stamps-Assorted", "CORRESPONDENCE"),
        ("Greeting Cards-Assorted", "CORRESPONDENCE"),
        ("Ramen Noodles", "INSTANT FOODS"),
        ("Watercolor Paints", "ART SUPPLIES"),
        ("Chess Set", "GAMES"),
    ]
    
    print("Classification Test Results:")
    print("=" * 60)
    for item_name, category in test_items:
        classification = classify_item_essential(item_name, category)
        print(f"{item_name:30} [{category:20}] -> {classification}")

