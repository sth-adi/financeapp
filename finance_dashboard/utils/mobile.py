import streamlit as st


MOBILE_CSS = """
<style>
/* Stack columns vertically on small screens */
@media (max-width: 768px) {
    div[data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }

    /* Reduce font size for metric values so they fit */
    div[data-testid="metric-container"] {
        padding: 0.4rem 0.6rem;
    }

    /* Make dataframes scroll horizontally */
    div[data-testid="stDataFrame"] {
        overflow-x: auto;
    }

    /* Shrink sidebar toggle button area */
    section[data-testid="stSidebar"] {
        min-width: 0 !important;
    }

    /* Make plotly charts not overflow */
    div.js-plotly-plot {
        max-width: 100%;
    }
}
</style>
"""


def inject_mobile_css():
    """Inject responsive CSS to improve the app on small screens."""
    st.markdown(MOBILE_CSS, unsafe_allow_html=True)
