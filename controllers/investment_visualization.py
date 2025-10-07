import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np

def calculate_compound_growth(monthly_contribution, annual_return, months):
    """Calculate compound growth over time with monthly contributions."""
    monthly_return = annual_return / 12
    total_invested = []
    total_value = []
    interest_earned = []
    
    for month in range(months + 1):
        if month == 0:
            invested = 0
            value = 0
            interest = 0
        else:
            # Previous value grows by monthly return
            prev_value = total_value[-1] if total_value else 0
            grown_value = prev_value * (1 + monthly_return)
            
            # Add new contribution
            value = grown_value + monthly_contribution
            invested = (total_invested[-1] if total_invested else 0) + monthly_contribution
            interest = value - invested
        
        total_invested.append(invested)
        total_value.append(value)
        interest_earned.append(interest)
    
    return total_invested, total_value, interest_earned

def create_investment_comparison_chart(investment_data):
    """Create a comparison chart showing different investment options over time."""
    months = 20 * 12  # 20 years
    fig = go.Figure()
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    for i, (option, data) in enumerate(investment_data.items()):
        monthly_contribution = data['monthly_contribution']
        annual_return = data['annual_return'] / 100
        
        invested, value, interest = calculate_compound_growth(
            monthly_contribution, annual_return, months
        )
        
        months_array = list(range(months + 1))
        
        fig.add_trace(go.Scatter(
            x=months_array,
            y=value,
            mode='lines',
            name=f"{option} (${value[-1]:,.0f})",
            line=dict(color=colors[i % len(colors)], width=3),
            hovertemplate=f"<b>{option}</b><br>" +
                         "Month: %{x}<br>" +
                         "Value: $%{y:,.0f}<br>" +
                         "<extra></extra>"
        ))
    
    fig.update_layout(
        title="Investment Growth Comparison Over Time",
        xaxis_title="Months",
        yaxis_title="Portfolio Value ($)",
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=12)
    )
    
    return fig

def create_contribution_breakdown_chart(investment_data):
    """Create a pie chart showing monthly contribution breakdown."""
    labels = list(investment_data.keys())
    values = [data['monthly_contribution'] for data in investment_data.values()]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        textinfo='label+percent+value',
        texttemplate='%{label}<br>$%{value:,.0f}<br>(%{percent})',
        hovertemplate='<b>%{label}</b><br>Monthly: $%{value:,.0f}<br>Percentage: %{percent}<extra></extra>'
    )])
    
    fig.update_layout(
        title="Monthly Contribution Distribution",
        height=400,
        showlegend=True,
        font=dict(size=12)
    )
    
    return fig

def create_goal_progress_chart(investment_data, goal_amount):
    """Create a bar chart showing progress toward goal."""
    options = list(investment_data.keys())
    final_values = []
    goal_achieved = []
    
    months = 20 * 12  # 20 years
    
    for option, data in investment_data.items():
        monthly_contribution = data['monthly_contribution']
        annual_return = data['annual_return'] / 100
        
        _, value, _ = calculate_compound_growth(monthly_contribution, annual_return, months)
        final_value = value[-1]
        final_values.append(final_value)
        goal_achieved.append(final_value >= goal_amount)
    
    colors = ['#2ca02c' if achieved else '#d62728' for achieved in goal_achieved]
    
    fig = go.Figure(data=[
        go.Bar(
            x=options,
            y=final_values,
            marker_color=colors,
            text=[f"${val:,.0f}" for val in final_values],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Final Value: $%{y:,.0f}<br>Goal: $' + f"{goal_amount:,.0f}" + '<extra></extra>'
        )
    ])
    
    fig.add_hline(
        y=goal_amount, 
        line_dash="dash", 
        line_color="red",
        annotation_text=f"Goal: ${goal_amount:,.0f}",
        annotation_position="top right"
    )
    
    fig.update_layout(
        title="Final Portfolio Value vs Goal",
        xaxis_title="Investment Option",
        yaxis_title="Final Value ($)",
        height=400,
        showlegend=False,
        font=dict(size=12)
    )
    
    return fig

