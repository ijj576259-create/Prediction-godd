
import json
import glob
import os
import csv

FILES = sorted(glob.glob("football-data/2025-26/*.json"))


def all_teams_list():
    teams = {}

    for file in FILES:
        league = os.path.basename(file).replace(".json", "")

        with open(file) as f:
            data = json.load(f)

        for m in data.get("matches", []):
            for name in [m["team1"], m["team2"]]:
                teams.setdefault(name, set()).add(league)

    print("\n⚽ ALL TEAMS - ONE LIST")
    print("========================")

    for i, name in enumerate(sorted(teams), 1):
        leagues = ", ".join(sorted(teams[name]))
        print(f"{i}. {name} [{leagues}]")

    print("\nTotal unique teams:", len(teams))


def load_league():
    print("\n🌍 SELECT LEAGUE")

    for i, file in enumerate(FILES, 1):
        print(f"{i}. {os.path.basename(file)}")

    try:
        n = int(input("\nLeague number: "))
        if not 1 <= n <= len(FILES):
            return None
    except ValueError:
        return None

    with open(FILES[n - 1]) as f:
        data = json.load(f)

    matches = []

    for m in data.get("matches", []):
        score = m.get("score")

        if isinstance(score, dict):
            score = score.get("ft")

        if not isinstance(score, list) or len(score) < 2:
            continue

        if score[0] is None or score[1] is None:
            continue

        matches.append({
            "date": m.get("date", ""),
            "home": m["team1"],
            "away": m["team2"],
            "hg": score[0],
            "ag": score[1]
        })

    return matches, os.path.basename(FILES[n - 1])


def load_all_matches():
    matches = []

    for file in FILES:
        with open(file) as f:
            data = json.load(f)

        for m in data.get("matches", []):
            score = m.get("score")

            if isinstance(score, dict):
                score = score.get("ft")

            if not isinstance(score, list) or len(score) < 2:
                continue

            if score[0] is None or score[1] is None:
                continue

            matches.append({
                "date": m.get("date", ""),
                "home": m["team1"],
                "away": m["team2"],
                "hg": score[0],
                "ag": score[1]
            })

    return matches


def build_teams(matches):
    teams = {}

    for m in matches:
        for name in [m["home"], m["away"]]:
            if name not in teams:
                teams[name] = {
                    "played": 0,
                    "points": 0,
                    "gf": 0,
                    "ga": 0
                }

        h = teams[m["home"]]
        a = teams[m["away"]]

        h["played"] += 1
        a["played"] += 1

        h["gf"] += m["hg"]
        h["ga"] += m["ag"]

        a["gf"] += m["ag"]
        a["ga"] += m["hg"]

        if m["hg"] > m["ag"]:
            h["points"] += 3
        elif m["ag"] > m["hg"]:
            a["points"] += 3
        else:
            h["points"] += 1
            a["points"] += 1

    return teams


def choose_teams(teams):
    print("\n===== AVAILABLE TEAMS =====")

    for name in sorted(teams):
        print("-", name)

    first = input("\nHome Team: ").strip().lower()
    second = input("Away Team: ").strip().lower()

    home = next((t for t in teams if t.lower() == first), None)
    away = next((t for t in teams if t.lower() == second), None)

    if not home or not away or home == away:
        print("\nInvalid team selection!")
        return None

    return home, away


def total_corner_estimate(home, away):
    aliases = {
        "AC Milan": "Milan",
        "AC Monza": "Monza"
    }

    corner_home = aliases.get(home, home)
    corner_away = aliases.get(away, away)

    team_corners = {
        corner_home: [],
        corner_away: []
    }

    files = glob.glob(
        os.path.expanduser(
            "~/open-matchday/data/*/results_2627.csv"
        )
    )

    for file in files:
        with open(file, newline="") as f:
            for row in csv.DictReader(f):
                h = row.get("home_corners", "")
                a = row.get("away_corners", "")

                if not h or not a:
                    continue

                try:
                    total = int(h) + int(a)
                except ValueError:
                    continue

                if row["home"] == corner_home or row["away"] == corner_home:
                    team_corners[corner_home].append(total)

                if row["home"] == corner_away or row["away"] == corner_away:
                    team_corners[corner_away].append(total)

    values = (
        team_corners[corner_home]
        + team_corners[corner_away]
    )

    if not values:
        return None

    return round(sum(values) / len(values), 1)


