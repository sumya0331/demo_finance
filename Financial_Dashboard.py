

import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt


st.set_page_config(page_title="Financial Dashboard", layout="wide")
st.title("Financial Dashboard Demo (Enhanced & Compact)")


folder = r"C:\Financial_Demo\Raw_Data"
if not os.path.exists(folder):
    st.error(f"Folder '{folder}' олдсонгүй! Raw_Data folder-ийг '{folder}'-д үүсгэнэ үү.")
    st.stop()


@st.cache_data(ttl=60)
def load_data():
    files = [f for f in os.listdir(folder) if f.endswith('.xlsx') and not f.startswith('~$')]
    all_data = []
    for file in files:
        df = pd.read_excel(os.path.join(folder, file))
        df.columns = [c.strip() for c in df.columns]  

        
        if 'Month' in df.columns:
            df['Month'] = pd.to_datetime(df['Month'], errors='coerce')
        elif 'Data' in df.columns:
            df['Month'] = pd.to_datetime(df['Data'], errors='coerce')
        else:
            st.warning(f"{file} файлын Month/Data column олдсонгүй!")
            continue

        required_cols = ['Product', 'Branch', 'Income', 'Expense']
        if not all(c in df.columns for c in required_cols):
            st.warning(f"{file} файлын required columns тохирохгүй байна! Columns: {df.columns.tolist()}")
            continue

        df['Profit'] = df['Income'] - df['Expense']
        all_data.append(df[['Product','Branch','Month','Income','Expense','Profit']])

    if len(all_data) == 0:
        st.error("Excel файлуудаас ямар ч датаг уншиж чадсангүй!")
        st.stop()

   
    df_all = pd.concat(all_data, ignore_index=True)
    df_all['MonthInt'] = df_all['Month'].dt.year*100 + df_all['Month'].dt.month
    return df_all


if 'refresh' not in st.session_state:
    st.session_state.refresh = 0

if st.button("Refresh Data"):
    st.session_state.refresh += 1
    st.cache_data.clear()  


df_all = load_data()


product_filter = st.multiselect(
    "Select Product",
    options=df_all['Product'].unique(),
    default=df_all['Product'].unique()
)

branch_filter = st.multiselect(
    "Select Branch",
    options=df_all['Branch'].unique(),
    default=df_all['Branch'].unique()
)


min_month = int(df_all['MonthInt'].min())
max_month = int(df_all['MonthInt'].max())
month_filter = st.slider(
    "Select Month Range",
    min_value=min_month,
    max_value=max_month,
    value=(min_month, max_month)
)

filtered_df = df_all[
    (df_all['Product'].isin(product_filter)) &
    (df_all['Branch'].isin(branch_filter)) &
    (df_all['MonthInt'] >= month_filter[0]) &
    (df_all['MonthInt'] <= month_filter[1])
]


summary = filtered_df.groupby(['Product','Branch'])[['Income','Expense','Profit']].sum().reset_index()
summary['Profit_Forecast'] = summary.groupby('Product')['Profit'].transform(lambda x: x.rolling(3, min_periods=1).mean())


st.subheader("Key Metrics")
total_income = summary['Income'].sum()
total_expense = summary['Expense'].sum()
total_profit = summary['Profit'].sum()

col1, col2, col3 = st.columns([1,1,1])
col1.metric("Total Income", f"${total_income:,.0f}")
col2.metric("Total Expense", f"${total_expense:,.0f}")
if total_profit < 0:
    col3.metric("Total Profit", f"${total_profit:,.0f}", delta="⚠ Loss")
else:
    col3.metric("Total Profit", f"${total_profit:,.0f}")


tab1, tab2 = st.tabs(["Summary Table","Charts + Forecast"])

with tab1:
    st.subheader("Summary Table")
    st.dataframe(summary)

with tab2:
    st.subheader("Product-wise Charts")
    for product in summary['Product'].unique():
        prod_data = summary[summary['Product']==product]
        col1, col2 = st.columns(2)  # 2 charts per row

        with col1:
            fig, ax = plt.subplots(figsize=(5,3))
            ax.bar(prod_data['Branch'], prod_data['Income'], label='Income', alpha=0.7)
            ax.bar(prod_data['Branch'], prod_data['Expense'], label='Expense', alpha=0.7)
            ax.set_title(f"{product} Income vs Expense")
            ax.legend()
            st.pyplot(fig)

        with col2:
            fig2, ax2 = plt.subplots(figsize=(5,3))
            ax2.plot(prod_data['Branch'], prod_data['Profit_Forecast'], color='red', marker='o', label='Profit Forecast')
            ax2.set_title(f"{product} Profit Forecast")
            ax2.legend()
            st.pyplot(fig2)