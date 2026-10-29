"""The app's look beyond its theme (app/.streamlit/config.toml): one stylesheet, injected once by app.py, so a
screen never carries its own CSS for things every screen shares.

One blue palette: text and titles navy #14213D, secondary text slate #4A5568, accent blue #2F6FB5, the page light
blue #F5F8FC and the sidebar soft blue #E8F0FA (the theme). Every text keeps a WCAG contrast of at least 4.5:1 on its
background (Streamlit's captions, the text colour at 60 %, fell under it: they are slate here). Notices use soft backgrounds of the same
palette with navy text, not Streamlit's own blue, yellow and green.
"""
import streamlit as st
import streamlit.components.v1 as components

MARK = "#9C4A00"   # a warning mark in text (dark amber): 5:1 or more on the page's light blue

CSS = """<style>
/* The theme guard (apply) takes no room */
[data-testid=stElementContainer]:has(iframe[height="0"]) {display: none;}

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

/* Secondary text in slate, solid (not the text colour at 60 %, which fell under 4.5:1) */
[data-testid=stCaptionContainer], [data-testid=stCaptionContainer] p, [data-testid=stWidgetLabel] small {color: #4A5568;}
a, a:visited {color: #2F6FB5;}

/* Notices in the palette: a soft background, navy text, an accent on the left */
[data-testid=stAlertContainer] {border-left: 4px solid transparent; border-radius: 10px;}
[data-testid=stAlertContainer]:has([data-testid=stAlertContentInfo]) {background: #DCE8F7; border-left-color: #2F6FB5;}
[data-testid=stAlertContainer]:has([data-testid=stAlertContentWarning]) {background: #FBF1DE; border-left-color: #B7791F;}
[data-testid=stAlertContainer]:has([data-testid=stAlertContentSuccess]) {background: #E6F2EA; border-left-color: #2F855A;}
[data-testid=stAlertContainer]:has([data-testid=stAlertContentError]) {background: #FBE9E7; border-left-color: #C53030;}
[data-testid=stAlertContainer] p, [data-testid=stAlertContainer] li {color: #14213D;}

/* Inline code in the palette (Streamlit's is green, 2.7:1) */
[data-testid=stMarkdownContainer] code, [data-testid=stCaptionContainer] code {color: #14213D; background: #E1E9F5;}

/* Code blocks (SPARQL, SQL, Turtle): Streamlit's highlighting is made for white and falls to 2.4:1 here; the same
   roles in darker shades of the palette, 5:1 to 8:1 on the block's background */
[data-testid=stCode] code, [data-testid=stCode] .token {color: #14213D;}
[data-testid=stCode] .token.variable {color: #0B5E7A;}
[data-testid=stCode] .token.keyword, [data-testid=stCode] .token.function {color: #1F4E8C;}
[data-testid=stCode] .token.string, [data-testid=stCode] .token.number, [data-testid=stCode] .token.boolean {color: #1E6B3A;}
[data-testid=stCode] .token.url {color: #5B2C9E;}
[data-testid=stCode] .token.punctuation, [data-testid=stCode] .token.operator {color: #4A5568;}
[data-testid=stCode] .token.comment {color: #5A6A80; font-style: italic;}

/* A disabled button stays readable (Streamlit dims its text to 40 %) */
button:disabled, button:disabled p {color: #5A6A80 !important;}

/* Big numbers in the decks' blue */
[data-testid=stMetricValue] {color: #2F6FB5;}

/* Expanders read as sections */
[data-testid=stExpander] summary p {font-weight: 600;}

/* The sidebar's long texts, smaller */
[data-testid=stSidebar] [data-testid=stCaptionContainer] {font-size: 0.78rem; line-height: 1.35;}
</style>"""


# Streamlit keeps the last theme a browser chose (localStorage), and that wins over the app's theme: a browser that
# once had «Dark» drew this palette's navy titles on a dark background. The app has one theme, so a stored choice that
# is not it is removed, and the page reloads once with the app's theme.
KEEP_THEME = """<script>
try {
  const key = 'stActiveTheme-/-v1', stored = window.parent.localStorage.getItem(key);
  if (stored && JSON.parse(stored).name !== 'Custom Theme') {
    window.parent.localStorage.removeItem(key);
    window.parent.location.reload();
  }
} catch (e) {}
</script>"""


def apply():
    st.markdown(CSS, unsafe_allow_html=True)
    components.html(KEEP_THEME, height=0)
