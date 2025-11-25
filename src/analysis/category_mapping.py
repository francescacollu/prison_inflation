"""
Category mapping from commissary categories to CPI categories.
"""

# Mapping from commissary category to CPI category
COMMISSARY_TO_CPI_MAPPING = {
    # Food categories -> "Food at home"
    "CANDY": "Food at home",
    "CONDIMENTS": "Food at home",
    "INSTANT FOODS": "Food at home",
    "JUICES / WATER / TEA": "Food at home",
    "KOSHER ITEMS": "Food at home",
    "OTHER FOOD ITEMS": "Food at home",
    "PACKAGED MEAT": "Food at home",
    "SNACKS": "Food at home",
    "SODAS": "Food at home",
    "BEVERAGES": "Food at home",
    "ICE CREAM": "Food at home",
    "INSTANT DRINK MIX": "Food at home",
    "INSTANT DRINK MIXES": "Food at home",
    
    # Hygiene and personal care -> "Personal care"
    "HYGIENE": "Personal care",
    "FEMALE ONLY": "Personal care",
    "MALE ONLY": "Personal care",
    
    # Clothing -> "Apparel"
    "CLOTHING": "Apparel",
    "SHOES": "Apparel",
    
    # Medications -> "Medicinal drugs"
    "OTC MEDICATIONS, VITAMINS, ETC": "Medicinal drugs",
    
    # Recreation items -> "Recreation"
    "ART SUPPLIES": "Recreation",
    "CORRESPONDENCE": "Recreation",
    "GAMES": "Recreation",
    "ELECTRICAL": "Recreation",
    
    # Religious items -> "Other goods"
    "JEWELRY / RELIGIOUS": "Other goods",
    
    # Miscellaneous -> "CPI-U" (general baseline)
    "MISCELLANEOUS": "CPI-U",
}

def get_cpi_category(commissary_category):
    """
    Get the corresponding CPI category for a commissary category.
    
    Args:
        commissary_category: The commissary category name
    
    Returns:
        The corresponding CPI category name, or "CPI-U" if not found
    """
    return COMMISSARY_TO_CPI_MAPPING.get(commissary_category, "CPI-U")

def get_all_commissary_categories():
    """Get all commissary categories in the mapping."""
    return list(COMMISSARY_TO_CPI_MAPPING.keys())

def get_cpi_categories():
    """Get all unique CPI categories."""
    return list(set(COMMISSARY_TO_CPI_MAPPING.values()))

def print_mapping_summary():
    """Print a summary of the category mapping."""
    print("Commissary to CPI Category Mapping:")
    print("=" * 60)
    
    # Group by CPI category
    cpi_to_commissary = {}
    for comm_cat, cpi_cat in COMMISSARY_TO_CPI_MAPPING.items():
        if cpi_cat not in cpi_to_commissary:
            cpi_to_commissary[cpi_cat] = []
        cpi_to_commissary[cpi_cat].append(comm_cat)
    
    for cpi_cat in sorted(cpi_to_commissary.keys()):
        print(f"\n{cpi_cat}:")
        for comm_cat in sorted(cpi_to_commissary[cpi_cat]):
            print(f"  - {comm_cat}")

if __name__ == "__main__":
    print_mapping_summary()

