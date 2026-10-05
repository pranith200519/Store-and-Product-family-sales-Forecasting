import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="Sales Forecasting Dashboard",
    page_icon="📊",
    layout="wide"
)

# ---------------------------------------------------------
# TITLE
# ---------------------------------------------------------

st.title("📊 Store & Product Family Sales Forecasting Dashboard")

st.markdown(
    """
    This dashboard analyzes sales data from multiple retail datasets.
    It provides insights into sales trends, stores, products, promotions,
    local events and demand patterns.
    """
)

# ---------------------------------------------------------
# DATA FILES
# ---------------------------------------------------------

DATA_FOLDER = "Data"

FILES = {
    "Product Sales M5": "Product_Sales_M5_Style_Final.xlsx",
    "Walmart Retail Sales": "Walmart_Retail_Sales_Forecasting_Final.xlsx",
    "Store Item Demand": "Store_Item_Demand_Forecasting_Final.xlsx"
}

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

@st.cache_data
def load_data(file_path):
    return pd.read_excel(file_path)


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

st.sidebar.header("⚙️ Dashboard Settings")

selected_dataset = st.sidebar.selectbox(
    "Select Dataset",
    list(FILES.keys())
)

file_path = os.path.join(
    DATA_FOLDER,
    FILES[selected_dataset]
)

# ---------------------------------------------------------
# CHECK FILE
# ---------------------------------------------------------

if not os.path.exists(file_path):

    st.error(
        f"File not found:\n\n{file_path}\n\n"
        "Please check that the Excel file is inside the data folder."
    )

    st.stop()


# ---------------------------------------------------------
# READ DATA
# ---------------------------------------------------------

df = load_data(file_path)

# Remove completely empty rows
df = df.dropna(how="all")

# ---------------------------------------------------------
# AUTOMATIC DATE DETECTION
# ---------------------------------------------------------

date_columns = [
    col for col in df.columns
    if "date" in col.lower()
]

if date_columns:

    date_column = date_columns[0]

    df[date_column] = pd.to_datetime(
        df[date_column],
        errors="coerce"
    )

    df = df.dropna(subset=[date_column])

else:

    date_column = None


# ---------------------------------------------------------
# AUTOMATIC NUMERIC COLUMNS
# ---------------------------------------------------------

numeric_columns = df.select_dtypes(
    include="number"
).columns.tolist()


# ---------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------

st.sidebar.subheader("🔎 Filters")

filtered_df = df.copy()


# Date filter
if date_column:

    min_date = df[date_column].min().date()
    max_date = df[date_column].max().date()

    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if len(date_range) == 2:

        start_date = pd.Timestamp(date_range[0])
        end_date = pd.Timestamp(date_range[1])

        filtered_df = filtered_df[
            (filtered_df[date_column] >= start_date)
            &
            (filtered_df[date_column] <= end_date)
        ]


# Category filters
categorical_columns = df.select_dtypes(
    include=["object", "category"]
).columns.tolist()

for col in categorical_columns:

    # Don't show extremely large categorical columns
    if df[col].nunique() <= 50:

        values = sorted(
            df[col].dropna().astype(str).unique().tolist()
        )

        selected_values = st.sidebar.multiselect(
            f"Select {col}",
            values
        )

        if selected_values:

            filtered_df = filtered_df[
                filtered_df[col].astype(str).isin(selected_values)
            ]


# ---------------------------------------------------------
# DATASET INFORMATION
# ---------------------------------------------------------

st.subheader("📋 Dataset Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Rows",
        f"{len(filtered_df):,}"
    )

with col2:
    st.metric(
        "Total Columns",
        f"{len(filtered_df.columns):,}"
    )

with col3:
    st.metric(
        "Missing Values",
        f"{filtered_df.isna().sum().sum():,}"
    )

with col4:
    st.metric(
        "Duplicate Rows",
        f"{filtered_df.duplicated().sum():,}"
    )


# ---------------------------------------------------------
# FIND SALES COLUMN
# ---------------------------------------------------------

sales_candidates = [
    col for col in df.columns
    if any(
        word in col.lower()
        for word in [
            "sales",
            "sale",
            "revenue",
            "demand",
            "quantity",
            "units"
        ]
    )
]

sales_column = None

for col in sales_candidates:

    if pd.api.types.is_numeric_dtype(df[col]):

        sales_column = col
        break


# ---------------------------------------------------------
# KPI SECTION
# ---------------------------------------------------------

st.subheader("📈 Key Performance Indicators")

k1, k2, k3, k4 = st.columns(4)

if sales_column:

    total_sales = filtered_df[sales_column].sum()

    average_sales = filtered_df[sales_column].mean()

    maximum_sales = filtered_df[sales_column].max()

    minimum_sales = filtered_df[sales_column].min()

    with k1:
        st.metric(
            "Total Sales / Demand",
            f"{total_sales:,.2f}"
        )

    with k2:
        st.metric(
            "Average",
            f"{average_sales:,.2f}"
        )

    with k3:
        st.metric(
            "Maximum",
            f"{maximum_sales:,.2f}"
        )

    with k4:
        st.metric(
            "Minimum",
            f"{minimum_sales:,.2f}"
        )

