import os
import requests
from datetime import datetime
import time

# Basic info
TEAM_NAME = "Timberwolves"
TEAM_ABBREV = "MIN"
COMMUNITY_NAME = "timberwolves@lemmy.world"
COMMUNITY_INSTANCE = "midwest.social"

# Get secrets from GitHub
username = os.environ["USERNAME"]
password = os.environ["PASSWORD"]
api_key = os.environ["BALLDONTLIE_API_KEY"]

# API headers
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

def get_latest_game(team_id):
    today = datetime.today().strftime("%Y-%m-%d")
    url = f"https://www.balldontlie.io/api/v1/games?team_ids[]={team_id}&end_date={today}&per_page=1&sort=-date"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    resp = requests.get(url, headers=headers)
    
    try:
        data = resp.json()["data"]
        if not data:
            raise Exception("No game data returned. Maybe the team hasn't played recently?")
        return data[0]
    except Exception as e:
        raise Exception(f"Failed to get latest game. Raw response: {resp.text}") from e

def get_latest_game(team_id):
    today = datetime.today().strftime("%Y-%m-%d")
    url = f"https://www.balldontlie.io/api/v1/games?team_ids[]={team_id}&end_date={today}&per_page=1&sort=-date"
    
    print("Game API URL:", url)

    resp = requests.get(url)
    
    # Check if the request was successful
    if resp.status_code != 200:
        raise Exception(f"Failed request: {resp.status_code}. Response: {resp.text}")
    
    # Log the raw response for debugging
    print("Raw response from API:", resp.text)
    
    try:
        data = resp.json()["data"]
        if not data:
            raise Exception("No game data returned. Maybe the team hasn't played recently?")
        return data[0]
    except Exception as e:
        raise Exception(f"Failed to get latest game. Raw response: {resp.text}") from e


def get_box_score(game_id):
    player_stats = []
    page = 1

    while True:
        url = f"https://www.balldontlie.io/api/v1/stats?game_ids[]={game_id}&per_page=100&page={page}"
        resp = requests.get(url)
        data = resp.json()
        player_stats += data["data"]

        if data["meta"]["next_page"] is None:
            break
        page += 1

    return player_stats


def format_team_box_score(stats, team_abbrev):
    table = f"### {team_abbrev} Box Score\n\n"
    table += "| Player | PTS | REB | AST | STL | BLK | FG% |\n"
    table += "|--------|-----|-----|-----|-----|-----|------|\n"

    for stat in stats:
        if stat["team"]["abbreviation"] != team_abbrev:
            continue

        player = f"{stat['player']['first_name']} {stat['player']['last_name']}"
        pts = stat["pts"]
        reb = stat["reb"]
        ast = stat["ast"]
        stl = stat["stl"]
        blk = stat["blk"]
        fga = stat["fga"]
        fgm = stat["fgm"]
        fg_pct = round((fgm / fga) * 100, 1) if fga else 0

        table += f"| {player} | {pts} | {reb} | {ast} | {stl} | {blk} | {fg_pct}% |\n"

    return table


try:
    print("🔐 Logging in...")

    # Login to Lemmy
    login_resp = requests.post(f"https://{COMMUNITY_INSTANCE}/api/v3/user/login", json={
    "username_or_email": username,
    "password": password
}, headers=HEADERS)
    
    login_data = login_resp.json()
    jwt = login_data["jwt"]

    print("Login response:", login_resp.text)  # <-- log raw text response for easier debugging
    
    login_data = login_resp.json()
    if "jwt" not in login_data:
        raise Exception(f"Login failed! Response: {login_data}")
    jwt = login_data["jwt"]

    print("✅ Logged in!")

    # Get community ID
    print("🔍 Looking up community...")
    community_lookup = requests.get(
        f"https://{COMMUNITY_INSTANCE}/api/v3/community",
        params={"name": COMMUNITY_NAME}
    )
    community_data = community_lookup.json()
    community_id = community_data["community_view"]["community"]["id"]

    print(f"✅ Community ID: {community_id}")

    # Get team info
    print("📡 Fetching latest game info...")
    team_resp = requests.get("https://www.balldontlie.io/api/v1/teams")

    print("🧪 Team API response text:", team_resp.text)
    
    teams = team_resp.json()["data"]
    team_id = next(t["id"] for t in teams if t["abbreviation"] == TEAM_ABBREV)

    game = get_latest_game(team_id)
    game_id = game["id"]
    home_team = game["home_team"]
    visitor_team = game["visitor_team"]

    home_score = game["home_team_score"]
    visitor_score = game["visitor_team_score"]

    if home_team["abbreviation"] == TEAM_ABBREV:
        opponent_abbrev = visitor_team["abbreviation"]
        team_score = home_score
        opponent_score = visitor_score
    else:
        opponent_abbrev = home_team["abbreviation"]
        team_score = visitor_score
        opponent_score = home_score

    title = f"Final: {TEAM_ABBREV} {team_score}, {opponent_abbrev} {opponent_score}"

    print("📊 Fetching box scores...")
    stats = get_box_score(game_id)
    wolves_table = format_team_box_score(stats, TEAM_ABBREV)
    opponent_table = format_team_box_score(stats, opponent_abbrev)

    body_text = f"""\
**Final Score**  
**{TEAM_ABBREV}** {team_score}  
**{opponent_abbrev}** {opponent_score}

---

{wolves_table}

---

{opponent_table}

---

_This post was generated by eastern_bot_wolf 🐺_
"""

    print("📬 Posting to Lemmy...")
    post_resp = requests.post(
        f"https://{COMMUNITY_INSTANCE}/api/v3/post",
        headers={"Authorization": f"Bearer {jwt}"},
        json={
            "name": title,
            "community_id": community_id,
            "body": body_text,
        }
    )

    if post_resp.status_code == 200:
        print("✅ Post published successfully!")
    else:
        print(f"❌ Post failed with status code {post_resp.status_code}")
        print(post_resp.text)

except Exception as e:
    print("❗ An error occurred:")
    print(e)
