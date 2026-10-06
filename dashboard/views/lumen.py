import streamlit as st
import streamlit.components.v1 as components

URL = "https://lumen.yuanhaofeng.com/"

st.title("Lumen: Smart Precinct Platform")
st.caption(
    "FEIT Hackathon 2026: SMEC Spot Prize, Top 5 of 15 finalists. Built with team xMyst. "
    "My role: problem research, business case and the pitch."
)
c1, c2, c3 = st.columns(3)
c1.markdown("**See**  \nWindow mounted counters count pedestrians on the device, with no images stored.")
c2.markdown("**Understand**  \nA digital twin models street shade and forecasts crowds.")
c3.markdown("**Act**  \nCooler, quieter walking routes for workers, and fixes ranked by walkers helped per dollar for the council.")
st.link_button("Open full screen", URL)
components.iframe(URL, height=850, scrolling=True)
st.caption("If the prototype doesn't show here, use Open full screen.")
