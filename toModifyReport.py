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
    team = []
    opposite_team = []
    for i, r in match_df.iterrows():
        if r["NAME"] in team_1_player_names:
            home_away.append("HOME")
            team.append(home_team)
            opposite_team.append(away_team)
            if home_team == team_batting_first:
                target_chase.append("TARGET")
            else:
                target_chase.append("CHASE")
        else:
            home_away.append("AWAY")
            team.append(away_team)
            opposite_team.append(home_team)
            if away_team == team_batting_first:
                target_chase.append("TARGET")
            else:
                target_chase.append("CHASE")

    return home_away, target_chase, team, opposite_team


path = "reports/allMatchesData.csv"
report_df = pd.read_csv(path)

for index, row in report_df.iterrows():
    match_id = row["MATCH_ID"]

    match_api = Match(match_id)
    match_df = pd.read_csv(f"reports/results/{match_id}.csv")
    home_away, target_chase, team, opposite_team = getPlayerTeamDetails(match_api, match_df)
    match_df["VS_TEAM"] = opposite_team

    cols = ['NAME', 'POSITION', 'TEAM_NAME', 'VS_TEAM', 'HOME_AWAY', 'TARGET_CHASE', 'RECENT_FORM', 'INT_FORM', 'INT_CLASS_FORM',
            'RECENT_CLASS_FORM', 'RECENT_PREDICTION', 'INT_PREDICTION', 'DREAM11']
    match_df = match_df[cols]
    match_df.to_csv(f"reports/results/{match_id}.csv", index=False)
