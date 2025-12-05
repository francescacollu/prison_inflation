"""
Correspondence mapping from CPI categories to commissary categories.

This file defines the mapping from CPI categories to their corresponding
commissary categories. This is used to calculate inflation for each category
and compare commissary prices to CPI inflation.
"""

# Mapping from CPI category to list of commissary categories
CPI_TO_COMMISSARY_MAPPING = {
    "Apparel": [
        "CLOTHING",
        "JEWELRY / RELIGIOUS",
        "SHOES",
    ],
    "Food at home": [
        "INSTANT FOODS",
        "KOSHER ITEMS",
        "PACKAGED MEAT",
        "SNACKS",
        "ICE CREAM",
        "CONDIMENTS",
        "INSTANT DRINK MIXES",
        "BEVERAGES",
        "CANDY",
        "JUICES / WATER / TEA",
        "OTHER FOOD ITEMS",
        "SODAS",
        "INSTANT DRINK MIX",
    ],
    "Personal care": [
        "HYGIENE",
        "FEMALE ONLY",
        "MALE ONLY",
    ],
    "Medicinal drugs": [
        "OTC MEDICATIONS, VITAMINS, ETC",
    ],
    "Recreation": [
        "ART SUPPLIES",
        "CORRESPONDENCE",
        "GAMES",
        "ELECTRICAL",
    ],
}
