import requests
from datetime import date
import json

# CONFIG - set your team info here
TEAM_NAME = "Minnesota Timberwolves"
LEMMY_INSTANCE = "https://midwest.social"
COMMUNITY_ID = 12345  # <-- We'll replace this below
import os
USERNAME = os.environ.get("USERNAME")
PASSWORD = os.environ.get("PASSWORD")

def get_team_id():
    response = requests.get("https://www.balldontlie.io/api/v1/teams")
    teams = response.json()["data"]
    for team in teams:
        if team["full_name"] == TEAM_NAME:
            return team["id"]
    return None

def get_latest_game(team_id):
    today = date.today()
    url = f"https://www.balldontlie.io/api/v1/games?team_ids[]={team_id}&per_page=1&end_date={today}"
    response = requests.get(url)
    games = response.json()["data"]
    return games[0] if games else None

def get_community_id(auth_headers):
    resp = requests.get(f"{LEMMY_INSTANCE}/api/v3/community?name=timberwolves@lemmy.world", headers=auth_headers)
    return resp.json()["community_view"]["community"]["id"]

def post_to_lemmy(title, body):
    # Log in
    login_resp = requests.post(f"{LEMMY_INSTANCE}/api/v3/user/login", json={
        "username_or_email": USERNAME,
        "password": PASSWORD
    })
    jwt = login_resp.json()["jwt"]
    auth_headers = {"Authorization": f"Bearer {jwt}"}

    # Get community ID if needed
    global COMMUNITY_ID
    if COMMUNITY_ID == 12345:
        COMMUNITY_ID = get_community_id(auth_headers)

    # Post
    post_data = {
        "name": title,
        "body": body,
        "community_id": COMMUNITY_ID
    }
    response = requests.post(f"{LEMMY_INSTANCE}/api/v3/post", headers=auth_headers, json=post_data)
    print("Posted:", response.status_code, response.text)

def main():
    team_id = get_team_id()
    game = get_latest_game(team_id)

    if not game or not game["status"].startswith("Final"):
        print("No completed game found.")
        return

    home = game["home_team"]["full_name"]
    away = game["visitor_team"]["full_name"]
    home_score = game["home_team_score"]
    away_score = game["visitor_team_score"]

    title = f"Final: {away} {away_score} - {home_score} {home}"
    body = f"Game finished on {game['date'][:10]}\n\nFinal score:\n\n{away}: {away_score}\n{home}: {home_score}"
    post_to_lemmy(title, body)

main()
