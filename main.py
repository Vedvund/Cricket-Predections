"""
Project Name: Cricket Prediction
Project Moto: To predict the upcoming match result and player performance (Machine Learning)
Project Description:
"""
import json
import os
import re
import time
import timeit
from typing import Union
import shutil

import pandas as pd
from bs4 import BeautifulSoup
from espncricinfo.match import Match
import matplotlib.pyplot as plt

import requests

# Global Variable
# global bothSquadDetails
bothSquadDetails = {}
sleepTime = 2
totalPlayers = 0
pagesLeft = 0
matchUrl = ""
vpnStatus = "n"
matchClass = ""
currentYear = 0
intPeriod = 0


def getBothSquadIds() -> list:
    """
    1. convert match url into squads url.
    2. Using BeautifulSoup extract html text and separate player id's from players url
    :return: List of all player ids in both teams
    """
    global matchUrl

    # 1. convert match url into squads url.
    match_squad_link = matchUrl.replace("live-cricket-score", "match-squads")

    # 2. Using BeautifulSoup extract html text and separate player id's from players url
    html_text = requests.get(match_squad_link, time.sleep(sleepTime)).text
    soup = BeautifulSoup(html_text, "lxml")

    table_data = soup.find_all("tbody")
    data = table_data[0].find_all('a', href=True)
    both_squad_ids = re.findall("[0-9][0-9][0-9]+", str(data))

    return both_squad_ids


def getSimplifiedPosition(player_primary_role):
    """
    Checks what is players' primary role and converts it to simpler format
    :param player_primary_role: str
    :return: str
    """
    if player_primary_role is None:
        return "5 Unknown"
    if "wicketkeeper" in player_primary_role.lower():
        return "1 Wicketkeeper"
    if "all" in player_primary_role.lower():
        return "3 All Rounder"
    if "bat" in player_primary_role.lower():
        return "2 Batsmen"
    if "bowl" in player_primary_role.lower():
        return "4 Bowler"
    return player_primary_role


def getPlayerDetails(player_id) -> None:
    """
    1. Get Player API link
    2. download player details in json format
    3. extract required details from json file
    4. Add all the player details on to the global variable squadDetails
    :param player_id: int
    :return: None
    """
    global bothSquadDetails, totalPlayers
    print(f"{totalPlayers} players to download, Current player ID: {player_id}")

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
        "POSITION": getSimplifiedPosition(player_details["position"]["name"]),
        "URL": player_details["links"][0]["href"],
        "PLAYING_11_STATUS": False,
        "RECENT_FORM": 0,
        "RECENT_CLASS_FORM": 0,
        "INT_CLASS_FORM": 0,
        "INTERNATIONAL_FORM": 0,
        "EXPERTS_CHOICE": 0,
        "PREDICTION": 0,
        "RECENT_PREDICTION": 0,
        "INT_PREDICTION": 0
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
    global totalPlayers, bothSquadDetails, matchUrl

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
                    "T20I": "T20", "Youth ODI": "ODI", "Youth Test": "Test"}
    if match_class == "":
        return "Warm-up"
    return classes_list[match_class]


def getMatchTotalRunsAndWickets(match_api):
    """
    Extract all runs and wickets and get total runs and total wickets of that match
    :param match_api: Dictionary
    :return: int, int
    """

    # Check if the match has a result
    time.sleep(sleepTime)
    result = match_api.result
    if result == "No result":
        return 0, 0

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

        print(f"{file_name} exists & {pagesLeft} pages to download in recent match records")
        return

    # 2. Check if player_matches_url exists or not
    if player_matches_url is None:
        pagesLeft -= 10
        print(f" matches page doesn't exists for {player_id} & {pagesLeft} pages to download in recent match records")
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
    additional_info = {"MATCH_CLASS": [], "TOTAL_RUNS": [], "TOTAL_WICKETS": [], "PERFORMANCE": []}
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
        print(f"{pagesLeft} pages to download in recent match records, Current player id: {player_id}")

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

    # Performance
    for i in range(len(table_body["TOTAL_WICKETS"])):
        runs = 0
        wickets = 0
        if "BAT" in table_body:
            runs = table_body["BAT"][i]
        if "BOWL" in table_body:
            wickets = table_body["BOWL"][i]
        match_runs = table_body["TOTAL_RUNS"][i]
        match_wickets = table_body["TOTAL_WICKETS"][i]

        player_points = int(runs) + (int(wickets) * 25)
        match_points = int(match_runs) + (int(match_wickets) * 25)

        performance = 0
        if (player_points != 0) and (match_points != 0):
            performance = (player_points / match_points) * 100

        table_body["PERFORMANCE"].append(round(performance, 3))

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

        # 1. Check if the player recent match records are downloaded
        file_name = str(player_id) + ".csv"
        folder_path = "DataBase/recentMatchRecords"
        if fileExists(file_name, folder_path):
            pagesLeft -= 10
            print(
                f"for {player_id} recent matches records are already downloaded & {pagesLeft} pages to download in recent match records")
        else:
            player_matches_url = getPlayerMatchUrl(bothSquadDetails[player_id]["URL"])
            downloadRecentMatchRecords(player_matches_url, player_id)
    pass


