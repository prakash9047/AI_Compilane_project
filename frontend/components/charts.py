"""
Plotly chart components for compliance visualization.
"""
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List
import pandas as pd


def create_compliance_gauge(score: float, title: str = "Compliance Score") -> go.Figure:
    """
    Create a gauge chart for compliance score.
    
    Args:
        score: Compliance score (0-100)
        title: Chart title
        
    Returns:
        Plotly figure
    """
    # Determine color based on score
    if score >= 80:
        color = "green"
    elif score >= 50:
        color = "yellow"
    else:
        color = "red"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 24}},
        delta={'reference': 80, 'increasing': {'color': "green"}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': '#ffcccc'},
                {'range': [50, 80], 'color': '#ffffcc'},
                {'range': [80, 100], 'color': '#ccffcc'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 80
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=60, b=20),
        font={'size': 16}
    )
    
    return fig


def create_severity_pie_chart(severity_counts: Dict[str, int]) -> go.Figure:
    """
    Create a pie chart for severity distribution.
    
    Args:
        severity_counts: Dict with severity levels and counts
        
    Returns:
        Plotly figure
    """
    labels = list(severity_counts.keys())
    values = list(severity_counts.values())
    
    colors = {
        'critical': '#d32f2f',
        'high': '#f57c00',
        'medium': '#fbc02d',
        'low': '#388e3c'
    }
    
    color_list = [colors.get(label.lower(), '#999999') for label in labels]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        marker=dict(colors=color_list),
        textinfo='label+percent+value',
        textposition='auto'
    )])
    
    fig.update_layout(
        title="Issues by Severity",
        height=400,
        showlegend=True,
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    return fig


def create_severity_bar_chart(severity_counts: Dict[str, int]) -> go.Figure:
    """
    Create a bar chart for severity distribution.
    
    Args:
        severity_counts: Dict with severity levels and counts
        
    Returns:
        Plotly figure
    """
    df = pd.DataFrame(list(severity_counts.items()), columns=['Severity', 'Count'])
    
    colors = {
        'critical': '#d32f2f',
        'high': '#f57c00',
        'medium': '#fbc02d',
        'low': '#388e3c'
    }
    
    df['Color'] = df['Severity'].str.lower().map(colors)
    
    fig = go.Figure(data=[
        go.Bar(
            x=df['Severity'],
            y=df['Count'],
            marker_color=df['Color'],
            text=df['Count'],
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        title="Issues Count by Severity",
        xaxis_title="Severity Level",
        yaxis_title="Number of Issues",
        height=400,
        showlegend=False,
        margin=dict(l=20, r=20, t=60, b=40)
    )
    
    return fig


def create_compliance_trend(trend_data: List[Dict]) -> go.Figure:
    """
    Create a line chart for compliance score trends.
    
    Args:
        trend_data: List of dicts with 'date' and 'score' keys
        
    Returns:
        Plotly figure
    """
    df = pd.DataFrame(trend_data)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['score'],
        mode='lines+markers',
        name='Compliance Score',
        line=dict(color='#1976d2', width=3),
        marker=dict(size=8),
        fill='tozeroy',
        fillcolor='rgba(25, 118, 210, 0.1)'
    ))
    
    # Add target line
    fig.add_hline(
        y=80,
        line_dash="dash",
        line_color="green",
        annotation_text="Target (80%)",
        annotation_position="right"
    )
    
    fig.update_layout(
        title="Compliance Score Trend",
        xaxis_title="Date",
        yaxis_title="Compliance Score (%)",
        yaxis_range=[0, 100],
        height=400,
        hovermode='x unified',
        margin=dict(l=20, r=20, t=60, b=40)
    )
    
    return fig


def create_rule_compliance_breakdown(rule_data: List[Dict]) -> go.Figure:
    """
    Create a horizontal bar chart for top failed rules.
    
    Args:
        rule_data: List of dicts with 'rule_name' and 'fail_count' keys
        
    Returns:
        Plotly figure
    """
    df = pd.DataFrame(rule_data)
    df = df.nlargest(10, 'fail_count')  # Top 10
    
    fig = go.Figure(data=[
        go.Bar(
            y=df['rule_name'],
            x=df['fail_count'],
            orientation='h',
            marker=dict(
                color=df['fail_count'],
                colorscale='Reds',
                showscale=True
            ),
            text=df['fail_count'],
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        title="Top 10 Failed Rules",
        xaxis_title="Failure Count",
        yaxis_title="Rule Name",
        height=500,
        showlegend=False,
        margin=dict(l=200, r=20, t=60, b=40)
    )
    
    return fig


def create_framework_comparison(framework_data: Dict[str, Dict]) -> go.Figure:
    """
    Create a stacked bar chart comparing frameworks.
    
    Args:
        framework_data: Dict with framework names and pass/fail counts
        
    Returns:
        Plotly figure
    """
    frameworks = list(framework_data.keys())
    passed = [data['passed'] for data in framework_data.values()]
    failed = [data['failed'] for data in framework_data.values()]
    
    fig = go.Figure(data=[
        go.Bar(name='Passed', x=frameworks, y=passed, marker_color='#4caf50'),
        go.Bar(name='Failed', x=frameworks, y=failed, marker_color='#f44336')
    ])
    
    fig.update_layout(
        title="Compliance by Framework",
        xaxis_title="Framework",
        yaxis_title="Number of Rules",
        barmode='stack',
        height=400,
        margin=dict(l=20, r=20, t=60, b=40)
    )
    
    return fig


def create_document_comparison(comparison_data: List[Dict]) -> go.Figure:
    """
    Create a grouped bar chart comparing documents.
    
    Args:
        comparison_data: List of dicts with 'document', 'score', 'passed', 'failed'
        
    Returns:
        Plotly figure
    """
    df = pd.DataFrame(comparison_data)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Compliance Score',
        x=df['document'],
        y=df['score'],
        marker_color='#2196f3',
        yaxis='y',
        offsetgroup=1
    ))
    
    fig.add_trace(go.Bar(
        name='Rules Passed',
        x=df['document'],
        y=df['passed'],
        marker_color='#4caf50',
        yaxis='y2',
        offsetgroup=2
    ))
    
    fig.add_trace(go.Bar(
        name='Rules Failed',
        x=df['document'],
        y=df['failed'],
        marker_color='#f44336',
        yaxis='y2',
        offsetgroup=3
    ))
    
    fig.update_layout(
        title="Document Comparison",
        xaxis_title="Document",
        yaxis=dict(
            title="Compliance Score (%)",
            side='left'
        ),
        yaxis2=dict(
            title="Rule Count",
            side='right',
            overlaying='y'
        ),
        barmode='group',
        height=400,
        margin=dict(l=20, r=60, t=60, b=100)
    )
    
    return fig


def create_compliance_heatmap(heatmap_data: pd.DataFrame) -> go.Figure:
    """
    Create a heatmap for document vs rule compliance.
    
    Args:
        heatmap_data: DataFrame with documents as rows, rules as columns
        
    Returns:
        Plotly figure
    """
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='RdYlGn',
        text=heatmap_data.values,
        texttemplate='%{text}',
        textfont={"size": 10},
        colorbar=dict(title="Compliance")
    ))
    
    fig.update_layout(
        title="Document vs Rule Compliance Matrix",
        xaxis_title="Rules",
        yaxis_title="Documents",
        height=600,
        margin=dict(l=150, r=20, t=60, b=150)
    )
    
    return fig
