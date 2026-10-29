"""The app's look beyond its theme (app/.streamlit/config.toml): one stylesheet, injected once by app.py, so a
screen never carries its own CSS for things every screen shares. Colours are the decks': blue #2F6FB5, titles
#14213D, background #F7F6F2.
"""
import streamlit as st

CSS = """<style>
/* Room for the content: less empty space above and at the sides */
[data-testid=stMainBlockContainer] {padding: 2.5rem 3rem 6rem;}

/* Titles in the decks' dark blue, a little tighter */
h1, h2, h3 {color: #14213D; letter-spacing: -0.01em;}

/* Cards side by side are as tall as the tallest: a bordered container alone in its column fills it */
[data-testid=stHorizontalBlock] {align-items: stretch;}
[data-testid=stColumn] > [data-testid=stVerticalBlockBorderWrapper],
[data-testid=stColumn] > [data-testid=stVerticalBlockBorderWrapper] > div,
[data-testid=stColumn] > [data-testid=stVerticalBlockBorderWrapper] > div > [data-testid=stVerticalBlock] {height: 100%;}
[data-testid=stColumn] [data-testid=stVerticalBlock] > [data-testid=stVerticalBlockBorderWrapper]:only-child {height: 100%;}

/* Big numbers in the decks' blue */
[data-testid=stMetricValue] {color: #2F6FB5;}

/* Expanders read as sections */
[data-testid=stExpander] summary p {font-weight: 600;}

/* The sidebar's long texts, smaller */
[data-testid=stSidebar] [data-testid=stCaptionContainer] {font-size: 0.78rem; line-height: 1.35;}
</style>"""


def apply():
    st.markdown(CSS, unsafe_allow_html=True)