def getInternationalRecordsLink(player_id) -> str:
    """
    check if international records are available
    :param player_id: int
    :return: str
    """
    test_odi_t20i_records_link = f"https://stats.espncricinfo.com/ci/engine/player/{player_id}.html?class=11;template=results;type=allround;view=match"
    youth_odi_link = f"https://stats.espncricinfo.com/ci/engine/player/{player_id}.html?class=21;template=results;type=allround;view=match"

    html_text = requests.get(test_odi_t20i_records_link, time.sleep(sleepTime)).text
    soup = BeautifulSoup(html_text, "lxml")

    # 2. Check if the records' table is available if not return youth odi link
    table_header = soup.find_all("tr", class_="headlinks")
    if len(table_header) == 0:
        return youth_odi_link

    return test_odi_t20i_records_link


def getInternationalRecordsDict(records_link) -> dict:
    """
    1. Extract html text from link
    2. Check if the records' table is available if not return None
    3. Extract table html data
    4. Convert html table into DataFrame
    4.1 Extract table header
        4.1A Check if the head is empty
    4.2 Extract table body
        4.2A if last column then convert it to match id
    :param records_link: str
    :return: Dictionary
    """
    global pagesLeft
    # 1. Extract html text from link
    html_text = requests.get(records_link, time.sleep(sleepTime)).text
    soup = BeautifulSoup(html_text, "lxml")

    # 2. Check if the records' table is available if not return None
    table_header = soup.find_all("tr", class_="headlinks")
    if len(table_header) == 0:
        pagesLeft -= 20
        print(f"No international records found, {pagesLeft} pages to download in international Match Records")
        return {}

    # 3. Extract table html data
    table_data = soup.find_all("table", class_="engineTable")
    table_data = table_data[3]

    # 4. Convert html table into DataFrame
    # 4.1 Extract table header
    head_data = table_data.find_all("th")
    column = []
    table = {}
    count = 1
    for head in head_data:
        header = head.text
        # 4.1A Check if the head is empty
        if header == "":
            header = "empty-" + str(count)
            count += 1
        column.append(header)
        table[header] = []

    # 4.2 Extract table body
    table_body_data = table_data.find_all("td")
    num_table_cols = len(column)
    for index in range(len(table_body_data)):
        cols_index = index % num_table_cols

        # if last column then convert it to match id
        if cols_index == num_table_cols - 1:
            # match_name = table_body_data[index].text
            match_url = table_body_data[index]
            match_url = match_url.find_all("a")
            match_url = match_url[0]['href']
            match_id = getMatchId(match_url)
            type_and_id = str(match_id)
            table[column[cols_index]].append(type_and_id)
        elif column[cols_index] == "Start Date":
            year = table_body_data[index].text
            year = year.split(" ")
            year = year[2]
            table[column[cols_index]].append(year)
        else:
            table[column[cols_index]].append(table_body_data[index].text)

    return table


def getInternationalRecordsTable(player_id) -> None:
    """
    1. Check if the player recent match records are downloaded
    2. Extract international matches records and extract the data
    3. Create table and download it into a csv file
        3.1 Create table dictionary format
        3.2 Go through each row in a sequential order and append the extracted values
            3.2A Extract runs
            3.2B Extract wickets
            3.2C Extract match
            3.2D Extract year
            3.2E Extract ground
            3.2F extract Match ID
            3.2G Extract Match Class
            3.2H Extract Match runs and wickets
            3.2I Calculate performance
    4. convert dict into DataFrame and then CSV
    :param player_id:
    :return:
    """
    global pagesLeft, currentYear, intPeriod

    # 1. Check if the player recent match records are downloaded
    file_name = str(player_id) + ".csv"
    folder_path = "DataBase/internationalMatchRecords"
    file_path = folder_path + "/" + file_name
    if fileExists(file_name, folder_path):
        pagesLeft -= 20
        print(
            f"For {player_id} International records are already downloaded, {pagesLeft} pages to download in international Match Records")
        return

    # 2. Extract international matches records and extract the data
    records_link = getInternationalRecordsLink(player_id)
    records_dict = getInternationalRecordsDict(records_link)

    # 3. Create table and download it into a csv file
    # 3.1 Create table dictionary format
    table = {"MATCH": [], "BAT": [], "BALL": [], "DATE": [], "GROUND": [], "MATCH_ID": [], "MATCH_CLASS": [],
             "TOTAL_RUNS": [], "TOTAL_WICKETS": [], "PERFORMANCE": []}

    records_dict_keys_list = []
    for keys in records_dict:
        records_dict_keys_list.append(keys)

    # 3.2 Go through each row in a sequential order and append the extracted values
    if len(records_dict) != 0:
        for i in range(len(records_dict["Bat1"])):
            if currentYear - int(records_dict["Start Date"][i]) <= intPeriod:

                # 3.2A Extract runs
                bat2 = 0
                bat1 = getRunsSimplified(records_dict["Bat1"][i])
                if bat1 == "DNB" or bat1 == "-" or bat1 == "TDNB" or bat1 == "sub":
                    bat1 = 0
                if "Bat2" in records_dict:
                    bat2 = getRunsSimplified(records_dict["Bat2"][i])
                if bat2 == "DNB" or bat2 == "-" or bat2 == "TDNB" or bat2 == "sub":
                    bat2 = 0
                runs = int(bat1) + int(bat2)
                table["BAT"].append(runs)

                # 3.2B Extract wickets
                wickets = records_dict["Wkts"][i]
                if wickets == "-":
                    wickets = 0
                table["BALL"].append(wickets)

                # 3.2C Extract match
                table["MATCH"].append(records_dict["Opposition"][i])

                # 3.2D Extract year
                table["DATE"].append(records_dict["Start Date"][i])

                # 3.2E Extract ground
                table["GROUND"].append(records_dict["Ground"][i])

                # 3.2F extract Match ID
                key_value = records_dict_keys_list[len(records_dict) - 1]
                match_id = records_dict[key_value][i]
                table["MATCH_ID"].append(match_id)

                match_api = Match(match_id)

                # 3.2G Extract Match Class
                table["MATCH_CLASS"].append(getMatchClass(match_api))

                match_runs, match_wickets = getMatchTotalRunsAndWickets(match_api)

                # 3.2H Extract Match runs and wickets
                table["TOTAL_RUNS"].append(match_runs)
                table["TOTAL_WICKETS"].append(match_wickets)

                # 3.2I Calculate performance
                player_points = int(runs) + (int(wickets) * 25)
                match_points = int(match_runs) + (int(match_wickets) * 25)

                performance = 0
                if (player_points != 0) and (match_points != 0):
                    performance = (player_points / match_points) * 100
                table["PERFORMANCE"].append(round(performance, 3))

                pagesLeft -= 1
                print(f"{pagesLeft} pages to download in international Match Records, Current player id: {player_id}")

    # 4. convert dict into DataFrame and then CSV
    international_records_df = pd.DataFrame()
    for head in table:
        international_records_df[head] = table[head]
    international_records_df.to_csv(file_path, index=False)

    pass


