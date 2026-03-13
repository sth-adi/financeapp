"""
charts.py
---------
Plotly chart factory functions for the personal finance dashboard.

Each function accepts a pandas DataFrame (or simple scalar values) and
returns a plotly Figure object ready to be passed to st.plotly_chart().
No Streamlit calls are made here — charts are kept framework-agnostic so
they can also be rendered in a notebook or exported to HTML.

All charts use a consistent minimal style:
- Clean white/light background with subtle grid lines
- A small, readable margin set
- Legends positioned to avoid overlapping the data

Dependencies: plotly (express + graph_objects), pandas
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# ---------------------------------------------------------------------------
# Shared style constants — edit these to retheme the whole dashboard at once
# ---------------------------------------------------------------------------

# Colour palette
_COLOR_INCOME   = "#2ecc71"   # green  – positive money in
_COLOR_SPENDING = "#e74c3c"   # red    – money out
_COLOR_NET      = "#9b59b6"   # purple – net / savings trend
_COLOR_GOAL     = "#3498db"   # blue   – goal progress bar

# Standard margin applied to every chart (keeps all charts aligned in the UI)
_MARGIN = dict(t=50, b=40, l=40, r=20)


# ---------------------------------------------------------------------------
# 1. Spending by category – pie / donut chart
# ---------------------------------------------------------------------------

def spending_by_category_chart(df_category: pd.DataFrame) -> go.Figure:
    """Return a donut pie chart of spending broken down by category.

    Parameters
    ----------
    df_category:
        DataFrame with at least two columns:
            category (str) – expense category label
            amount   (float) – total amount spent in that category

    Returns
    -------
    plotly Figure – donut pie chart, or an empty figure with a message if
    the DataFrame is empty.
    """
    # Guard: return a blank figure with an informative message when there is
    # no data to display (avoids cryptic Plotly errors in the UI).
    if df_category is None or df_category.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Spending by Category",
            annotations=[{
                "text": "No spending data available",
                "xref": "paper", "yref": "paper",
                "x": 0.5, "y": 0.5,
                "showarrow": False,
                "font": {"size": 14, "color": "gray"},
            }],
            margin=_MARGIN,
        )
        return fig

    fig = px.pie(
        df_category,
        names="category",
        values="amount",
        title="Spending by Category",
        hole=0.38,   # donut cutout keeps the centre uncluttered
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        # Pull each slice very slightly for visual separation
        pull=[0.02] * len(df_category),
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5),
        margin=_MARGIN,
    )

    return fig


# ---------------------------------------------------------------------------
# 2. Income vs spending – grouped bar chart
# ---------------------------------------------------------------------------

def income_vs_spending_chart(df_monthly: pd.DataFrame) -> go.Figure:
    """Return a grouped bar chart comparing income and spending each month.

    Parameters
    ----------
    df_monthly:
        DataFrame with at least three columns:
            month    (str, YYYY-MM) – calendar month label
            income   (float)        – total income for that month
            spending (float)        – total expenses for that month

    Returns
    -------
    plotly Figure – grouped bar chart with income in green and spending in red,
    or an empty figure with a message if the DataFrame is empty.
    """
    if df_monthly is None or df_monthly.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Income vs Spending by Month",
            annotations=[{
                "text": "No monthly data available",
                "xref": "paper", "yref": "paper",
                "x": 0.5, "y": 0.5,
                "showarrow": False,
                "font": {"size": 14, "color": "gray"},
            }],
            margin=_MARGIN,
        )
        return fig

    fig = go.Figure()

    # Income bars
    fig.add_trace(go.Bar(
        name="Income",
        x=df_monthly["month"],
        y=df_monthly["income"],
        marker_color=_COLOR_INCOME,
        hovertemplate="<b>%{x}</b><br>Income: $%{y:,.2f}<extra></extra>",
    ))

    # Spending bars
    fig.add_trace(go.Bar(
        name="Spending",
        x=df_monthly["month"],
        y=df_monthly["spending"],
        marker_color=_COLOR_SPENDING,
        hovertemplate="<b>%{x}</b><br>Spending: $%{y:,.2f}<extra></extra>",
    ))

    fig.update_layout(
        title="Income vs Spending by Month",
        barmode="group",
        xaxis_title="Month",
        yaxis_title="Amount ($)",
        # Place legend above the plot so it doesn't cover bars
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=_MARGIN,
        yaxis=dict(tickprefix="$", tickformat=",.0f"),
    )

    return fig


# ---------------------------------------------------------------------------
# 3. Goal progress – horizontal bar chart
# ---------------------------------------------------------------------------

def goal_progress_chart(
    goal_name: str,
    current: float,
    target: float,
) -> go.Figure:
    """Return a horizontal bar chart showing progress toward a financial goal.

    The bar is capped at 100 % so it never overflows the axis even when the
    goal has been exceeded.

    Parameters
    ----------
    goal_name:
        Display name of the goal (used as the y-axis label and chart title).
    current:
        Amount saved or accumulated so far (float).
    target:
        The goal's total target amount (float). Must be > 0.

    Returns
    -------
    plotly Figure – a compact horizontal bar scaled from 0 to 100 %.
    """
    # Prevent division by zero if target was accidentally set to 0
    if target <= 0:
        target = 1.0

    # Clamp progress to [0, 100] %
    pct       = min(current / target * 100, 100.0)
    remaining = max(target - current, 0.0)

    fig = go.Figure(go.Bar(
        x=[pct],
        y=[goal_name],
        orientation="h",
        marker_color=_COLOR_GOAL,
        # Show the percentage and raw amounts inside the bar
        text=[f"  {pct:.1f}%  —  ${current:,.0f} of ${target:,.0f}"],
        textposition="inside",
        hovertemplate=(
            f"<b>{goal_name}</b><br>"
            f"Saved: ${current:,.2f}<br>"
            f"Target: ${target:,.2f}<br>"
            f"Remaining: ${remaining:,.2f}<br>"
            f"Progress: {pct:.1f}%<extra></extra>"
        ),
    ))

    fig.update_layout(
        title=f"Goal Progress: {goal_name}",
        xaxis=dict(
            range=[0, 100],
            title="Progress (%)",
            ticksuffix="%",
        ),
        yaxis=dict(title=""),
        height=140,    # compact height — these are often stacked on a page
        margin=dict(t=45, b=25, l=10, r=20),
    )

    return fig


# ---------------------------------------------------------------------------
# 4. Savings trend – line chart
# ---------------------------------------------------------------------------

def savings_trend_chart(df_monthly: pd.DataFrame) -> go.Figure:
    """Return a line chart of net savings (income minus spending) over time.

    A dashed zero-line is drawn so it is immediately obvious which months
    were positive and which were deficit months.

    Parameters
    ----------
    df_monthly:
        DataFrame with at least two columns:
            month (str, YYYY-MM) – calendar month label
            net   (float)        – net amount (income minus spending)

    Returns
    -------
    plotly Figure – line chart with markers at each data point,
    or an empty figure with a message if the DataFrame is empty.
    """
    if df_monthly is None or df_monthly.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Monthly Net Savings Trend",
            annotations=[{
                "text": "No data available",
                "xref": "paper", "yref": "paper",
                "x": 0.5, "y": 0.5,
                "showarrow": False,
                "font": {"size": 14, "color": "gray"},
            }],
            margin=_MARGIN,
        )
        return fig

    fig = px.line(
        df_monthly,
        x="month",
        y="net",
        title="Monthly Net Savings Trend",
        markers=True,
        labels={"month": "Month", "net": "Net ($)"},
        color_discrete_sequence=[_COLOR_NET],
    )

    # Style the line and markers for readability
    fig.update_traces(
        line=dict(width=2.5),
        marker=dict(size=8),
        hovertemplate="<b>%{x}</b><br>Net: $%{y:,.2f}<extra></extra>",
    )

    # Dashed zero line makes break-even month instantly visible
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray",
        opacity=0.5,
        annotation_text="Break-even",
        annotation_position="right",
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Net ($)",
        yaxis=dict(tickprefix="$", tickformat=",.0f"),
        margin=_MARGIN,
    )

    return fig
