import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

def create_srq_visualization(score):
    """Create a gauge chart for SRQ-20 score"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "SRQ-20 Score"},
        gauge={
            'axis': {'range': [None, 20], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 5], 'color': 'green'},
                {'range': [5, 8], 'color': 'yellow'},
                {'range': [8, 11], 'color': 'orange'},
                {'range': [11, 20], 'color': 'red'},
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 8
            }
        }
    ))
    
    return fig

def create_dass_visualization(depression, anxiety, stress):
    """Create a bar chart for DASS-42 scores"""
    data = {
        'Scale': ['Depression', 'Anxiety', 'Stress'],
        'Score': [depression, anxiety, stress]
    }
    df = pd.DataFrame(data)
    
    # Define color based on severity
    colors = []
    
    # Depression colors
    if depression < 10:
        colors.append('green')
    elif depression < 14:
        colors.append('yellow')
    elif depression < 21:
        colors.append('orange')
    else:
        colors.append('red')
    
    # Anxiety colors
    if anxiety < 8:
        colors.append('green')
    elif anxiety < 10:
        colors.append('yellow')
    elif anxiety < 15:
        colors.append('orange')
    else:
        colors.append('red')
    
    # Stress colors
    if stress < 15:
        colors.append('green')
    elif stress < 19:
        colors.append('yellow')
    elif stress < 26:
        colors.append('orange')
    else:
        colors.append('red')
    
    fig = px.bar(df, x='Scale', y='Score', text='Score', color='Scale',
                title="DASS-42 Scores")
    
    return fig

def create_demographics_pie_chart(patients, field):
    """Create a pie chart for demographic data"""
    # Extract the field values
    values = [p.get(field, 'Unknown') for p in patients if p.get(field)]
    
    # Count occurrences
    counts = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    
    # Create dataframe
    df = pd.DataFrame({
        'Category': list(counts.keys()),
        'Count': list(counts.values())
    })
    
    fig = px.pie(df, names='Category', values='Count', title=f"{field.capitalize()} Distribution")
    
    return fig

def create_trends_chart(patients, field, date_field='created_at'):
    """Create a trend chart over time"""
    data = []
    for p in patients:
        if p.get(field) and p.get(date_field):
            data.append({
                'date': p.get(date_field),
                'value': p.get(field)
            })
    
    if not data:
        return None
    
    # Sort by date
    data.sort(key=lambda x: x['date'])
    
    # Create dataframe
    df = pd.DataFrame(data)
    
    fig = px.line(df, x='date', y='value', title=f"{field.capitalize()} Trend")
    
    return fig