def getInternationalMatchRecords() -> None:
    """
    Go through each player ID and generate international records table
    :return: None
    """
    global bothSquadDetails, pagesLeft
    pagesLeft = len(bothSquadDetails) * 20

    for player_id in bothSquadDetails:
        getInternationalRecordsTable(player_id)
    pass


def getAllRecentPerformance(player_id) -> Union[int, float]:
    """
    1. open the csv file as DataFrame
    2. calculate average performance in all recent matches
    :param player_id: int
    :return: int
    """
    file_name = f"{player_id}.csv"
    folder_path = "DataBase/recentMatchRecords"
    if fileExists(file_name, folder_path):
        recent_matches = pd.read_csv(f"DataBase/recentMatchRecords/{player_id}.csv")
        total = 0
        count = 0
        for index, row in recent_matches.iterrows():
            total += row["PERFORMANCE"]
            count += 1
        if total == 0 or count == 0:
            return 0
        return round((total / count), 3)
    print(f"{player_id} recent performance doesn't exist")
    return 0


def getMatchClassRecentPerformance(player_id) -> Union[int, float]:
    """
    1. open the csv file as DataFrame
    2. calculate average performance in similar match class in  recent matches
    :param player_id: int
    :return: int
    """
    global matchClass

    file_name = f"{player_id}.csv"
    folder_path = "DataBase/recentMatchRecords"
    if fileExists(file_name, folder_path):
        recent_matches = pd.read_csv(f"DataBase/recentMatchRecords/{player_id}.csv")
        total = 0
        count = 0
        for index, row in recent_matches.iterrows():
            if matchClass == row["MATCH_CLASS"]:
                total += row["PERFORMANCE"]
                count += 1
        if total == 0 or count == 0:
            return 0
        return round((total / count), 3)
    print(f"{player_id} recent performance doesn't exist")
    return 0


def getAllInternationalPerformance(player_id) -> Union[int, float]:
    """
    1. open the csv file as DataFrame
    2. calculate average performance in all international matches in the last 2 years period
    :param player_id: int
    :return: int
    """
    file_name = f"{player_id}.csv"
    folder_path = "DataBase/internationalMatchRecords"
    if fileExists(file_name, folder_path):
        international_matches = pd.read_csv(f"DataBase/internationalMatchRecords/{player_id}.csv")
        total = 0
        count = 0
        for index, row in international_matches.iterrows():
            total += row["PERFORMANCE"]
            count += 1
        if total == 0 or count == 0:
            return 0
        return round((total / count), 3)
    print(f"{player_id} international performance doesn't exist")
    return 0


def getMatchClassInternationalPerformance(player_id) -> Union[int, float]:
    """
    1. open the csv file as DataFrame
    2. calculate average performance in similar match class in international matches
    :param player_id: int
    :return: int
    """
    global matchClass
    file_name = f"{player_id}.csv"
    folder_path = "DataBase/internationalMatchRecords"
    if fileExists(file_name, folder_path):
        international_matches = pd.read_csv(f"DataBase/internationalMatchRecords/{player_id}.csv")
        total = 0
        count = 0
        for index, row in international_matches.iterrows():
            if matchClass == row["MATCH_CLASS"]:
                total += row["PERFORMANCE"]
                count += 1
        if total == 0 or count == 0:
            return 0
        return round((total / count), 3)
    print(f"{player_id} international performance doesn't exist")
    return 0


