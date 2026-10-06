"""
WanderWise — AI travel recommender.

  * Hybrid recommender (recommender.py): content-based matching on your
    preferences, blended with collaborative filtering from traveller ratings.
  * Live weather for where you are and for every match (Open-Meteo, no key).
  * Your location from the browser (GPS), or a city you pick, for distance
    and flying time.
  * A chat panel about any match, answered by Gemini when a GOOGLE_API_KEY
    is set, or from the trip facts when it isn't.
  * Accounts and saved destinations in SQLite (ww_db.py).
"""

from concurrent.futures import ThreadPoolExecutor

import plotly.express as px
import streamlit as st

import ww_db
import ww_services as svc
from recommender import ALL_ACTIVITIES, ALL_CLIMATES, get_recommendations, load_destinations


@st.cache_data(ttl=900, show_spinner=False)
def weather(lat, lon):
    return svc.get_weather(lat, lon)


def weather_many(points):
    with ThreadPoolExecutor(max_workers=8) as pool:
        return list(pool.map(lambda p: weather(*p), points))


# ---------------------------------------------------------------- account
def account_box():
    st.sidebar.header("Your account")
    user = st.session_state.get("ww_user")
    if user:
        st.sidebar.success(f"Signed in as **{user['name']}**")
        if st.sidebar.button("Sign out", key="ww_signout"):
            st.session_state.pop("ww_user")
            st.rerun()
        return
    mode = st.sidebar.radio("Account", ["Sign in", "Create account"], horizontal=True,
                            label_visibility="collapsed", key="ww_mode")
    with st.sidebar.form("ww_auth", clear_on_submit=False):
        name = st.text_input("Username", key="ww_username")
        pw = st.text_input("Password", type="password", key="ww_password")
        go = st.form_submit_button(mode)
    if go:
        if mode == "Create account":
            ok, msg = ww_db.create_user(name, pw)
            if not ok:
                st.sidebar.error(msg)
                return
        uid = ww_db.check_login(name, pw)
        if uid:
            st.session_state.ww_user = {"id": uid, "name": name.strip().lower()}
            st.rerun()
        else:
            st.sidebar.error("That username and password don't match.")
    st.sidebar.caption("Sign in to save destinations. Browsing works without an account.")


# ---------------------------------------------------------------- location
def location_box():
    st.subheader("Where are you now?")
    c1, c2 = st.columns([1, 2])
    use_gps = c1.toggle("Use my location", key="ww_gps",
                        help="Your browser asks permission first. Nothing is stored.")
    origin, origin_name = None, None
    if use_gps:
        try:
            from streamlit_js_eval import get_geolocation

            loc = get_geolocation()
            if loc and "coords" in loc:
                origin = (loc["coords"]["latitude"], loc["coords"]["longitude"])
                origin_name = "your location"
            else:
                c2.caption("Waiting for location permission. Using the city below for now.")
        except Exception:
            c2.caption("Location isn't available in this browser. Using the city below.")
    city = c2.selectbox("Or pick a city", list(svc.CITIES), key="ww_city")
    if origin is None:
        origin, origin_name = svc.CITIES[city], city

    w = weather(*origin)
    if w:
        m = st.columns(4)
        m[0].metric(f"Now in {origin_name}", f"{w['temp']:.0f}°C", w["summary"], delta_color="off")
        m[1].metric("Feels like", f"{w['feels']:.0f}°C")
        m[2].metric("Humidity", f"{w['humidity']:.0f}%")
        m[3].metric("Wind", f"{w['wind']:.0f} km/h")
    else:
        st.info("Live weather isn't reachable right now, so weather panels are hidden. Recommendations still work.")
    return origin, origin_name


# ---------------------------------------------------------------- chat
def chat_panel(recs, origin, origin_name, weathers):
    st.subheader("Ask about a destination")
    names = recs["name"].tolist()
    pick = st.selectbox("Destination", names, key="ww_chat_dest")
    i = names.index(pick)
    dest = recs.iloc[i]
    km = svc.distance_km(origin, (dest["lat"], dest["lon"]))
    context = svc.trip_context(dest, weathers[i], origin_name, km)

    key = f"ww_chat_{pick}"
    history = st.session_state.setdefault(key, [])
    for m in history:
        with st.chat_message(m["role"]):
            st.write(m["content"])
            if m.get("note"):
                st.caption(m["note"])

    live = bool(svc.gemini_key())
    st.caption("Answers come from Gemini." if live else
               "Offline mode: answers are built from the trip facts. Add a GOOGLE_API_KEY to get Gemini answers.")
    question = st.chat_input(f"e.g. What should I pack for {pick}?", key="ww_chat_input")
    if question:
        history.append({"role": "user", "content": question})
        with st.spinner("Thinking"):
            answer, was_live = svc.ask_gemini(question, context, history)
        history.append({"role": "assistant", "content": answer,
                        "note": "" if was_live else "Offline answer from trip facts"})
        st.rerun()


