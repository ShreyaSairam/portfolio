import streamlit as st
import streamlit.components.v1 as components

URL = "https://shreyasairam.github.io/out-of-phase/"

st.title("Out of Phase: Who Does Your Battery Work For?")
st.caption(
    "Big batteries earn money by following the electricity price, set for a whole region. The strain on the "
    "grid happens at the local substation. Using real data from Sydney (AEMO prices, 104 Ausgrid substations) "
    "and Delhi, this asks whether the two line up. In Sydney they do on only 42% of days."
)
st.link_button("Open full screen", URL)
components.iframe(URL, height=900, scrolling=True)