def getPreMatchStatistics() -> None:
    """
    1. Create Statistics table dictionary
    2. Generate table dictionary content
    2.1 Extract name and position from global variable bothSquadDetails
    2.2 Calculate all recent matches form
    2.3 Calculate all international matches form
    2.4 Calculate all similar class matches form (average of international and recent matches form)
    2.4A Calculate similar class recent matches form
    2.4B Calculate similar class international matches form
    3. Create csv file from the statistics table dictionary
    :return: None
    """
    global bothSquadDetails, matchUrl

    # 1. Create Statistics table dictionary
    statistics_table = {"NAME": [], "POSITION": [], "RECENT_CLASS_FORM": [],
                        "INT_CLASS_FORM": [], "RECENT_FORM": [], "MATCH_CLASS_FORM": [], "INTERNATIONAL_FORM": [],
                        "RECENT_PREDICTION": [], "INT_PREDICTION": []}

    # 2. Generate table dictionary content
    for player_id in bothSquadDetails:
        # 2.1 Extract name and position from global variable bothSquadDetails
        name = bothSquadDetails[player_id]["NAME"]
        statistics_table["NAME"].append(name)

        position = bothSquadDetails[player_id]["POSITION"]
        statistics_table["POSITION"].append(position)

        # 2.2 Calculate all recent matches form
        recent_all = getAllRecentPerformance(player_id)
        statistics_table["RECENT_FORM"].append(recent_all)
        bothSquadDetails[player_id]["RECENT_FORM"] = recent_all

        # 2.3 Calculate all international matches form
        int_all = getAllInternationalPerformance(player_id)
        statistics_table["INTERNATIONAL_FORM"].append(int_all)
        bothSquadDetails[player_id]["INTERNATIONAL_FORM"] = int_all

        # 2.4 Calculate all similar class matches form (average of international and recent matches form)
        # 2.4A Calculate similar class recent matches form
        recent_class = getMatchClassRecentPerformance(player_id)
        statistics_table["RECENT_CLASS_FORM"].append(recent_class)

        # 2.4B Calculate similar class international matches form
        int_class = getMatchClassInternationalPerformance(player_id)
        statistics_table["INT_CLASS_FORM"].append(int_class)

        # 2.4C Calculate average of both
        match_class_form = (recent_class + int_class) / 2
        statistics_table["MATCH_CLASS_FORM"].append(round(match_class_form, 3))
        bothSquadDetails[player_id]["RECENT_CLASS_FORM"] = recent_class
        bothSquadDetails[player_id]["INT_CLASS_FORM"] = int_class

        # 2.4D Calculate Recent prediction
        recent_prediction = int(recent_all) + (int(recent_class) * 0.5)
        statistics_table["RECENT_PREDICTION"].append(round(recent_prediction, 3))
        bothSquadDetails[player_id]["RECENT_PREDICTION"] = round(recent_prediction, 3)

        # 2.4E Calculate International prediction
        int_prediction = ((int(recent_all) * (int(recent_class) * 0.5)) + (
                int(int_all) + (int(int_class) * 0.5))) / 2
        statistics_table["INT_PREDICTION"].append(round(int_prediction, 3))
        bothSquadDetails[player_id]["INT_PREDICTION"] = round(int_prediction, 3)

    # 3.0 Create csv file from the statistics table dictionary
    match_id = getMatchId(matchUrl)
    file_name = f"{match_id}.csv"
    folder_path = "DataBase/preMatchStatistics"
    file_path = folder_path + "/" + file_name

    statistics_table_df = pd.DataFrame()
    for column in statistics_table:
        statistics_table_df[column] = statistics_table[column]

    sorted_statistics_table_df = statistics_table_df.sort_values(by=['RECENT_PREDICTION'], ascending=False)

    sorted_statistics_table_df.to_csv(file_path, index=False)
    sorted_statistics_table_df.to_csv("currentMatchReports/preMatchPrediction.csv", index=False)

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
    # Start stopwatch
    start = timeit.default_timer()

    getBothSquadDetails()
    getRecentMatchRecords()
    getInternationalMatchRecords()
    getPreMatchStatistics()
    for i in range(3):
        print("")

    # Stop stopwatch & calculate elapsed time
    stop = timeit.default_timer()
    print('Time elapsed for Pre Match Statistics: ', round(((stop - start) / 60), 3), "'s")
    pass


def getPlayingXIIds(match_api) -> list:
    """
    1. extract playing 11 form team 1 and team 2
    2. append all into one single list variable
    :param match_api: dict
    :return: list
    """
    # 1. extract playing 11 form team 1 and team 2
    team_1 = match_api.team_1_players
    team_2 = match_api.team_2_players

    # 2. append all into one single list variable
    all_playing_11_players_ids = []
    for i in range(len(team_1)):
        all_playing_11_players_ids.append(team_1[i]["object_id"])
    for i in range(len(team_2)):
        all_playing_11_players_ids.append(team_2[i]["object_id"])

    return all_playing_11_players_ids


def getCleanNames(team_names_string) -> list:
    """
    1. Clear the string from unwanted text
    2. split the string into names
    3. send the names list
    :param team_names_string: str
    :return: list
    """
    # 1. Clear the string from unwanted text
    names = team_names_string
    unwanted_text = [" (wk)", " (c)", " (c)(wk)", " (capt.)", " (capt./wk)", " (c & wk)", "(wk)", "(c)", " (c/w)",
                     "(c)(wk)", "(capt.)", "(capt./wk)", "(c & wk)", "(c/w)", "(w)", " (w)", "."]

    for text in unwanted_text:
        names = names.replace(text, "")

    # 2. split the string into names
    names = names.split(", ")
    players_names = []
    for player in names:
        full_name = player
        # name = player.split(" ")
        # full_name = name[1] + " " + name[2]
        players_names.append(full_name)

    # 3. send the names list
    return players_names