def display_investment_visualizations(investment_table_text, goal_amount):
    """Parse investment table and create visualizations."""
    try:
        # st.write(f"🎯 display_investment_visualizations called with goal_amount: {goal_amount}")
        # st.write(f"🎯 Table text length: {len(investment_table_text) if investment_table_text else 0}")
        # st.write(f"🎯 First 200 chars: {investment_table_text[:200] if investment_table_text else 'None'}")
        
        if not investment_table_text or not investment_table_text.strip():
            st.warning("No investment table data provided for visualization.")
            return

        # Split table text into lines
        lines = investment_table_text.strip().split('\n')
        # st.write(f"🎯 Total lines to process: {len(lines)}")

        # Clean broken lines in table (handle line breaks inside cells)
        cleaned_lines = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            if line.startswith('|') and line.endswith('|'):
                cleaned_lines.append(line)
                i += 1
            elif line.startswith('|') and not line.endswith('|'):
                # Reconstruct broken line
                reconstructed = line
                i += 1
                while i < len(lines):
                    next_line = lines[i].strip()
                    if not next_line:
                        i += 1
                        continue
                    if next_line.startswith('|'):
                        break
                    reconstructed += " " + next_line
                    i += 1
                reconstructed = reconstructed.replace('∣', '|')
                cleaned_lines.append(reconstructed)
            else:
                cleaned_lines.append(line)
                i += 1

        # st.write(f"🎯 Cleaned lines: {len(cleaned_lines)}")

        # Parse table into dictionary
        investment_data = {}
        for line in cleaned_lines:
            # Skip header and separator lines
            if 'Investment Option' in line or line.startswith('|---') or line.startswith('|----------------'):
                continue

            # Split line into columns
            parts = [part.strip() for part in line.split('|')][1:-1]  # remove empty first/last element
            if len(parts) < 7:
                continue

            option = parts[0]
            return_range = parts[1]
            effective_return = parts[2]
            monthly_contrib = parts[3]

            try:
                annual_return = float(effective_return.replace('%',''))
                monthly_contribution = float(monthly_contrib.replace('$','').replace(',',''))
                if annual_return > 0 and monthly_contribution > 0:
                    investment_data[option] = {
                        'annual_return': annual_return,
                        'monthly_contribution': monthly_contribution
                    }
                    # st.write(f"✅ Added {option}: {annual_return}%, ${monthly_contribution}")
            except Exception as e:
                st.write(f"⚠️ Error parsing line: {line} -> {e}")
                continue

        if not investment_data:
            st.warning("Could not parse investment data. Using sample data for demonstration.")
            investment_data = {
                "Bank Savings Account": {"annual_return": 3.56, "monthly_contribution": 2882.93},
                "Equity Mutual Funds": {"annual_return": 10.47, "monthly_contribution": 1316.88},
                "Index Funds": {"annual_return": 13.24, "monthly_contribution": 944.74},
                "Stock Market": {"annual_return": 18.97, "monthly_contribution": 466.09}
            }

        # Create visualizations
        st.markdown("### 📊 Investment Growth Analysis")
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(create_contribution_breakdown_chart(investment_data), use_container_width=True)
        with col2:
            st.plotly_chart(create_goal_progress_chart(investment_data, goal_amount), use_container_width=True)
        st.plotly_chart(create_investment_comparison_chart(investment_data), use_container_width=True)

    except Exception as e:
        st.error(f"Error creating visualizations: {str(e)}")

def extract_investment_table_from_response(response_text):
    """Extract the investment options table from the agent response."""
    if not response_text:
        return None
        
    lines = response_text.split('\n')
    table_lines = []
    inside_table = False
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        # Start table when header line is found
        if not inside_table and 'investment option' in line_lower and '|' in line:
            inside_table = True
            table_lines.append(line)
            continue
        
        if inside_table:
            if line.strip() == "" or line.startswith('####'):
                # end of table
                break
            elif '|' in line:
                table_lines.append(line)
            else:
                # ignore non-table lines inside table section
                continue
    
    if table_lines:
        return '\n'.join(table_lines)
    
    return None
