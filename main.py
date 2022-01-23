"""
Project Name: Cricket Prediction
Project Moto: To predict the upcoming match result and player performance (Machine Learning)
Project Description:
"""
import re
import time
from bs4 import BeautifulSoup

import requests

# Global Variable
# global bothSquadDetails, totalPlayers

bothSquadDetails = {}
sleepTime = 1
totalPlayers = 0


def getBothSquadIds():
    """
    1. convert match url into squads url.
    2. Using BeautifulSoup extract html text and separate player id's from players url
    :return: List of all player ids in both teams
    """
    match_squad_link = matchUrl.replace("live-cricket-score", "match-squads")

    html_text = requests.get(match_squad_link, time.sleep(sleepTime)).text
    soup = BeautifulSoup(html_text, "lxml")

    table_data = soup.find_all("tbody")
    data = table_data[0].find_all('a', href=True)
    both_squad_ids = re.findall("[0-9][0-9][0-9]+", str(data))

    return both_squad_ids


def getPlayerDetails(player_id):
    """
    1. Get Player API link
    2. download player details in json format
    3. extract required details from json file
    4. Add all the player details on to the global variable bothSquadDetails
    :param player_id: int
    :return: None
    """
    global bothSquadDetails, totalPlayers
    print(f"{totalPlayers} players to download")

    # 1. Get Player API link
    player_api = f"http://core.espnuk.org/v2/sports/cricket/athletes/{player_id}"

    # 2. download player details in json format
    player_details = requests.get(player_api, time.sleep(sleepTime))
    player_details = player_details.json()

    # 3A. extract required details from json file
    details = {
        "name": player_details["name"],
        "id": player_details["id"],
        "age": player_details["age"],
        "position": player_details["position"]["name"],
        "url": player_details["links"][0]["href"],
        "playing_11_status": False,
        "recent_form": 0,
        "class_form": 0,
        "int_form": 0,
        "experts_choice": 0,
        "prediction": 0
    }
    # 3B. Extract player style separately because all the players doesn't have batting style and bowling style.
    for style in player_details["style"]:
        if style["type"] == "batting":
            details["bat_style"] = style["description"]
        else:
            details["ball_style"] = style["description"]

    # 4. Add all the player details on to the global variable bothSquadDetails
    bothSquadDetails[player_details["name"]] = details

    totalPlayers -= 1
    pass


def getBothSquadDetails():
    """

    :return:
    """
    global bothSquadDetails, totalPlayers

    both_squad_ids = getBothSquadIds()
    totalPlayers = len(both_squad_ids)
    for player_id in both_squad_ids:
        getPlayerDetails(player_id)
    pass


def preMatchPreparation():
    """
    Extract Squad Details
    Extract each player’s recent matches record
    Extract each player’s international match records
        Batting (Based on Match Type)
        Bowling (Based on Match Type)
    Calculate Pre Match Statistics.
    :return: None
    """
    getBothSquadDetails()
    pass


if __name__ == '__main__':
    # matchUrl = input("Enter the ESPNCricInfo match URL: ")
    matchUrl = "https://www.espncricinfo.com/series/pakistan-super-league-2021-22-1292999/karachi-kings-vs-multan-sultans-1st-match-1293000/live-cricket-score"
    # vpnStatus = input("Are you using VPN?(y/n) ")
    # if vpnStatus == "y":
    #     sleepTime = 0

    preMatchPreparation()