def getPlaying11Manually() -> list:
    """
    # 1. Extract playing 11 names of both teams from input and combine them
    # 2. extract all squad players names from bothSquadDetails
    # 3. Check if the name exists in bothSquadDetails. if yes extract player id, else take player id from input()
    # 4. send all the player ids
    :return: list
    """
    global bothSquadDetails

    # 1. Extract playing 11 names of both teams from input and combine them
    playing_11_names = []
    team_1_string = input("Enter team 1 names: ")
    playing_11_names += getCleanNames(team_1_string)
    team_2_string = input("Enter team 2 names: ")
    playing_11_names += getCleanNames(team_2_string)

    # 2. extract all squad players names from bothSquadDetails
    squad_names = {}
    for ids in bothSquadDetails:
        name = bothSquadDetails[ids]["NAME"].lower()
        squad_names[name] = ids

    # 3. Check if the name exists in bothSquadDetails. if yes extract player id, else take player id from input()
    playing_11_ids = []
    for player_name in playing_11_names:
        if player_name.lower() in squad_names:
            player_id = squad_names[player_name.lower()]
            playing_11_ids.append(player_id)
        else:
            print(f"{player_name} not present in any of the squad")
            player_id = input(f"{player_name} ESPNCricInfo Details")
            playing_11_ids.append(player_id)

    # 4. send all the player ids
    return playing_11_ids


def extractPlayingXI() -> None:
    """
    1. Extract both teams Playing 11 ids
    1.1 Check if playing 11 is available
    1.2 if playing 11 is not available then extract ids manually
    2. check if extracted ids are in bothSquadDetails and change the status of PLAYING_11_STATUS in bothSquadDetails
    2.1 if not present then extract player details and add them to bothSquadDetails
    2.2 change the status of PLAYING_11_STATUS of each player in bothSquadDetails
    :return: None
    """
    global matchUrl, sleepTime, bothSquadDetails, totalPlayers

    # 1. Extract both teams Playing 11 ids
    # 1.1 Check if playing 11 is available
    match_id = getMatchId(matchUrl)
    time.sleep(sleepTime)
    available = input("is playing xi available? (y/n) ")
    if available == "y":
        match_api = Match(match_id)
        playing_11_ids = getPlayingXIIds(match_api)
    else:
        playing_11_ids = []

    # 1.2 if playing 11 is not available then extract ids manually
    if len(playing_11_ids) == 0:
        print("Playing xi not yet announced. Please enter playing XI manually")
        playing_11_ids = getPlaying11Manually()

    # 2. check if extracted ids are in bothSquadDetails and change the status of PLAYING_11_STATUS in bothSquadDetails
    # 2.1 if not present then extract player details and add them to bothSquadDetails
    totalPlayers = len(playing_11_ids)
    for player_id in playing_11_ids:
        if str(player_id) in bothSquadDetails:
            totalPlayers -= 1
            print(
                f"{bothSquadDetails[str(player_id)]['NAME']} already exists in Squad Details, {totalPlayers} players left  to download")
            bothSquadDetails[str(player_id)]["PLAYING_11_STATUS"] = True
        else:
            getPlayerDetails(player_id)
            bothSquadDetails[player_id]["PLAYING_11_STATUS"] = True

        # 2.2 change the status of PLAYING_11_STATUS of each player in bothSquadDetails
    pass


def getPlaying11Statistics() -> None:
    """
    # 1.0 Create table dictionary with empty values
    # 2.0 check PLAYING_11_STATUS in bothSquadDetails and extract data and append them to the table
    # 3.0 Create csv file from the statistics table dictionary

    :return:
    """
    global matchUrl, sleepTime, bothSquadDetails, totalPlayers

    # 1.0 Create table dictionary with empty values
    table = {"NAME": [], "POSITION": [], "RECENT_FORM": [], "INT_FORM": [], "INT_CLASS_FORM": [],
             "RECENT_CLASS_FORM": [], "RECENT_PREDICTION": [], "INT_PREDICTION": []}

    # 2.0 check PLAYING_11_STATUS in bothSquadDetails and extract data and append them to the table
    for player in bothSquadDetails:
        if bothSquadDetails[player]["PLAYING_11_STATUS"]:
            name = bothSquadDetails[player]["NAME"]
            table["NAME"].append(name)

            position = bothSquadDetails[player]["POSITION"]
            table["POSITION"].append(position)

            recent_form = bothSquadDetails[player]["RECENT_FORM"]
            table["RECENT_FORM"].append(round(recent_form, 3))

            int_form = bothSquadDetails[player]["INTERNATIONAL_FORM"]
            table["INT_FORM"].append(round(int_form, 3))

            recent_class = bothSquadDetails[player]["RECENT_CLASS_FORM"]
            table["RECENT_CLASS_FORM"].append(round(recent_class, 3))

            int_class = bothSquadDetails[player]["INT_CLASS_FORM"]
            table["INT_CLASS_FORM"].append(round(int_class, 3))

            int_class = bothSquadDetails[player]["RECENT_PREDICTION"]
            table["RECENT_PREDICTION"].append(round(int_class, 3))

            int_class = bothSquadDetails[player]["INT_PREDICTION"]
            table["INT_PREDICTION"].append(round(int_class, 3))

    # 3.0 Create csv file from table dictionary
    match_id = getMatchId(matchUrl)
    file_name = f"{match_id}.csv"
    folder_path = "DataBase/playing11Statistics"
    file_path = folder_path + "/" + file_name

    statistics_table_df = pd.DataFrame()
    for column in table:
        statistics_table_df[column] = table[column]

    sorted_statistics_table_df = statistics_table_df.sort_values(by=['RECENT_PREDICTION'], ascending=False)

    sorted_statistics_table_df.to_csv(file_path, index=False)
    sorted_statistics_table_df.to_csv("currentMatchReports/afterTossPrediction.csv", index=False)
    pass