def prediction(teams, home, away):
    h = teams[home]
    a = teams[away]

    hs = round((
        h["gf"] / h["played"] +
        a["ga"] / a["played"]
    ) / 2, 1)

    aws = round((
        a["gf"] / a["played"] +
        h["ga"] / h["played"]
    ) / 2, 1)

    print("\n===== MATCH PREDICTION =====")
    print(home, "VS", away)
    print(home, hs)
    print(away, aws)

    corners = total_corner_estimate(home, away)

    print("\n===== CORNER ANALYSIS =====")

    if corners is not None:
        print("Historical Average Total Corners:", corners)
    else:
        print("Corner data not available")

    print("\nHistorical analysis only.")


def last_five(matches, home, away):
    print("\n===== LAST 5 MATCHES =====")

    for team in [home, away]:
        recent = [
            m for m in matches
            if m["home"] == team or m["away"] == team
        ]

        recent.sort(key=lambda x: x["date"])

        print("\n", team)

        for m in recent[-5:]:
            if m["home"] == team:
                gf, ga = m["hg"], m["ag"]
                opponent = m["away"]
            else:
                gf, ga = m["ag"], m["hg"]
                opponent = m["home"]

            result = "W" if gf > ga else "D" if gf == ga else "L"

            print(m["date"], opponent, gf, "-", ga, result)


def wdl(teams, home, away):
    h = teams[home]
    a = teams[away]

    hr = h["points"] / (h["played"] * 3)
    ar = a["points"] / (a["played"] * 3)

    hs = (hr + 1 - ar) / 2
    aws = (ar + 1 - hr) / 2
    ds = max(0.05, 1 - abs(hs - aws))

    total = hs + aws + ds

    print("\n===== W/D/L ANALYSIS =====")
    print("Historical home-win score:", round(hs / total * 100, 1), "%")
    print("Historical draw score:", round(ds / total * 100, 1), "%")
    print("Historical away-win score:", round(aws / total * 100, 1), "%")
    print("These are not validated probabilities.")


def main():
    while True:
        os.system("clear")

        print("""
================================
       ⚽ PREDICTION GOD
================================
       ALL-IN-ONE V2
================================

1. Match Prediction
2. Last 5 Matches
3. Win / Draw / Loss
4. All Leagues
5. Exit
6. All Teams - One List

================================
""")

        choice = input("Choose Feature: ").strip()

        if choice == "5":
            print("Thank you for using Prediction God!")
            break

        if choice == "4":
            print("\n===== ALL LEAGUES =====")
            for file in FILES:
                print(os.path.basename(file))
            input("\nPress ENTER...")
            continue

        if choice == "6":
            all_teams_list()
            input("\nPress ENTER...")
            continue

        if choice not in ["1", "2", "3"]:
            print("Invalid choice!")
            input("Press ENTER...")
            continue

        if choice == "1":
            matches = load_all_matches()
        else:
            loaded = load_league()

            if loaded is None:
                print("Invalid league!")
                input("Press ENTER...")
                continue

            matches, league = loaded
            print("\nLeague:", league)

        teams = build_teams(matches)
        selected = choose_teams(teams)

        if selected is None:
            input("\nPress ENTER...")
            continue

        home, away = selected

        if choice == "1":
            prediction(teams, home, away)
        elif choice == "2":
            last_five(matches, home, away)
        elif choice == "3":
            wdl(teams, home, away)

        input("\nPress ENTER to return to menu...")


if __name__ == "__main__":
    main()
