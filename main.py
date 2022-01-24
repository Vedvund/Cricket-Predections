"""
Project Name: Cricket Prediction
Project Moto: To predict the upcoming match result and player performance (Machine Learning)
Project Description:
"""
import json
import os
import re
import time

import pandas as pd
from bs4 import BeautifulSoup

import requests

# Global Variable
# global bothSquadDetails
from espncricinfo.match import Match

bothSquadDetails = {}
sleepTime = 1
totalPlayers = 0
pagesLeft = 0


def getBothSquadIds() -> list:
    """
    1. convert match url into squads url.
    2. Using BeautifulSoup extract html text and separate player id's from players url
    :return: List of all player ids in both teams
    """

    # 1. convert match url into squads url.
    match_squad_link = matchUrl.replace("live-cricket-score", "match-squads")

    # 2. Using BeautifulSoup extract html text and separate player id's from players url
    html_text = requests.get(match_squad_link, time.sleep(sleepTime)).text
    soup = BeautifulSoup(html_text, "lxml")

    table_data = soup.find_all("tbody")
    data = table_data[0].find_all('a', href=True)
    both_squad_ids = re.findall("[0-9][0-9][0-9]+", str(data))

    return both_squad_ids


def getPlayerDetails(player_id) -> None:
    """
    1. Get Player API link
    2. download player details in json format
    3. extract required details from json file
    4. Add all the player details on to the global variable squadDetails
    :param player_id: int
    :return: None
    """
    global bothSquadDetails, totalPlayers, names2Ids
    print(f"{totalPlayers} players to download")

    # 1. Get Player API link
    player_api = f"http://core.espnuk.org/v2/sports/cricket/athletes/{player_id}"

    # 2. download player details in json format
    player_details = requests.get(player_api, time.sleep(sleepTime))
    player_details = player_details.json()

    # 3A. extract required details from json file
    details = {
        "NAME": player_details["name"],
        "ID": player_details["id"],
        "AGE": player_details["age"],
        "POSITION": player_details["position"]["name"],
        "URL": player_details["links"][0]["href"],
        "PLAYING_11_STATUS": False,
        "RECENT_FORM": 0,
        "MATCH_CLASS_FORM": 0,
        "INTERNATIONAL_FORM": 0,
        "EXPERTS_CHOICE": 0,
        "PREDICTION": 0
    }
    # 3B. Extract player style separately because all the players doesn't have batting style and bowling style.
    for style in player_details["style"]:
        if style["type"] == "batting":
            details["BAT_STYLE"] = style["description"]
        else:
            details["BALL_STYLE"] = style["description"]

    # 4. Add all the player details on to the global variable squadDetails
    bothSquadDetails[player_id] = details
    totalPlayers -= 1
    pass


def getMatchId(match_url) -> int:
    """
    1. Extracts match id from match url
    :param match_url: String --> Match URL
    :return: Int --> Match ID
    """
    ids = re.findall("[0-9]+", match_url)
    return ids[len(ids) - 1]


def fileExists(file_name, folder_path) -> bool:
    """
    1. Checks if the file exists in the folder
    :param file_name: String --> File name
    :param folder_path: String --> Destination File
    :return: Boolean --> If it exists or not 
    """
    all_squad_files = os.listdir(folder_path)
    if file_name in all_squad_files:
        return True
    return False


def getBothSquadDetails() -> None:
    """
    1. Extract both squad ids
    2. Extract each player details from their ids and add them to the global variable squadDetails
    3. Save the squad details into a json file

    :return:None
    """
    global totalPlayers, bothSquadDetails

    # Check of the json file already exists
    match_id = getMatchId(matchUrl)
    file_name = str(match_id) + ".json"
    folder_path = "DataBase/squadDetails"
    file_path = folder_path + "/" + file_name
    if fileExists(file_name, folder_path):
        with open(file_path) as json_file:
            bothSquadDetails = json.load(json_file)
        return None

    # 1. Extract both squad ids
    both_squad_ids = getBothSquadIds()
    totalPlayers = len(both_squad_ids)

    # 2. Extract each player details from their ids and add them to the global variable squadDetails
    for player_id in both_squad_ids:
        getPlayerDetails(player_id)

    # 3. Save the squad details into a json file
    with open(file_path, 'w') as json_file:
        json.dump(bothSquadDetails, json_file)

    pass