def afterToss():
    extractPlayingXI()
    getRecentMatchRecords()
    getInternationalMatchRecords()
    getPreMatchStatistics()
    getPlaying11Statistics()
    pass


def checkDirectory() -> None:
    """
    Check if required directory exists or not, ff it doesn't exist then Create directory
    :return: None
    """
    directories = [
        "DataBase/internationalMatchRecords",
        "DataBase/playing11Statistics",
        "DataBase/preMatchStatistics",
        "DataBase/recentMatchRecords",
        "DataBase/squadDetails",
        "currentMatchReports"
    ]

    for path in directories:
        if os.path.isdir(path):
            print(f"{path} exists")
        else:
            os.makedirs(path)
    pass


def clientInputs() -> None:
    """
    1. Enter Match URL
    2. If client is using vpn
    3. Check the international period. Not more than 1 year works
    4. Enter current match class
    5. Check directory before going forward
    :return: None
    """
    global matchUrl, vpnStatus, sleepTime, currentYear, intPeriod, matchClass

    matchUrl = ""
    vpnStatus = ""
    matchClass = ""

    # 1. Enter Match URL
    matchUrl = input("Enter the ESPNCricInfo match URL: ")

    # 2. If client is using vpn
    vpnStatus = input("Are you using VPN?(y/n) ")
    if vpnStatus == "y":
        sleepTime = 0

    # 3. Check the international period. Not more than 1 year works
    currentYear = 2022
    intPeriod = 1

    # 4. Enter current match class
    matchClass = input(" please enter type of match class (T20/Test/ODI): ")

    # 5. Check directory before going forward
    checkDirectory()
    pass


def checkReportStatus() -> bool:
    """
    # 1.0 Extract match id and open the all matches data file
    # 2.0 if match id is already in the all matches data then return true else false
    :return: bool
    """
    global matchUrl
    # 1.0 Extract match id and open the all matches data file
    match_id = getMatchId(matchUrl)
    all_matches_data_df = pd.read_csv("reports/allMatchesData.csv")

    # 2.0 if match id is already in the all matches data then return true else false
    for index, row in all_matches_data_df.iterrows():
        if row["MATCH_ID"] == int(match_id):
            return True
    return False


def getMatchesData():
    """
    # 1.0 Extract all the details  required for report
    # 2.0 Open allMatchesData.csv file and add the match details to the file
    :return: None
    """
    # 1.0 Extract all the details  required for report
    match_id = getMatchId(matchUrl)
    match_api = Match(match_id)
    total_runs, total_wickets = getMatchTotalRunsAndWickets(match_api)
    home_team = match_api.home_team
    away_team = match_api.team_2_abbreviation
    if home_team == match_api.team_2_abbreviation:
        away_team = match_api.team_1_abbreviation

    match_winner = match_api.match_winner
    winning_side = "AWAY"
    if match_winner == home_team:
        winning_side = "HOME"
    match_report_path = f"report/results/{match_id}.csv"

    # 2.0 Open allMatchesData.csv file and add the match details to the file
    df = pd.read_csv("reports/allMatchesData.csv")
    df.loc[len(df.index)] = [match_id, match_api.series_name, match_api.ground_name, match_api.match_class,
                             match_api.match_title, match_api.lighting, total_runs, total_wickets,
                             home_team, away_team, match_api.batting_first,
                             match_api.match_winner, winning_side, match_report_path]
    df.to_csv("reports/allMatchesData.csv", index=False)
    pass


def getPlayersDream11Points(match_df):
    """
    get player details manually
    :param match_df: DataFrame
    :return: List
    """
    print("\nEnter Dream11 Points Manually")
    dream11 = []
    for index, row in match_df.iterrows():
        player_name = row["NAME"]
        player_points = int(input(f"{player_name}: "))
        dream11.append(player_points)
    return dream11


def getPlayerTeamDetails(match_api, match_df):
    """
    1.0 extract Team1 and Team2 player Names
    2.0 add home team player names to team_1_player_names and away team names to team_2_player_names
    3.0 set home team name and away team name
    4.0 find home_away and target_chase details of the player
    :param match_api: dict
    :param match_df: dataframe
    :return: list, list
    """
    # 1.0 extract Team1 and Team2 player Names
    team_1 = match_api.team_1_players
    team_2 = match_api.team_2_players

    team_1_player_names = []
    team_2_player_names = []

    # 2.0 add home team player names to team_1_player_names and away team names to team_2_player_names
    for i in range(len(team_1)):
        if match_api.home_team == match_api.team_1_abbreviation:
            team_1_player_names.append(team_1[i]["known_as"])
        else:
            team_1_player_names.append(team_2[i]["known_as"])

    for i in range(len(team_2)):
        if match_api.home_team == match_api.team_1_abbreviation:
            team_2_player_names.append(team_2[i]["known_as"])
        else:
            team_2_player_names.append(team_1[i]["known_as"])

    # 3.0 set home team name and away team name
    home_team = match_api.home_team
    away_team = match_api.team_2_abbreviation
    if home_team == match_api.team_2_abbreviation:
        away_team = match_api.team_1_abbreviation

    team_batting_first = match_api.batting_first

    # 4.0 find home_away and target_chase details of the player
    home_away = []
    target_chase = []
    for index, row in match_df.iterrows():
        if row["NAME"] in team_1_player_names:
            home_away.append("HOME")
            if home_team == team_batting_first:
                target_chase.append("TARGET")
            else:
                target_chase.append("CHASE")
        else:
            home_away.append("AWAY")
            if away_team == team_batting_first:
                target_chase.append("TARGET")
            else:
                target_chase.append("CHASE")

    return home_away, target_chase