else:

    with k1:
        st.metric("Rows", len(filtered_df))

    with k2:
        st.metric("Columns", len(filtered_df.columns))

    with k3:
        st.metric(
            "Numeric Columns",
            len(numeric_columns)
        )

    with k4:
        st.metric(
            "Categorical Columns",
            len(categorical_columns)
        )


# ---------------------------------------------------------
# SALES TREND
# ---------------------------------------------------------

if date_column and sales_column:

    st.subheader("📅 Sales Trend Over Time")

    trend = (
        filtered_df
        .groupby(date_column)[sales_column]
        .sum()
        .reset_index()
    )

    fig = px.line(
        trend,
        x=date_column,
        y=sales_column,
        title="Sales / Demand Over Time",
        markers=True
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title=sales_column
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ---------------------------------------------------------
# MONTHLY SALES
# ---------------------------------------------------------

if date_column and sales_column:

    st.subheader("📊 Monthly Sales Analysis")

    monthly_df = filtered_df.copy()

    monthly_df["Year-Month"] = (
        monthly_df[date_column]
        .dt.to_period("M")
        .astype(str)
    )

    monthly_sales = (
        monthly_df
        .groupby("Year-Month")[sales_column]
        .sum()
        .reset_index()
    )

    fig = px.bar(
        monthly_sales,
        x="Year-Month",
        y=sales_column,
        title="Monthly Sales"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ---------------------------------------------------------
# YEAR ANALYSIS
# ---------------------------------------------------------

if date_column and sales_column:

    st.subheader("📆 Yearly Sales")

    yearly_df = filtered_df.copy()

    yearly_df["Year"] = (
        yearly_df[date_column]
        .dt.year
    )

    yearly_sales = (
        yearly_df
        .groupby("Year")[sales_column]
        .sum()
        .reset_index()
    )

    fig = px.bar(
        yearly_sales,
        x="Year",
        y=sales_column,
        title="Yearly Sales"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ---------------------------------------------------------
# STORE ANALYSIS
# ---------------------------------------------------------

store_columns = [
    col for col in df.columns
    if "store" in col.lower()
]

if store_columns and sales_column:

    store_column = store_columns[0]

    st.subheader("🏪 Store-wise Sales")

    store_sales = (
        filtered_df
        .groupby(store_column)[sales_column]
        .sum()
        .reset_index()
        .sort_values(
            sales_column,
            ascending=False
        )
        .head(20)
    )

    fig = px.bar(
        store_sales,
        x=store_column,
        y=sales_column,
        title="Top Stores by Sales"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ---------------------------------------------------------
# PRODUCT ANALYSIS
# ---------------------------------------------------------

product_columns = [
    col for col in df.columns
    if any(
        word in col.lower()
        for word in [
            "product",
            "family",
            "item"
        ]
    )
]

if product_columns and sales_column:

    product_column = product_columns[0]

    st.subheader("🛍️ Product-wise Sales")

    product_sales = (
        filtered_df
        .groupby(product_column)[sales_column]
        .sum()
        .reset_index()
        .sort_values(
            sales_column,
            ascending=False
        )
        .head(20)
    )

    fig = px.bar(
        product_sales,
        x=product_column,
        y=sales_column,
        title="Top Products / Product Families"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ---------------------------------------------------------
# PROMOTION ANALYSIS
# ---------------------------------------------------------

promotion_columns = [
    col for col in df.columns
    if "promo" in col.lower()
    or "promotion" in col.lower()
]

if promotion_columns and sales_column:

    promotion_column = promotion_columns[0]

    st.subheader("🎯 Promotion Analysis")

    promotion_sales = (
        filtered_df
        .groupby(promotion_column)[sales_column]
        .mean()
        .reset_index()
    )

    fig = px.bar(
        promotion_sales,
        x=promotion_column,
        y=sales_column,
        title="Average Sales During Promotions"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ---------------------------------------------------------
# EVENT ANALYSIS
# ---------------------------------------------------------

event_columns = [
    col for col in df.columns
    if "event" in col.lower()
    or "holiday" in col.lower()
]

if event_columns and sales_column:

    event_column = event_columns[0]

    st.subheader("🎉 Event / Holiday Analysis")

    event_sales = (
        filtered_df
        .groupby(event_column)[sales_column]
        .mean()
        .reset_index()
    )

    fig = px.bar(
        event_sales,
        x=event_column,
        y=sales_column,
        title="Average Sales by Event / Holiday"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ---------------------------------------------------------
# CORRELATION
# ---------------------------------------------------------

if len(numeric_columns) >= 2:

    st.subheader("🔗 Correlation Analysis")

    correlation = filtered_df[
        numeric_columns
    ].corr()

    fig = px.imshow(
        correlation,
        text_auto=True,
        title="Correlation Matrix"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ---------------------------------------------------------
# DATA TABLE
# ---------------------------------------------------------

st.subheader("📄 Final Preprocessed Data")

st.dataframe(
    filtered_df,
    use_container_width=True,
    height=400
)


# ---------------------------------------------------------
# DOWNLOAD FILTERED DATA
# ---------------------------------------------------------

st.subheader("⬇️ Download Data")

csv_data = filtered_df.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="Download Filtered Dataset",
    data=csv_data,
    file_name="filtered_sales_data.csv",
    mime="text/csv"
)


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.markdown("---")

st.caption(
    "Store & Product Family Sales Forecasting "
    "under Promotions and Local Events"
)