def getPlayerMatchUrl(player_url) -> None or str:
    """
    1. Extract tab widgets from url
    2. check if the matches' page exists or not
    3. if exists then extract the url
    :param player_url: str --> player overview link
    :return: link or string
    """
    # 1. Extract tab widgets from url
    html_text = requests.get(player_url, time.sleep(sleepTime)).text
    soup = BeautifulSoup(html_text, "lxml")
    tab_widgets = soup.find_all("a", class_="widget-tab-link")

    # 2. check if the matches' page exists
    if len(tab_widgets) < 2:
        return None

    # 3. if exists then extract the url
    for i in range(len(tab_widgets)):
        page_url = soup.find_all("a", class_="widget-tab-link")[i]['href']
        if "matches" in page_url:
            return "https://www.espncricinfo.com" + page_url


def getRunsSimplified(runs) -> int:
    """
    convert runs extracted into int
    :param runs: str
    :return: int
    """
    if "*" in runs:
        runs = runs.replace("*", "")
    if "-" in runs:
        runs = runs.replace("-", "0")
    if "&" in runs:
        x = re.findall("[0-9]+", runs)
        runs = int(x[0]) + int(x[1])
    return runs


def getWicketsSimplified(wickets) -> int:
    """
    convert wickets extracted into int    
    :param wickets: str
    :return: int
    """
    if "*" in wickets:
        wickets = wickets.replace("*", "")
    if "-" in wickets:
        wickets = wickets.replace("-", "0")
    if "&" in wickets:
        x = re.findall("[0-9]+", wickets)
        wickets = int(x[0]) + int(x[2])
    else:
        wickets = wickets[0]
    return wickets


def getMatchClass(match_api) -> str:
    """
    Extract match class and simplify the class
    :param match_api: Dictionary
    :return: str
    """
    match_class = match_api.match_class

    classes_list = {"Twenty20": "T20", "Test": "Test", "First-class": "Test", "List A": "ODI", "ODI": "ODI",
                    "T20I": "T20", "Youth ODI": "ODI"}
    if match_class == "":
        return "Warm-up"
    return classes_list[match_class]


def getMatchTotalRunsAndWickets(match_api) -> [int, int]:
    """
    Extract all runs and wickets and get total runs and total wickets of that match
    :param match_api: Dictionary
    :return: int, int
    """
    innings = match_api.innings
    match_runs = 0
    match_wickets = 0
    for i in range(len(innings)):
        match_runs += int(innings[i]["runs"])
        match_wickets += int(innings[i]["wickets"])
    return match_runs, match_wickets