def getFinalMatchReport():
    """
    # 1.0 Open the match file from DataBase/playing11Statistics and sort the DF based on NAME col
    # 2.0 Check if the DREAM11 col is already in playing11Statistics. if not extract each players' points
    # 3.0 extract player-details if necessary
    # 4.0 Rearrange columns of DataFrame
    :return: None
    """
    # 1.0 Open the match file from DataBase/playing11Statistics and sort the DF based on NAME col
    match_id = getMatchId(matchUrl)
    match_df = pd.read_csv(f"DataBase/playing11Statistics/{match_id}.csv")
    match_df = match_df.sort_values(by=['NAME'])

    # 2.0 Check if the DREAM11 col is already in playing11Statistics. if not extract each players' points
    cols = match_df.columns.tolist()
    if "DREAM11" not in cols:
        dream11 = getPlayersDream11Points(match_df)
        match_df["DREAM11"] = dream11

    # 3.0 extract player-details if necessary
    match_api = Match(match_id)
    home_away, target_chase = getPlayerTeamDetails(match_api, match_df)
    match_df["HOME_AWAY"] = home_away
    match_df["TARGET_CHASE"] = target_chase

    # 4.0 Rearrange columns of DataFrame
    cols = ['NAME', 'POSITION', 'HOME_AWAY', 'TARGET_CHASE', 'RECENT_FORM', 'INT_FORM', 'INT_CLASS_FORM',
            'RECENT_CLASS_FORM', 'RECENT_PREDICTION', 'INT_PREDICTION', 'DREAM11']
    match_df = match_df[cols]
    match_df.to_csv(f"reports/results/{match_id}.csv", index=False)
    pass


def createReport():
    """
    1.0 Check if match report already exists:
    2.0 Create final match report
    :return: nONE
    """
    # 1.0 Check if match report already exists:
    exists = checkReportStatus()

    # 2.0 Create final match report
    if not exists:
        getMatchesData()
        getFinalMatchReport()
    pass


def getAllTop5():
    """
    # 1.0 Get similar match ids form reports/allMatchesData.csv file
    # 2.0 create empty top5 dataframe
    # 3.0 Extract top 5 players from the similar matches and add them to the top5 dataframe
    # 4.0 Sort top5 dataframe
    :return: DataFrame
    """
    global matchUrl
    # 1.0 Get similar match ids form reports/allMatchesData.csv file
    all_matches_data_df = pd.read_csv("reports/allMatchesData.csv")
    match_id = getMatchId(matchUrl)
    match_api = Match(match_id)
    match_class = match_api.match_class

    all_match_ids = []
    for index, row in all_matches_data_df.iterrows():
        if row["MATCH_CLASS"] == match_class:
            all_match_ids.append(row["MATCH_ID"])

    # 2.0 create empty top5 dataframe
    all_match_ids.sort()
    top5_df = pd.DataFrame(
        columns=['NAME', 'POSITION', 'HOME_AWAY', 'TARGET_CHASE', 'RECENT_FORM', 'INT_FORM', 'INT_CLASS_FORM',
                 'RECENT_CLASS_FORM', 'RECENT_PREDICTION', 'INT_PREDICTION', 'DREAM11']
    )

    # 3.0 Extract top 5 players from the similar matches and add them to the top5 dataframe
    for matchID in all_match_ids:
        match_df = pd.read_csv(f"reports/results/{matchID}.csv")
        match_df = match_df.sort_values(by=['DREAM11'], ascending=False)

        result = match_df.iloc[[0, 1, 2, 3, 4]]
        frames = [top5_df, result]
        top5_df = pd.concat(frames)

    # 4.0 Sort top5 dataframe
    top5_df = top5_df.sort_values(by=['INT_FORM'], ascending=False)
    top5_df = top5_df.sort_values(by=['POSITION'], ascending=False)
    top5_df = top5_df.sort_values(by=['RECENT_PREDICTION'], ascending=False)
    top5_df.to_csv("currentMatchReports/top5Insights.csv", index=False)
    return top5_df


def getTopPlayersInsights(top5_df):
    """
    # 1.0 get frequency count
    # 2.0 creating the dataset
    # 3.0 creating the bar plot
    :param top5_df: DataFrame
    :return:
    """
    # 1.0 get frequency count
    frequency = {}
    for index, row in top5_df.iterrows():
        recent_prediction = round(row["RECENT_PREDICTION"], 1)
        if recent_prediction not in frequency:
            frequency[recent_prediction] = 0
        frequency[recent_prediction] += 1

    # 2.0 creating the dataset
    form = list(frequency.keys())
    count = list(frequency.values())

    fig = plt.figure(figsize=(10, 5))
    plt.xticks(form)

    # 3.0 creating the bar plot
    plt.bar(form, count, color='maroon',
            width=0.4)

    plt.xlabel("RECENT PREDICTION")
    plt.ylabel("COUNT")
    plt.title("FREQUENCY BASED ON RECENT PREDICTION RESULTS")
    plt.savefig('currentMatchReports/recent_prediction_insights.png')
    plt.close(fig)
    pass


