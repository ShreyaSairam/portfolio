"""
WanderWise — destinations dataset.

There's no open, freely licensed "travel recommendation" dataset with the
attributes a recommender needs (climate, activity mix, budget tier,
season), so this is a hand-curated reference dataset of 50 well-known
global destinations, built from general, widely available travel
knowledge (climate zones, typical costs, what each place is known for).
Budget figures are rough indicative daily costs (accommodation + food +
local transport, mid-range travel) for orientation, not live pricing.

Run this once to generate destinations.csv:
    python build_destinations.py
"""

import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "destinations.csv")

# columns: name, country, region, climate, budget_level (1=budget,2=mid,3=luxury),
# avg_daily_cost_usd, best_season, activities (pipe-separated tags)
DESTINATIONS = [
    ("Bali", "Indonesia", "Southeast Asia", "Tropical", 1, 45, "Apr-Oct", "beach|nature|relaxation|culture"),
    ("Bangkok", "Thailand", "Southeast Asia", "Tropical", 1, 40, "Nov-Feb", "food|culture|nightlife|shopping"),
    ("Chiang Mai", "Thailand", "Southeast Asia", "Tropical", 1, 30, "Nov-Feb", "culture|nature|food|relaxation"),
    ("Hanoi", "Vietnam", "Southeast Asia", "Tropical", 1, 30, "Oct-Apr", "food|culture|history"),
    ("Ho Chi Minh City", "Vietnam", "Southeast Asia", "Tropical", 1, 30, "Dec-Apr", "food|culture|nightlife"),
    ("Siem Reap", "Cambodia", "Southeast Asia", "Tropical", 1, 35, "Nov-Feb", "history|culture|adventure"),
    ("Kuala Lumpur", "Malaysia", "Southeast Asia", "Tropical", 2, 45, "Dec-Feb", "food|shopping|culture|nightlife"),
    ("Singapore", "Singapore", "Southeast Asia", "Tropical", 3, 120, "Feb-Apr", "food|shopping|culture|nightlife"),
    ("Tokyo", "Japan", "East Asia", "Temperate", 3, 130, "Mar-May", "culture|food|shopping|nightlife"),
    ("Kyoto", "Japan", "East Asia", "Temperate", 2, 100, "Mar-May", "culture|history|nature"),
    ("Seoul", "South Korea", "East Asia", "Temperate", 2, 90, "Sep-Nov", "food|culture|nightlife|shopping"),
    ("Beijing", "China", "East Asia", "Temperate", 2, 70, "Sep-Nov", "history|culture"),
    ("Shanghai", "China", "East Asia", "Temperate", 2, 85, "Sep-Nov", "culture|shopping|nightlife"),
    ("Taipei", "Taiwan", "East Asia", "Temperate", 2, 70, "Oct-Dec", "food|culture|nature"),
    ("Bali Ubud", "Indonesia", "Southeast Asia", "Tropical", 1, 40, "Apr-Oct", "nature|relaxation|culture"),
    ("Queenstown", "New Zealand", "Oceania", "Temperate", 3, 140, "Dec-Feb", "adventure|nature"),
    ("Sydney", "Australia", "Oceania", "Temperate", 3, 150, "Sep-Nov", "beach|culture|nightlife|nature"),
    ("Melbourne", "Australia", "Oceania", "Temperate", 3, 140, "Mar-May", "food|culture|nightlife"),
    ("Fiji (Nadi)", "Fiji", "Oceania", "Tropical", 2, 90, "May-Oct", "beach|relaxation|adventure"),
    ("Reykjavik", "Iceland", "Northern Europe", "Cold", 3, 160, "Jun-Aug", "nature|adventure"),
    ("Oslo", "Norway", "Northern Europe", "Cold", 3, 170, "Jun-Aug", "nature|culture"),
    ("Stockholm", "Sweden", "Northern Europe", "Cold", 3, 150, "Jun-Aug", "culture|nightlife|nature"),
    ("Copenhagen", "Denmark", "Northern Europe", "Cold", 3, 160, "Jun-Aug", "culture|food|nightlife"),
    ("Amsterdam", "Netherlands", "Western Europe", "Temperate", 3, 140, "Apr-Sep", "culture|nightlife|history"),
    ("Paris", "France", "Western Europe", "Temperate", 3, 150, "Apr-Jun", "culture|history|food|shopping"),
    ("London", "United Kingdom", "Western Europe", "Temperate", 3, 160, "May-Sep", "culture|history|nightlife|shopping"),
    ("Berlin", "Germany", "Western Europe", "Temperate", 2, 100, "May-Sep", "history|culture|nightlife"),
    ("Barcelona", "Spain", "Southern Europe", "Mediterranean", 2, 110, "May-Jun", "beach|culture|food|nightlife"),
    ("Madrid", "Spain", "Southern Europe", "Mediterranean", 2, 100, "Apr-Jun", "culture|food|nightlife"),
    ("Rome", "Italy", "Southern Europe", "Mediterranean", 2, 120, "Apr-Jun", "history|culture|food"),
    ("Venice", "Italy", "Southern Europe", "Mediterranean", 3, 150, "Apr-Jun", "culture|history|relaxation"),
    ("Santorini", "Greece", "Southern Europe", "Mediterranean", 3, 140, "May-Sep", "beach|relaxation|culture"),
    ("Athens", "Greece", "Southern Europe", "Mediterranean", 2, 90, "Apr-Jun", "history|culture|food"),
    ("Lisbon", "Portugal", "Southern Europe", "Mediterranean", 2, 90, "Mar-May", "culture|food|beach|nightlife"),
    ("Prague", "Czech Republic", "Central Europe", "Temperate", 2, 80, "May-Sep", "history|culture|nightlife"),
    ("Vienna", "Austria", "Central Europe", "Temperate", 3, 130, "Apr-Jun", "culture|history"),
    ("Zurich", "Switzerland", "Central Europe", "Cold", 3, 200, "Jun-Sep", "nature|culture"),
    ("Interlaken", "Switzerland", "Central Europe", "Cold", 3, 180, "Jun-Sep", "adventure|nature"),
    ("Dubai", "UAE", "Middle East", "Arid", 3, 150, "Nov-Mar", "shopping|nightlife|adventure"),
    ("Istanbul", "Turkey", "Middle East", "Mediterranean", 2, 60, "Apr-May", "history|culture|food"),
    ("Marrakech", "Morocco", "North Africa", "Arid", 1, 50, "Mar-May", "culture|history|adventure"),
    ("Cape Town", "South Africa", "Southern Africa", "Mediterranean", 2, 70, "Nov-Mar", "nature|adventure|beach|food"),
    ("Nairobi", "Kenya", "East Africa", "Tropical", 2, 80, "Jun-Oct", "wildlife|adventure|nature"),
    ("Cairo", "Egypt", "North Africa", "Arid", 1, 45, "Oct-Apr", "history|culture"),
    ("New York City", "United States", "North America", "Temperate", 3, 180, "Apr-Jun", "culture|nightlife|shopping|food"),
    ("San Francisco", "United States", "North America", "Temperate", 3, 170, "Sep-Nov", "culture|food|nature"),
    ("Cancun", "Mexico", "North America", "Tropical", 2, 90, "Dec-Apr", "beach|relaxation|nightlife"),
    ("Rio de Janeiro", "Brazil", "South America", "Tropical", 2, 70, "Dec-Mar", "beach|nightlife|nature"),
    ("Buenos Aires", "Argentina", "South America", "Temperate", 1, 55, "Sep-Nov", "culture|food|nightlife"),
    ("Cusco", "Peru", "South America", "Temperate", 1, 40, "May-Sep", "history|adventure|culture"),
    ("Banff", "Canada", "North America", "Cold", 3, 150, "Jun-Sep", "nature|adventure"),
]

