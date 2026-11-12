
import math
import re
import pandas as pd
import streamlit as st
from database import get_all_properties

# =====================================================
# 1. PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="PROPSCOUT | Property Finder",
    page_icon="🏡",
    layout="wide"
)

# =====================================================
# 2. WEBSITE DESIGN
# =====================================================

st.markdown("""
<style>
.stApp {
    background-color: #f3f6fb;
    color: #26364b;
}

.block-container {
    max-width: 1250px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

.hero {
    background: linear-gradient(120deg, #142b49, #286779);
    padding: 30px;
    border-radius: 18px;
    margin-bottom: 24px;
}

.hero h1 {
    color: white !important;
    font-size: 42px;
    margin-bottom: 8px;
}

.hero p {
    color: #f0f7ff !important;
    font-size: 16px;
}

h2, h3 {
    color: #173554 !important;
}

.property-title {
    color: #17385b !important;
    font-size: 21px;
    font-weight: 750;
    line-height: 1.5;
    overflow-wrap: anywhere;
}

.property-price {
    color: #087653 !important;
    font-size: 27px;
    font-weight: 800;
    margin: 10px 0;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #ffffff !important;
    border: 1px solid #dbe3ed !important;
    border-radius: 14px !important;
    padding: 12px !important;
    margin-bottom: 12px;
}

div[data-testid="stVerticalBlockBorderWrapper"] p {
    color: #26364b !important;
}

section[data-testid="stSidebar"] {
    background-color: #172b46;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span {
    color: white !important;
}

.stTextInput input {
    background-color: white !important;
    color: #172b46 !important;
}

div[data-baseweb="select"] > div {
    background-color: white !important;
}

div[data-baseweb="select"] * {
    color: #172b46 !important;
}

div[data-testid="stExpander"] {
    background-color: #f8fafc !important;
    border: 1px solid #d8e1eb !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# 3. NUMERIC CONVERSION
# =====================================================

def to_number(value):
    """
    Convert dataset values such as:
    6500000, '6,500,000', '650 sqft'
    into usable numeric values.
    """

    if pd.isna(value):
        return float("nan")

    if isinstance(value, (int, float)):
        number = float(value)
        return number if math.isfinite(number) else float("nan")

    text = str(value).strip().lower()

    if not text or text in {"nan", "none", "-", "n/a", "na"}:
        return float("nan")

    text = text.replace(",", "").replace("₹", "").strip()

    multiplier = 1

    if "crore" in text or re.search(r"\bcr\b", text):
        multiplier = 10000000
    elif "lakh" in text or re.search(r"\blac\b", text):
        multiplier = 100000
    elif re.search(r"\bthousand\b", text):
        multiplier = 1000

    match = re.search(r"-?\d+(?:\.\d+)?", text)

    if not match:
        return float("nan")

    return float(match.group()) * multiplier


def format_price(value):
    number = to_number(value)

    if pd.isna(number):
        return "Price not available"

    if number >= 10000000:
        return f"₹{number / 10000000:.2f} Cr"

    if number >= 100000:
        return f"₹{number / 100000:.2f} Lakh"

    return f"₹{number:,.0f}"


def show_value(value):
    if pd.isna(value):
        return "Not specified"

    if isinstance(value, float) and value.is_integer():
        return f"{int(value):,}"

    return str(value).strip()


# =====================================================
# 4. LOAD THE REAL DATA FROM DATABASE.PY
# =====================================================

try:
    df = get_all_properties()

    if df is None or df.empty:
        st.error("No properties found. Please import the CSV using database.py.")
        st.stop()

except Exception as error:
    st.error(f"Could not load property data: {error}")
    st.stop()

df = df.copy()
df.columns = df.columns.astype(str).str.strip()
df = df.dropna(how="all").reset_index(drop=True)

# Use the actual column names from your Kaggle dataset.
# Price (in rupees) is the primary price field.
# Amount (in rupees) is used only if Price is unavailable.

price_col = (
    "Price (in rupees)"
    if "Price (in rupees)" in df.columns
    else (
        "Amount (in rupees)"
        if "Amount (in rupees)" in df.columns
        else None
    )
)

location_col = "location" if "location" in df.columns else None
title_col = "Title" if "Title" in df.columns else None
description_col = "Description" if "Description" in df.columns else None
transaction_col = "Transaction" if "Transaction" in df.columns else None
status_col = "Status" if "Status" in df.columns else None
furnishing_col = "Furnishing" if "Furnishing" in df.columns else None
bathroom_col = "Bathroom" if "Bathroom" in df.columns else None
balcony_col = "Balcony" if "Balcony" in df.columns else None
parking_col = "Car Parking" if "Car Parking" in df.columns else None
floor_col = "Floor" if "Floor" in df.columns else None
society_col = "Society" if "Society" in df.columns else None
ownership_col = "Ownership" if "Ownership" in df.columns else None
facing_col = "facing" if "facing" in df.columns else None
overlooking_col = "overlooking" if "overlooking" in df.columns else None

area_candidates = [
    "Carpet Area",
    "Super Area",
    "Plot Area"
]

area_cols = [
    col for col in area_candidates
    if col in df.columns
]

# Convert price and area columns ONCE.
# Filters and sorting use these numeric helper columns.

if price_col:
    df["_numeric_price"] = df[price_col].apply(to_number)
else:
    df["_numeric_price"] = float("nan")

for col in area_cols:
    df[f"_numeric_area_{col}"] = df[col].apply(to_number)

original_columns = list(df.columns)
search_columns = [
    col for col in original_columns
    if not col.startswith("_numeric_")
]


# =====================================================
# 5. HEADER
# =====================================================

st.markdown("""
<div class="hero">
    <h1>🏡 PROPSCOUT</h1>
    <p>Find a home that fits your needs.</p>
    <p>Search real property listings and refine results using filters.</p>
</div>
""", unsafe_allow_html=True)


# =====================================================
# 6. SEARCH BAR
# =====================================================

search_text = st.text_input(
    "🔎 Search properties",
    placeholder="Search by title, location, society or description..."
)


# =====================================================
# 7. SIDEBAR FILTER CONTROLS
#    Options are based on the COMPLETE dataset.
# =====================================================

st.sidebar.title("Find Your Property")
st.sidebar.write("Select your preferences.")

# Location
if location_col:
    location_options = sorted(
        df[location_col].dropna().astype(str).unique().tolist()
    )

    selected_location = st.sidebar.selectbox(
        "Location",
        ["All locations"] + location_options,
        key="location_filter"
    )
else:
    selected_location = "All locations"

# Transaction / purpose
if transaction_col:
    transaction_options = sorted(
        df[transaction_col].dropna().astype(str).unique().tolist()
    )

    selected_transaction = st.sidebar.selectbox(
        "Transaction / Purpose",
        ["All"] + transaction_options,
        key="transaction_filter"
    )
else:
    selected_transaction = "All"

# Furnishing
if furnishing_col:
    furnishing_options = sorted(
        df[furnishing_col].dropna().astype(str).unique().tolist()
    )

    selected_furnishing = st.sidebar.selectbox(
        "Furnishing",
        ["All"] + furnishing_options,
        key="furnishing_filter"
    )
else:
    selected_furnishing = "All"

# Status
if status_col:
    status_options = sorted(
        df[status_col].dropna().astype(str).unique().tolist()
    )

    selected_status = st.sidebar.selectbox(
        "Property Status",
        ["All"] + status_options,
        key="status_filter"
    )
else:
    selected_status = "All"


# Categorical filters: preserve the original dataset values.
categorical_filters = [
    (bathroom_col, "Bathrooms", "bathroom_filter"),
    (balcony_col, "Balconies", "balcony_filter"),
    (parking_col, "Car Parking", "parking_filter"),
    (ownership_col, "Ownership", "ownership_filter"),
    (facing_col, "Facing", "facing_filter"),
    (overlooking_col, "Overlooking", "overlooking_filter")
]

selected_categories = {}

for col, label, key in categorical_filters:
    if col:
        options = sorted(
            df[col].dropna().astype(str).unique().tolist()
        )

        selected_categories[col] = st.sidebar.selectbox(
            label,
            ["All"] + options,
            key=key
        )

# Price limits
if price_col:
    all_prices = df["_numeric_price"].dropna()

    if not all_prices.empty:
        minimum_price = float(all_prices.min())
        maximum_price = float(all_prices.max())

        if minimum_price < maximum_price:
            price_limits = st.sidebar.slider(
                "Budget (₹)",
                min_value=minimum_price,
                max_value=maximum_price,
                value=(minimum_price, maximum_price),
                format="%.0f",
                key="budget_filter"
            )
        else:
            price_limits = (minimum_price, maximum_price)
    else:
        price_limits = None
else:
    price_limits = None

# Area filter
area_col = area_cols[0] if area_cols else None

if area_col:
    numeric_area_col = f"_numeric_area_{area_col}"
    all_areas = df[numeric_area_col].dropna()

    if not all_areas.empty and all_areas.min() < all_areas.max():
        area_limits = st.sidebar.slider(
            f"{area_col} range",
            min_value=float(all_areas.min()),
            max_value=float(all_areas.max()),
            value=(float(all_areas.min()), float(all_areas.max())),
            key="area_filter"
        )
    else:
        area_limits = None
else:
    area_limits = None

# Sorting
sort_options = [
    "Default order",
    "Price: Low to High",
    "Price: High to Low"
]

sort_by = st.selectbox(
    "Sort results",
    sort_options,
    key="sort_filter"
)


# =====================================================
# 8. APPLY ALL FILTERS TO THE SAME DATAFRAME
# =====================================================

results = df.copy()

# Search title, description, location and every other
# original column. This is a literal, case-insensitive search.

if search_text.strip():
    search_mask = results[search_columns].astype(str).apply(
        lambda col: col.str.contains(
            search_text.strip(),
            case=False,
            na=False,
            regex=False
        )
    ).any(axis=1)

    results = results.loc[search_mask]

# Location filter
if selected_location != "All locations" and location_col:
    results = results[
        results[location_col].astype(str) == selected_location
    ]

# Transaction filter
if selected_transaction != "All" and transaction_col:
    results = results[
        results[transaction_col].astype(str) == selected_transaction
    ]

# Furnishing filter
if selected_furnishing != "All" and furnishing_col:
    results = results[
        results[furnishing_col].astype(str) == selected_furnishing
    ]

# Status filter
if selected_status != "All" and status_col:
    results = results[
        results[status_col].astype(str) == selected_status
    ]

# Bathroom, balcony, parking and other categories
for col, selected_value in selected_categories.items():
    if selected_value != "All":
        results = results[
            results[col].astype(str) == selected_value
        ]

# Budget filter: numeric comparison
if price_limits is not None:
    results = results[
        results["_numeric_price"].between(
            price_limits[0],
            price_limits[1],
            inclusive="both"
        )
    ]

# Area filter: numeric comparison
if area_limits is not None and area_col:
    numeric_area_col = f"_numeric_area_{area_col}"

    results = results[
        results[numeric_area_col].between(
            area_limits[0],
            area_limits[1],
            inclusive="both"
        )
    ]


# =====================================================
# 9. SORT USING NUMERIC PRICE, NOT TEXT
# =====================================================

if sort_by == "Price: Low to High":
    results = results.sort_values(
        by="_numeric_price",
        ascending=True,
        na_position="last",
        kind="stable"
    )

elif sort_by == "Price: High to Low":
    results = results.sort_values(
        by="_numeric_price",
        ascending=False,
        na_position="last",
        kind="stable"
    )


# =====================================================
# 10. DISPLAY RESULTS
# =====================================================

st.subheader("Available Properties")

st.write(f"**{len(results):,} matching properties**")

if results.empty:
    st.warning(
        "No properties match your selected filters. "
        "Try changing the location, budget or other filters."
    )
    st.stop()


# =====================================================
# 11. PAGINATION
#    Avoid rendering all 187,531 records at once.
# =====================================================

page_size = 12
total_pages = max(1, math.ceil(len(results) / page_size))

page_number = st.selectbox(
    "Page",
    list(range(1, total_pages + 1)),
    format_func=lambda page: f"Page {page} of {total_pages}",
    key="results_page"
)

start = (page_number - 1) * page_size
end = start + page_size

page_results = results.iloc[start:end]


# =====================================================
# 12. PROPERTY CARDS
# =====================================================

for row_number, (_, row) in enumerate(page_results.iterrows()):

    if title_col and pd.notna(row[title_col]):
        heading = show_value(row[title_col])
    elif location_col and pd.notna(row[location_col]):
        heading = "Property in " + show_value(row[location_col])
    else:
        heading = "Property Listing"

    with st.container(border=True):

        st.markdown(
            f'<div class="property-title">{heading}</div>',
            unsafe_allow_html=True
        )

        if location_col and pd.notna(row[location_col]):
            st.write(f"📍 {show_value(row[location_col])}")

        if price_col:
            st.markdown(
                f'<div class="property-price">'
                f'{format_price(row["_numeric_price"])}</div>',
                unsafe_allow_html=True
            )

        # Main listing details
        detail_fields = [
            ("Transaction", transaction_col),
            ("Status", status_col),
            ("Furnishing", furnishing_col),
            ("Bathrooms", bathroom_col),
            ("Balconies", balcony_col),
            ("Car Parking", parking_col),
            ("Floor", floor_col),
            ("Society", society_col),
            ("Ownership", ownership_col),
            ("Facing", facing_col),
            ("Overlooking", overlooking_col)
        ]

        facts = []

        for label, col in detail_fields:
            if col and pd.notna(row[col]):
                facts.append(f"**{label}:** {show_value(row[col])}")

        if area_col and pd.notna(row[area_col]):
            facts.append(f"**{area_col}:** {show_value(row[area_col])}")

        if facts:
            st.markdown("  \n".join(facts))

        if description_col and pd.notna(row[description_col]):
            description = show_value(row[description_col])

            if len(description) > 350:
                description = description[:350] + "..."

            st.write(description)

        with st.expander("View full property details"):
            for col in search_columns:
                if pd.notna(row[col]):
                    st.write(f"**{col}:** {show_value(row[col])}")


st.caption(
    f"Showing {start + 1}–{min(end, len(results))} "
    f"of {len(results):,} matching listings."
)
