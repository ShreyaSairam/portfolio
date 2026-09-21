"""
Display-name roster for the AT&T faces subjects (s1..s40).

The AT&T/ORL dataset doesn't ship real names (subjects are anonymised),
so this maps each subject id to a placeholder employee name/department
purely for the attendance-system demo UI. Edit ROSTER to rename people
or swap in your own enrolled faces (see enroll.py).
"""

DEPARTMENTS = [
    "Engineering", "Operations", "Finance", "Product",
    "Marketing", "HR", "Sales", "Support",
]

FIRST_NAMES = [
    "Alex", "Priya", "Jordan", "Wei", "Sam", "Maria", "Ken", "Nina",
    "Omar", "Grace", "Liam", "Aisha", "Noah", "Yuki", "Ivan", "Zoe",
    "Leo", "Mei", "Ravi", "Elena", "Tom", "Sofia", "Ben", "Anya",
    "Carlos", "Mia", "David", "Hana", "Eli", "Lucia", "Max", "Nadia",
    "Owen", "Priti", "Quinn", "Rosa", "Sam2", "Tara", "Umar", "Vera",
]


def build_roster():
    roster = {}
    for i in range(1, 41):
        name = FIRST_NAMES[i - 1]
        dept = DEPARTMENTS[(i - 1) % len(DEPARTMENTS)]
        roster[i] = {"name": f"{name} (ID {i:02d})", "department": dept}
    return roster


ROSTER = build_roster()
