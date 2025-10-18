import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Coffee Shop Acquisition Model", layout="wide", page_icon="☕")

# Custom CSS
st.markdown("""
    <style>
    .main {padding: 2rem;}
    .stMetric {background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem;}
    </style>
    """, unsafe_allow_html=True)

# Header
st.title("☕ Coffee Shop Acquisition Financial Model")
st.markdown("**Interactive analysis for multi-location retail acquisition**")
st.divider()

# Sidebar inputs
with st.sidebar:
    st.header("📊 Model Assumptions")
    
    st.subheader("Purchase & Financing")
    purchase_price = st.slider("Purchase Price ($)", 500000, 1000000, 750000, 10000, format="$%d")
    down_payment_pct = st.slider("Down Payment (%)", 10, 40, 20, 5)
    interest_rate = st.slider("Interest Rate (%)", 4.0, 12.0, 7.0, 0.5)
    loan_term = st.slider("Loan Term (years)", 5, 15, 7, 1)
    
    st.subheader("Revenue & Growth")
    current_revenue = st.slider("Current Annual Revenue ($)", 300000, 800000, 500000, 10000, format="$%d")
    base_growth = st.slider("Base Case Growth (%)", 0.0, 15.0, 5.0, 0.5)
    optimistic_growth = st.slider("Optimistic Growth (%)", 5.0, 20.0, 8.0, 0.5)
    pessimistic_growth = st.slider("Pessimistic Growth (%)", 0.0, 10.0, 2.0, 0.5)
    
    st.subheader("Operating Expenses (% of Revenue)")
    cogs_pct = st.slider("COGS (%)", 25, 45, 35, 1)
    labor_pct = st.slider("Labor (%)", 20, 40, 30, 1)
    rent_pct = st.slider("Rent (%)", 10, 25, 15, 1)
    other_opex_pct = st.slider("Other OpEx (%)", 5, 20, 10, 1)

def calculate_scenario(growth_rate):
    """Calculate financial projections for a given growth scenario"""
    down_payment = purchase_price * (down_payment_pct / 100)
    loan_amount = purchase_price - down_payment
    monthly_rate = interest_rate / 100 / 12
    num_payments = loan_term * 12
    
    # Calculate monthly payment using amortization formula
    if monthly_rate > 0:
        monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    else:
        monthly_payment = loan_amount / num_payments
    
    annual_debt_service = monthly_payment * 12
    
    years_data = []
    cumulative_cf = -down_payment
    
    for year in range(6):
        if year == 0:
            years_data.append({
                'Year': 0,
                'Revenue': current_revenue,
                'COGS': 0,
                'Labor': 0,
                'Rent': 0,
                'Other OpEx': 0,
                'EBITDA': 0,
                'Debt Service': 0,
                'Cash Flow': -down_payment,
                'Cumulative CF': cumulative_cf
            })
        else:
            revenue = current_revenue * (1 + growth_rate / 100) ** year
            cogs = revenue * (cogs_pct / 100)
            labor = revenue * (labor_pct / 100)
            rent = revenue * (rent_pct / 100)
            other_opex = revenue * (other_opex_pct / 100)
            total_opex = cogs + labor + rent + other_opex
            ebitda = revenue - total_opex
            cash_flow = ebitda - annual_debt_service
            cumulative_cf += cash_flow
            
            years_data.append({
                'Year': year,
                'Revenue': revenue,
                'COGS': cogs,
                'Labor': labor,
                'Rent': rent,
                'Other OpEx': other_opex,
                'EBITDA': ebitda,
                'Debt Service': annual_debt_service,
                'Cash Flow': cash_flow,
                'Cumulative CF': cumulative_cf
            })
    
    df = pd.DataFrame(years_data)
    
    # Calculate IRR manually
cash_flows = [-down_payment] + df[df['Year'] > 0]['Cash Flow'].tolist()
try:
    # Simple IRR calculation using numpy_financial alternative
    def calculate_irr(cashflows, iterations=100):
        rate = 0.1
        for i in range(iterations):
            npv = sum([cf / (1 + rate) ** t for t, cf in enumerate(cashflows)])
            if abs(npv) < 1:
                return rate * 100
            dnpv = sum([-t * cf / (1 + rate) ** (t + 1) for t, cf in enumerate(cashflows)])
            rate = rate - npv / dnpv
        return rate * 100
    irr = calculate_irr(cash_flows)
except:
    irr = 0
    
    # Calculate payback period
    payback_df = df[df['Cumulative CF'] > 0]
    payback = payback_df['Year'].min() if len(payback_df) > 0 else 'N/A'
    
    return df, irr, payback, down_payment, annual_debt_service

