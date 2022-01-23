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
both_squad_details = {}
sleepTime = 1


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


def getBothSquadDetails():
    """

    :return:
    """
    both_squad_ids = getBothSquadIds()

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