# Approximate city-centre coordinates (latitude, longitude), used for live
# weather lookups and distance from the traveller's location.
COORDS = {
    "Bali": (-8.65, 115.22), "Bangkok": (13.76, 100.50), "Chiang Mai": (18.79, 98.98),
    "Hanoi": (21.03, 105.85), "Ho Chi Minh City": (10.82, 106.63), "Siem Reap": (13.36, 103.86),
    "Kuala Lumpur": (3.14, 101.69), "Singapore": (1.35, 103.82), "Tokyo": (35.68, 139.69),
    "Kyoto": (35.01, 135.77), "Seoul": (37.57, 126.98), "Beijing": (39.90, 116.40),
    "Shanghai": (31.23, 121.47), "Taipei": (25.03, 121.57), "Bali Ubud": (-8.51, 115.26),
    "Queenstown": (-45.03, 168.66), "Sydney": (-33.87, 151.21), "Melbourne": (-37.81, 144.96),
    "Fiji (Nadi)": (-17.80, 177.42), "Reykjavik": (64.15, -21.94), "Oslo": (59.91, 10.75),
    "Stockholm": (59.33, 18.07), "Copenhagen": (55.68, 12.57), "Amsterdam": (52.37, 4.90),
    "Paris": (48.86, 2.35), "London": (51.51, -0.13), "Berlin": (52.52, 13.40),
    "Barcelona": (41.39, 2.17), "Madrid": (40.42, -3.70), "Rome": (41.90, 12.50),
    "Venice": (45.44, 12.32), "Santorini": (36.39, 25.46), "Athens": (37.98, 23.73),
    "Lisbon": (38.72, -9.14), "Prague": (50.08, 14.44), "Vienna": (48.21, 16.37),
    "Zurich": (47.38, 8.54), "Interlaken": (46.69, 7.86), "Dubai": (25.20, 55.27),
    "Istanbul": (41.01, 28.98), "Marrakech": (31.63, -8.01), "Cape Town": (-33.92, 18.42),
    "Nairobi": (-1.29, 36.82), "Cairo": (30.04, 31.24), "New York City": (40.71, -74.01),
    "San Francisco": (37.77, -122.42), "Cancun": (21.16, -86.85), "Rio de Janeiro": (-22.91, -43.17),
    "Buenos Aires": (-34.60, -58.38), "Cusco": (-13.53, -71.97), "Banff": (51.18, -115.57),
}


def main():
    with open(OUT_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "name",
                "country",
                "region",
                "climate",
                "budget_level",
                "avg_daily_cost_usd",
                "best_season",
                "activities",
                "lat",
                "lon",
            ]
        )
        writer.writerows(row + COORDS[row[0]] for row in DESTINATIONS)
    print(f"Wrote {len(DESTINATIONS)} destinations to {OUT_PATH}")


if __name__ == "__main__":
    main()