def getTopBattingInsights(top5_df):
    """
    # 1.0 get frequency count
    # 2.0 creating the dataset
    # 3.0 creating the bar plot
    :param top5_df: DataFrame
    :return:
    """
    # 1.0 get frequency count
    frequency = {}
    for index, row in top5_df.iterrows():
        if row["POSITION"] == "2 Batsmen":
            recent_prediction = round(row["RECENT_PREDICTION"], 1)
            if recent_prediction not in frequency:
                frequency[recent_prediction] = 0
            frequency[recent_prediction] += 1

    # 2.0 creating the dataset
    form = list(frequency.keys())
    count = list(frequency.values())

    fig = plt.figure(figsize=(10, 5))
    plt.xticks(form)

    # 3.0 creating the bar plot
    plt.bar(form, count, color='maroon',
            width=0.4)

    plt.xlabel("RECENT PREDICTION of BATTING")
    plt.ylabel("COUNT")
    plt.title("BATTING FREQUENCY BASED ON RECENT PREDICTION RESULTS")
    plt.savefig('currentMatchReports/batting_insights.png')
    plt.close(fig)
    pass


def getTopBowlingInsights(top5_df):
    """
    # 1.0 get frequency count
    # 2.0 creating the dataset
    # 3.0 creating the bar plot
    :param top5_df: DataFrame
    :return:
    """
    # 1.0 get frequency count
    frequency = {}
    for index, row in top5_df.iterrows():
        if row["POSITION"] == "4 Bowler":
            recent_prediction = round(row["RECENT_PREDICTION"], 1)
            if recent_prediction not in frequency:
                frequency[recent_prediction] = 0
            frequency[recent_prediction] += 1

    # 2.0 creating the dataset
    form = list(frequency.keys())
    count = list(frequency.values())

    fig = plt.figure(figsize=(10, 5))
    plt.xticks(form)

    # 3.0 creating the bar plot
    plt.bar(form, count, color='maroon',
            width=0.4)

    plt.xlabel("RECENT PREDICTION of BOWLING")
    plt.ylabel("COUNT")
    plt.title("BOWLING FREQUENCY BASED ON RECENT PREDICTION RESULTS")
    plt.savefig('currentMatchReports/bowling_insights.png')
    plt.close(fig)
    pass


def getTopAllRounderInsights(top5_df):
    """
    # 1.0 get frequency count
    # 2.0 creating the dataset
    # 3.0 creating the bar plot
    :param top5_df: DataFrame
    :return:
    """
    # 1.0 get frequency count
    frequency = {}
    for index, row in top5_df.iterrows():
        if row["POSITION"] == "3 All Rounder":
            recent_prediction = round(row["RECENT_PREDICTION"], 1)
            if recent_prediction not in frequency:
                frequency[recent_prediction] = 0
            frequency[recent_prediction] += 1

    # 2.0 creating the dataset
    form = list(frequency.keys())
    count = list(frequency.values())

    fig = plt.figure(figsize=(10, 5))
    plt.xticks(form)

    # 3.0 creating the bar plot
    plt.bar(form, count, color='maroon',
            width=0.4)

    plt.xlabel("RECENT PREDICTION of ALL ROUNDERS")
    plt.ylabel("COUNT")
    plt.title("ALL ROUNDERS FREQUENCY BASED ON RECENT PREDICTION RESULTS")
    plt.savefig('currentMatchReports/all_rounder_insights.png')
    plt.close(fig)
    pass


def getInsights():
    top5_df = getAllTop5()
    getTopPlayersInsights(top5_df)
    getTopBattingInsights(top5_df)
    getTopBowlingInsights(top5_df)
    getTopAllRounderInsights(top5_df)
    pass


def deleteMatchFiles():
    global bothSquadDetails, matchUrl
    match_id = getMatchId(matchUrl)
    squad_ids = []
    for player_id in bothSquadDetails:
        squad_ids.append(player_id)
    # delete files
    delete_all_files = input("Do you want to delete all the files? (y/n): ")
    print()
    if (delete_all_files == "y") and (input("Are you sure? (y/n): ") == "y"):
        shutil.rmtree("DataBase", ignore_errors=True)
        shutil.rmtree("currentMatchReports", ignore_errors=True)

    else:
        for player_id in squad_ids:
            os.remove(f"DataBase/internationalMatchRecords/{player_id}.csv")

            files = os.listdir("DataBase/recentMatchRecords")
            if f"{player_id}.csv" in files:
                os.remove(f"DataBase/recentMatchRecords/{player_id}.csv")

        os.remove(f"DataBase/playing11Statistics/{match_id}.csv")
        os.remove(f"DataBase/preMatchStatistics/{match_id}.csv")
        os.remove(f"DataBase/squadDetails/{match_id}.json")

    pass


if __name__ == '__main__':
    clientInputs()
    preMatchPreparation()

    tossStatus = False
    if input("Toss Done? (y/n) ") == "y":
        tossStatus = True
        afterToss()

    if tossStatus and input("Do you want to get the match insights? (y/n) ") == "y":
        getInsights()

    if tossStatus and (input("Is the match over? (y/n) ") == "y"):
        createReport()
        deleteMatchFiles()