def downloadRecentMatchRecords(player_matches_url, player_id) -> None:
    """
    1. Check if the player recent match records are downloaded
    2. Check if player_matches_url exists or not
    3. Extract recent records' table from player_matches_url
        3.1 get HTML text
        3.2 create DataFrame column
            3.2A get table Header and create empty table body dictionary with headers as keys and empty list as values
            3.2B Get match ids for generating additional info and update table_body
        3.3 extract values and add them to table_body
            3.3A Cleaning batting figure
            3.3B Cleaning bowling figure
            3.3C Extracting Match ID
            3.3D remaining all details
        3.4 Additional Details like ["MATCH_CLASS", "TOTAL_RUNS", "TOTAL_WICKETS"]
            3.4A Extract Match Class
            3.4B Extract Total Runs & Wickets
    4 Convert Dict into DataFrame and then save it in CSV format
    :param player_matches_url:
    :param player_id:
    :return: None
    """
    global pagesLeft

    # 1. Check if the player recent match records are downloaded
    file_name = str(player_id) + ".csv"
    folder_path = "DataBase/recentMatchRecords"
    file_path = folder_path + "/" + file_name
    if fileExists(file_name, folder_path):
        pagesLeft -= 10
        print(f"{pagesLeft} pages to download in recent match records")
        return

    # 2. Check if player_matches_url exists or not
    if player_matches_url is None:
        pagesLeft -= 10
        print(f"{pagesLeft} pages to download in recent match records")
        return

    # 3. Extract recent records' table from player_matches_url
    # 3.1 get HTML text
    html_text = requests.get(player_matches_url, time.sleep(sleepTime)).text
    soup = BeautifulSoup(html_text, "lxml")

    # 3.2 create DataFrame column
    # 3.2A get table Header and create empty table body dictionary with headers as keys and empty list as values
    table_body = {}
    table_headers = soup.find_all("th")
    df_columns = []
    for header in table_headers:
        if header.text == "FORMAT":
            df_columns.append("MATCH_ID")
            table_body["MATCH_ID"] = []
        else:
            df_columns.append(header.text)
            table_body[header.text] = []

    # 3.2B Get match ids for generating additional info and update table_body
    recent_matches_ids = []
    additional_info = {"MATCH_CLASS": [], "TOTAL_RUNS": [], "TOTAL_WICKETS": []}
    table_body.update(additional_info)

    # 3.3 extract values and add them to table_body
    table_body_data = soup.find_all("td")
    num_table_cols = len(df_columns)
    for index in range(len(table_body_data)):
        cols_index = index % num_table_cols

        # Cleaning batting figure
        if df_columns[cols_index] == "BAT":
            runs = table_body_data[index].text
            runs = getRunsSimplified(runs)
            table_body["BAT"].append(runs)

        # Cleaning bowling figure
        elif df_columns[cols_index] == "BOWL":
            wickets = table_body_data[index].text
            wickets = getWicketsSimplified(wickets)
            table_body["BOWL"].append(wickets)

        # Extracting Match ID
        elif df_columns[cols_index] == "MATCH_ID":
            match_url = table_body_data[index]
            match_url = match_url.find_all("a")
            match_url = match_url[0]['href']
            match_id = getMatchId(match_url)
            table_body["MATCH_ID"].append(match_id)
            recent_matches_ids.append(match_id)

        # remaining all details
        else:
            table_body[df_columns[cols_index]].append(table_body_data[index].text)

    # 3.4 Additional Details like ["MATCH_CLASS", "TOTAL_RUNS", "TOTAL_WICKETS"]

    for match_id in recent_matches_ids:
        print(f"{pagesLeft} pages to download in recent match records")

        time.sleep(sleepTime)
        match_api = Match(match_id)

        # 3.4A Extract Match Class
        match_class = getMatchClass(match_api)
        table_body["MATCH_CLASS"].append(match_class)

        # 3.4B Extract Total Runs & Wickets
        total_runs, total_wickets = getMatchTotalRunsAndWickets(match_api)
        table_body["TOTAL_RUNS"].append(total_runs)
        table_body["TOTAL_WICKETS"].append(total_wickets)

        pagesLeft -= 1

    # 4 Convert Dict into DataFrame and then save it in CSV format
    recent_records_df = pd.DataFrame()
    for column in table_body:
        recent_records_df[column] = table_body[column]
    recent_records_df.to_csv(file_path, index=False)
    pass


def getRecentMatchRecords() -> None:
    """
    For each player id extract players match url and download there recent match records
    :return: None
    """
    global bothSquadDetails, pagesLeft
    pagesLeft = len(bothSquadDetails) * 10

    for player_id in bothSquadDetails:
        player_matches_url = getPlayerMatchUrl(bothSquadDetails[player_id]["URL"])
        downloadRecentMatchRecords(player_matches_url, player_id)
    pass


def preMatchPreparation():
    """
    Extract Squad Details
    Extract each player’s recent match records
    Extract each player’s international match records
        Batting (Based on Match Type)
        Bowling (Based on Match Type)
    Calculate Pre Match Statistics.
    :return: None
    """
    getBothSquadDetails()
    getRecentMatchRecords()
    pass


if __name__ == '__main__':
    # matchUrl = input("Enter the ESPNCricInfo match URL: ")
    matchUrl = "https://www.espncricinfo.com/series/pakistan-super-league-2021-22-1292999/karachi-kings-vs-multan-sultans-1st-match-1293000/live-cricket-score"
    # vpnStatus = input("Are you using VPN?(y/n) ")
    # if vpnStatus == "y":
    #     sleepTime = 0

    preMatchPreparation()