def main():
    st.set_page_config(page_title="WanderWise", layout="wide")
    st.title("WanderWise: AI Travel Recommender")
    st.caption(
        "A hybrid recommender over 51 destinations, with live weather, your location, "
        "a chat assistant and saved favourites."
    )

    dest_df = load_destinations()
    account_box()
    user = st.session_state.get("ww_user")

    with st.sidebar:
        st.header("Your preferences")
        activities = st.multiselect("What do you want to do?", ALL_ACTIVITIES,
                                    default=["beach", "relaxation"], key="ww_acts")
        climate = st.selectbox("Preferred climate", ALL_CLIMATES, key="ww_climate")
        budget_label = st.select_slider("Budget", options=["Budget", "Mid-range", "Luxury"],
                                        value="Mid-range", key="ww_budget")
        liked = st.multiselect("Places you've enjoyed before (powers 'travellers like you')",
                               sorted(dest_df["name"].tolist()), key="ww_liked")
        collab_weight = st.slider("Weight on 'travellers like you also liked'", 0.0, 1.0, 0.35, 0.05,
                                  key="ww_cw")
        top_n = st.slider("Number of recommendations", 3, 12, 6, key="ww_topn")

    origin, origin_name = location_box()
    st.divider()

    if not activities:
        st.warning("Pick at least one activity in the sidebar.")
        return

    recs = get_recommendations(
        activities=activities, climate=climate,
        budget_level={"Budget": 1, "Mid-range": 2, "Luxury": 3}[budget_label],
        liked_destinations=liked, top_n=top_n, collab_weight=collab_weight,
    )
    weathers = weather_many(list(zip(recs["lat"], recs["lon"])))
    saved = set(ww_db.favourites(user["id"])["destination"]) if user else set()

    left, right = st.columns([3, 2])
    with left:
        st.subheader(f"Your top {len(recs)} matches")
        for i, row in recs.iterrows():
            km = svc.distance_km(origin, (row["lat"], row["lon"]))
            w = weathers[i]
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"#### {row['name']}, {row['country']}")
                    st.write(f"{row['region']} · {row['climate']} · best {row['best_season']} · "
                             f"about ${row['avg_daily_cost_usd']}/day")
                    st.write(f"**Things to do:** {row['activities'].replace('|', ', ')}")
                    st.caption(f"{km:,.0f} km from {origin_name}, about {svc.flight_hours(km):.0f} h flying")
                    if w:
                        st.caption("Weather now: " + f"**{w['temp']:.0f}°C, {w['summary'].lower()}** · next days: "
                                   + ", ".join(f"{d['max']:.0f}°/{d['min']:.0f}°" for d in w["days"]))
                with c2:
                    st.metric("Match", f"{row['match_score'] * 100:.0f}%")
                    st.caption(f"content {row['content_score']:.2f} · travellers {row['collab_score']:.2f}")
                    if user:
                        is_saved = row["name"] in saved
                        if st.button("Saved ✓" if is_saved else "Save", key=f"ww_save_{row['name']}"):
                            ww_db.toggle_favourite(user["id"], row["name"])
                            st.rerun()
    with right:
        chat_panel(recs, origin, origin_name, weathers)
        if user:
            st.subheader("Your saved destinations")
            fav = ww_db.favourites(user["id"])
            if fav.empty:
                st.caption("Nothing saved yet. Press Save on a match.")
            else:
                st.dataframe(fav, hide_index=True, width="stretch")

    with st.expander("Match score breakdown"):
        fig = px.bar(recs.sort_values("match_score"), x="match_score", y="name", orientation="h",
                     color="region", labels={"match_score": "Match score", "name": "Destination"})
        st.plotly_chart(fig, width="stretch")
    with st.expander("How the recommender works"):
        st.markdown(
            """
**Content-based:** each destination becomes a vector of its activities, climate and budget.
Your preferences become the same kind of vector, and cosine similarity scores how close they are.

**Collaborative filtering:** destinations are compared by how the same travellers rated them
(item-item cosine similarity). Places similar to ones you've enjoyed get a boost.

**Blend:** the final match is a weighted mix of the two, set by the slider in the sidebar.
The traveller ratings are simulated (see data/build_ratings.py) because real ones aren't openly available.
"""
        )


if __name__ == "__main__":
    main()
