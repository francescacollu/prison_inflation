"""
Category mapping from commissary categories to CPI categories.

This module uses the correspondence file to map commissary categories
to CPI categories for inflation calculations and comparisons.
"""

from cpi_to_commissary_mapping import CPI_TO_COMMISSARY_MAPPING

# Build reverse mapping from commissary category to CPI category
COMMISSARY_TO_CPI_MAPPING = {}
for cpi_category, commissary_categories in CPI_TO_COMMISSARY_MAPPING.items():
    for commissary_category in commissary_categories:
        COMMISSARY_TO_CPI_MAPPING[commissary_category] = cpi_category

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

def get_commissary_categories_for_cpi(cpi_category):
    """
    Get all commissary categories that map to a given CPI category.
    
    Args:
        cpi_category: The CPI category name
    
    Returns:
        List of commissary categories that map to this CPI category
    """
    return CPI_TO_COMMISSARY_MAPPING.get(cpi_category, [])

def print_mapping_summary():
    """Print a summary of the category mapping."""
    print("Commissary to CPI Category Mapping:")
    print("=" * 60)
    
    for cpi_cat in sorted(CPI_TO_COMMISSARY_MAPPING.keys()):
        print(f"\n{cpi_cat}:")
        for comm_cat in sorted(CPI_TO_COMMISSARY_MAPPING[cpi_cat]):
            print(f"  - {comm_cat}")

if __name__ == "__main__":
    print_mapping_summary()