# Calculate all scenarios
pessimistic_df, pessimistic_irr, pessimistic_payback, down_payment, debt_service = calculate_scenario(pessimistic_growth)
base_df, base_irr, base_payback, _, _ = calculate_scenario(base_growth)
optimistic_df, optimistic_irr, optimistic_payback, _, _ = calculate_scenario(optimistic_growth)

# Key Metrics Display
st.subheader("📈 Key Performance Indicators")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🔴 Pessimistic")
    st.metric("IRR", f"{pessimistic_irr:.2f}%")
    st.metric("Payback", f"Year {pessimistic_payback}" if pessimistic_payback != 'N/A' else 'N/A')

with col2:
    st.markdown("### 🔵 Base Case")
    st.metric("IRR", f"{base_irr:.2f}%")
    st.metric("Payback", f"Year {base_payback}" if base_payback != 'N/A' else 'N/A')

with col3:
    st.markdown("### 🟢 Optimistic")
    st.metric("IRR", f"{optimistic_irr:.2f}%")
    st.metric("Payback", f"Year {optimistic_payback}" if optimistic_payback != 'N/A' else 'N/A')

st.divider()

# Visualization Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Revenue", "💰 Cash Flow", "📋 Tables", "📥 Export"])

with tab1:
    st.subheader("5-Year Revenue Projections")
    fig = go.Figure()
    
    for df, name, color in [(pessimistic_df, 'Pessimistic', 'red'), 
                             (base_df, 'Base', 'blue'), 
                             (optimistic_df, 'Optimistic', 'green')]:
        filtered = df[df['Year'] > 0]
        fig.add_trace(go.Scatter(
            x=filtered['Year'], 
            y=filtered['Revenue'],
            name=name, 
            line=dict(color=color, width=3),
            mode='lines+markers'
        ))
    
    fig.update_layout(
        xaxis_title="Year", 
        yaxis_title="Revenue ($)",
        height=400,
        hovermode='x unified',
        yaxis=dict(tickformat='$,.0f')
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Annual Cash Flow by Scenario")
    fig = go.Figure()
    
    scenarios = [
        (pessimistic_df, 'Pessimistic', 'red'),
        (base_df, 'Base', 'blue'),
        (optimistic_df, 'Optimistic', 'green')
    ]
    
    for df, name, color in scenarios:
        filtered = df[df['Year'] > 0]
        fig.add_trace(go.Bar(
            x=filtered['Year'], 
            y=filtered['Cash Flow'],
            name=name,
            marker_color=color
        ))
    
    fig.update_layout(
        xaxis_title="Year", 
        yaxis_title="Cash Flow ($)",
        barmode='group',
        height=400,
        yaxis=dict(tickformat='$,.0f')
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Cumulative cash flow
    st.subheader("Cumulative Cash Flow")
    fig2 = go.Figure()
    
    for df, name, color in scenarios:
        fig2.add_trace(go.Scatter(
            x=df['Year'], 
            y=df['Cumulative CF'],
            name=name,
            line=dict(color=color, width=3),
            mode='lines+markers'
        ))
    
    fig2.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Break Even")
    fig2.update_layout(
        xaxis_title="Year", 
        yaxis_title="Cumulative Cash Flow ($)",
        height=400,
        yaxis=dict(tickformat='$,.0f')
    )
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    scenario_choice = st.selectbox("Select Scenario", ["Base Case", "Pessimistic", "Optimistic"])
    
    if scenario_choice == "Base Case":
        display_df = base_df.copy()
    elif scenario_choice == "Pessimistic":
        display_df = pessimistic_df.copy()
    else:
        display_df = optimistic_df.copy()
    
    st.subheader(f"{scenario_choice} - Detailed Projections")
    
    # Format currency columns
    currency_cols = ['Revenue', 'COGS', 'Labor', 'Rent', 'Other OpEx', 'EBITDA', 'Debt Service', 'Cash Flow', 'Cumulative CF']
    formatted_df = display_df.copy()
    for col in currency_cols:
        formatted_df[col] = formatted_df[col].apply(lambda x: f"${x:,.0f}")
    
    st.dataframe(formatted_df, use_container_width=True, hide_index=True)

with tab4:
    st.subheader("📥 Export Data")
    st.markdown("Download your financial projections for further analysis.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV Export
        csv = base_df.to_csv(index=False)
        st.download_button(
            label="📄 Download Base Case CSV",
            data=csv,
            file_name="coffee_shop_base_case.csv",
 mime="text/csv"
)
