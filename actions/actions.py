# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

from typing import Any, Text, Dict, List
from urllib import response

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import AllSlotsReset, SlotSet, ActiveLoop

import os
import re
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get('API_KEY', '')
DIR_PATH = os.path.dirname(os.path.realpath(__file__))

REGEX_EXACT_MATCH = r"^{}$"

class TheSportsDB:

    def __init__(self):
        self.base_url = "" #"https://sportscore1.p.rapidapi.com/teams/search"
        self.headers = {
            'x-rapidapi-host': "thesportsdb.p.rapidapi.com",
            'x-rapidapi-key': API_KEY
        }


    def search_player(self, name):
        url = "https://thesportsdb.p.rapidapi.com/searchplayers.php"
        querystring = {
            "p": name
        }
        file_path = os.path.join(DIR_PATH, 'db/search_player.json')
        return self.check_store(file_path, url, querystring)

    
    def search_team_by_name(self, name):
        url = "https://thesportsdb.p.rapidapi.com/searchteams.php"
        querystring = {
            "t": name
        }
        file_path = os.path.join(DIR_PATH, 'db/search_team_by_name.json')
        return self.check_store(file_path, url, querystring)
    
    
    def search_upcoming_events(self, id):
        url = "https://thesportsdb.p.rapidapi.com/eventsnext.php"
        querystring = {
            "id": id
        }
        file_path = os.path.join(DIR_PATH, 'db/search_upcoming_events.json')
        return self.check_store(file_path, url, querystring)


    def sports_list(self):
        print(self.headers)
        file_path = os.path.join(DIR_PATH, 'db/sports_list.json')
        if os.path.isfile(file_path):
            with open(file_path, 'r') as sports_list:
                return json.load(sports_list)
        else:
            url = "https://sportscore1.p.rapidapi.com/sports"
            response = requests.request("GET", url, headers=self.headers)
            print("RES:", response)
            r_data = response.json()
            with open(file_path, 'w+') as sports_list:
                json.dump(r_data, sports_list, indent=2)
            return r_data


    def check_store(self, file_path, url, params):
        # if os.path.isfile(file_path) and False:
        #     with open(file_path, 'r') as sports_list:
        #         return json.load(sports_list)
        # else:
        response = requests.request("GET", url, headers=self.headers, params=params)
        r_data = response.json()
        with open(file_path, 'w+') as sports_list:
            json.dump(r_data, sports_list, indent=2)
        return r_data


class ActionPlayerInfo(Action):

    def name(self):
        return "action_player_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        
        print("action_player_info")
        print(tracker.slots)
        sports_db = TheSportsDB()
        # print(tracker.latest_message["entities"])
        name = tracker.slots['player_name'] if tracker.slots['player_name'] else list(filter(lambda entity: entity['entity'] == 'PERSON', tracker.latest_message["entities"])) # tracker.get_slot('player_name')
        choice = tracker.slots['choice_list'] if tracker.slots['choice_list'] else list(filter(lambda entity: entity['entity'] == 'ORDINAL' or  entity['entity'] == 'choice', tracker.latest_message["entities"])) # tracker.get_slot('choice_list')
        
        if len(name) >= 1 and not tracker.slots['player_name']:
            # print(name)
            name = name[0]['value']
            SlotSet("player_name", name)        
            # print("name", name)

        if len(choice) >= 1 and not tracker.slots['choice_list']:
            choice = choice[0]['value']
            SlotSet("choice_list", choice)
            # print("choice", choice)

        if name is None or (name is not None and len(name) == 0):
            dispatcher.utter_message(response='utter_no_player')
            return [SlotSet("player_name", None), 
                    SlotSet("choice_list", None)]
        # print("ok", name)
        dispatcher.utter_message(response='utter_searching')
        players = sports_db.search_player(name)['player']
        # print("ok 2", players)
        # checking for empty results
        if players is None:
            dispatcher.utter_message(response='utter_no_player_name', player_name=name)
            return [SlotSet("player_name", None), 
                    SlotSet("choice_list", None)]
        
        choice_map = {
            "first": 0,
            "second": 1,
            "third": 2,
            "fourth": 3,
            "fifth": 4,
            "last": len(players)-1,
        }

        if choice and choice == "none":
            dispatcher.utter_message(text='Ok')
            return [SlotSet("player_name", None), 
                    SlotSet("choice_list", None)]

        if choice:
            players = sports_db.search_player(players[choice_map[choice.lower()]]['strPlayer'])['player']

        if players is None or len(players) == 0:
            dispatcher.utter_message(text="Sorry, I have no idea of who {} is.".format(name))
        
        elif len(players) > 1:
            exact_match = None
            # just getting the 5 results
            for player in players[:5]:
                reg = REGEX_EXACT_MATCH.format(name)
                # print("regex", reg)
                if re.match(reg, player['strPlayer'], re.IGNORECASE):
                    exact_match = player
                    break

            # print("Exact Match", exact_match)
            if exact_match:
                dispatcher.utter_message(text="{}".format(exact_match['strDescriptionEN'].split("\n")[0].split('. ')[0]))
                dispatcher.utter_message(response='utter_more_questions')
            else:
                dispatcher.utter_message(text="I got more than one result:")
                for player in players[:5]:
                    dispatcher.utter_message(text='{},'.format(player['strPlayer']))
                dispatcher.utter_message(text="Which one do you want to know more about?")
                return [SlotSet("player_name", name)]
        else:
            # dispatcher.utter_message(text="{} plays {}".format(name, players[0]['strSport']))
            if players[0]['strDescriptionEN'] is not None:
                dispatcher.utter_message(text="{}".format(players[0]['strDescriptionEN'].split("\n")[0].split('. ')[0]))
            else:
                dispatcher.utter_message(text="No information available.")
            # dispatcher.utter_message(response='utter_more_questions')

        return [] if len(players) > 1 else [SlotSet("player_name", None), 
                                            SlotSet("choice_list", None)]


class ActionBornDate(Action):

    def name(self):
        return "action_player_born_date"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        
        print("action_player_born_date")

        sports_db = TheSportsDB()
        name = tracker.slots['player_name'] if tracker.slots['player_name'] else list(filter(lambda entity: entity['entity'] == 'PERSON', tracker.latest_message["entities"])) # tracker.get_slot('player_name')
        choice = tracker.slots['choice_list'] if tracker.slots['choice_list'] else list(filter(lambda entity: entity['entity'] == 'ORDINAL' or  entity['entity'] == 'choice', tracker.latest_message["entities"])) # tracker.get_slot('choice_list')
        
        if len(name) >= 1 and not tracker.slots['player_name']:
            name = name[0]['value']
            SlotSet("player_name", name)        
        if len(choice) >= 1 and not tracker.slots['choice_list']:
            choice = choice[0]['value']
            SlotSet("choice_list", choice)

        print(tracker.slots)

        if name is None or (name is not None and len(name) == 0):
            dispatcher.utter_message(response='utter_no_player')
            return [SlotSet("player_name", None), 
                    SlotSet("choice_list", None)]

        dispatcher.utter_message(response='utter_searching')
        players = sports_db.search_player(name)['player']

        # checking for empty results
        if players is None:
            dispatcher.utter_message(response='utter_no_player_name', player_name=name)
            return [SlotSet("player_name", None), 
                    SlotSet("choice_list", None)]
        
        choice_map = {
            "first": 0,
            "second": 1,
            "third": 2,
            "fourth": 3,
            "fifth": 4,
            "last": len(players)-1,
        }

        if choice and choice == "none":
            dispatcher.utter_message(text='Ok')
            return [SlotSet("player_name", None), 
                    SlotSet("choice_list", None)]

        if choice:
            players = sports_db.search_player(players[choice_map[choice.lower()]]['strPlayer'])['player']

        if players is None or len(players) == 0:
            dispatcher.utter_message(text="Sorry, I have no idea of who {} is.".format(name))
        
        elif len(players) > 1:
            exact_match = None
            # just getting the 5 results
            for player in players[:5]:
                reg = REGEX_EXACT_MATCH.format(name)
                print("regex", reg)
                if re.match(reg, player['strPlayer'], re.IGNORECASE):
                    exact_match = player
                    break

            # print("Exact Match", exact_match)
            if exact_match:
                dispatcher.utter_message(text="{} was born on {}".format(name, exact_match['dateBorn']))
                dispatcher.utter_message(response='utter_more_questions')
            else:
                dispatcher.utter_message(text="I got more than one result:")
                for player in players[:5]:
                    dispatcher.utter_message(text='{},'.format(player['strPlayer']))
                dispatcher.utter_message(text="Which one do you want to know more about?")
                return [SlotSet("player_name", name)]
        else:
            # dispatcher.utter_message(text="{} plays {}".format(name, players[0]['strSport']))
            if players[0]['dateBorn'] is not None:
                dispatcher.utter_message(text="{} was born on {}".format(name, players[0]['dateBorn']))
            else:
                dispatcher.utter_message(text="No description available.")
            # dispatcher.utter_message(response='utter_more_questions')

        return [] if len(players) > 1 else [SlotSet("player_name", None), 
                                            SlotSet("choice_list", None)]

class ActionPlayerSport(Action):

    def name(self):
        return "action_player_sport"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        
        print("action_player_sport")

        sports_db = TheSportsDB()
        name = tracker.slots['player_name'] if tracker.slots['player_name'] else list(filter(lambda entity: entity['entity'] == 'PERSON', tracker.latest_message["entities"])) # tracker.get_slot('player_name')
        choice = tracker.slots['choice_list'] if tracker.slots['choice_list'] else list(filter(lambda entity: entity['entity'] == 'ORDINAL' or  entity['entity'] == 'choice', tracker.latest_message["entities"])) # tracker.get_slot('choice_list')
        
        if len(name) >= 1 and not tracker.slots['player_name']:
            name = name[0]['value']
            SlotSet("player_name", name)        
        if len(choice) >= 1 and not tracker.slots['choice_list']:
            choice = choice[0]['value']
            SlotSet("choice_list", choice)

        print(tracker.slots)

        if name is None or (name is not None and len(name) == 0):
            dispatcher.utter_message(response='utter_no_player')
            return [SlotSet("player_name", None), 
                    SlotSet("choice_list", None)]

        dispatcher.utter_message(response='utter_searching')
        players = sports_db.search_player(name)['player']

        # checking for empty results
        if players is None:
            dispatcher.utter_message(response='utter_no_player_name', player_name=name)
            return [SlotSet("player_name", None), 
                    SlotSet("choice_list", None)]
        
        choice_map = {
            "first": 0,
            "second": 1,
            "third": 2,
            "fourth": 3,
            "fifth": 4,
            "last": len(players)-1,
        }

        if choice and choice == "none":
            dispatcher.utter_message(text='Ok')
            return [SlotSet("player_name", None), 
                    SlotSet("choice_list", None)]

        if choice:
            players = sports_db.search_player(players[choice_map[choice.lower()]]['strPlayer'])['player']

        if players is None or len(players) == 0:
            dispatcher.utter_message(text="Sorry, I have no idea of who {} is.".format(name))
        
        elif len(players) > 1:
            exact_match = None
            # just getting the 5 results
            for player in players[:5]:
                reg = REGEX_EXACT_MATCH.format(name)
                print("regex", reg)
                if re.match(reg, player['strPlayer'], re.IGNORECASE):
                    exact_match = player
                    break

            # print("Exact Match", exact_match)
            if exact_match:
                dispatcher.utter_message(text="{} plays {}".format(name, exact_match['strSport']))
                dispatcher.utter_message(response='utter_more_questions')
            else:
                dispatcher.utter_message(text="I got more than one result:")
                for player in players[:5]:
                    dispatcher.utter_message(text='{},'.format(player['strPlayer']))
                dispatcher.utter_message(text="Which one do you want to know more about?")
                return [SlotSet("player_name", name)]
        else:
            # dispatcher.utter_message(text="{} plays {}".format(name, players[0]['strSport']))
            if players[0]['strSport'] is not None:
                dispatcher.utter_message(text="{} plays {}".format(name, players[0]['strSport']))
            else:
                dispatcher.utter_message(text="No description available.")
            # dispatcher.utter_message(response='utter_more_questions')

        return [] if len(players) > 1 else [SlotSet("player_name", None), 
                                            SlotSet("choice_list", None)]


class ActionPlayerHeight(Action):

    def name(self):
        return "action_player_height"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        
        print("action_player_height")

        sports_db = TheSportsDB()
        # print(tracker.latest_message["entities"])
        name = tracker.slots['player_name'] if tracker.slots['player_name'] else list(filter(lambda entity: entity['entity'] == 'PERSON', tracker.latest_message["entities"])) # tracker.get_slot('player_name')
        choice = tracker.slots['choice_list'] if tracker.slots['choice_list'] else list(filter(lambda entity: entity['entity'] == 'ORDINAL' or  entity['entity'] == 'choice', tracker.latest_message["entities"])) # tracker.get_slot('choice_list')
        
        if len(name) >= 1 and not tracker.slots['player_name']:
            name = name[0]['value']
            SlotSet("player_name", name)        
        if len(choice) >= 1 and not tracker.slots['choice_list']:
            choice = choice[0]['value']
            SlotSet("choice_list", choice)

        print(tracker.slots)

        if name is None or (name is not None and len(name) == 0):
            dispatcher.utter_message(response='utter_no_player')
            return [SlotSet("player_name", None), 
                    SlotSet("choice_list", None)]

        dispatcher.utter_message(response='utter_searching')
        players = sports_db.search_player(name)['player']

        # checking for empty results
        if players is None:
            dispatcher.utter_message(response='utter_no_player_name', player_name=name)
            return [SlotSet("player_name", None), 
                    SlotSet("choice_list", None)]
        
        choice_map = {
            "first": 0,
            "second": 1,
            "third": 2,
            "fourth": 3,
            "fifth": 4,
            "last": len(players)-1,
        }

        if choice and choice == "none":
            dispatcher.utter_message(text='Ok')
            return [SlotSet("player_name", None), 
                    SlotSet("choice_list", None)]

        if choice:
            players = sports_db.search_player(players[choice_map[choice.lower()]]['strPlayer'])['player']

        if players is None or len(players) == 0:
            dispatcher.utter_message(text="Sorry, I have no idea of who {} is.".format(name))
        
        elif len(players) > 1:
            exact_match = None
            # just getting the 5 results
            for player in players[:5]:
                reg = REGEX_EXACT_MATCH.format(name)
                print("regex", reg)
                if re.match(reg, player['strPlayer'], re.IGNORECASE):
                    exact_match = player
                    break

            # print("Exact Match", exact_match)
            if exact_match:
                dispatcher.utter_message(text="{}".format(exact_match['strHeight'].split("\n")[0]))
                dispatcher.utter_message(response='utter_more_questions')
            else:
                dispatcher.utter_message(text="I got more than one result:")
                for player in players[:5]:
                    dispatcher.utter_message(text='{},'.format(player['strPlayer']))
                dispatcher.utter_message(text="Which one do you want to know more about?")
                return [SlotSet("player_name", name)]
        else:
            # dispatcher.utter_message(text="{} plays {}".format(name, players[0]['strSport']))
            if players[0]['strHeight'] is not None:
                dispatcher.utter_message(text="{}".format(players[0]['strHeight'].split("\n")[0]))
            else:
                dispatcher.utter_message(text="No description available.")
            # dispatcher.utter_message(response='utter_more_questions')

        return [] if len(players) > 1 else [SlotSet("player_name", None), 
                                            SlotSet("choice_list", None)]

class ActionPlayerPlaysInTeam(Action):
    
    def name(self):
        return "action_player_plays_in_team"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):

        print("action_player_plays_in_team")
        
        sports_db = TheSportsDB()
        print(tracker.slots)
        print(tracker.latest_message["entities"])
        # reading slot
        name = tracker.slots['player_name'] if tracker.slots['player_name'] else list(filter(lambda entity: entity['entity'] == 'PERSON', tracker.latest_message["entities"])) # tracker.get_slot('player_name')
        team_name = tracker.slots['team_name'] if tracker.slots['team_name'] else list(filter(lambda entity: entity['entity'] == 'ORG', tracker.latest_message["entities"])) # tracker.get_slot('team_name')
        choice = tracker.slots['choice_list'] if tracker.slots['choice_list'] else list(filter(lambda entity: entity['entity'] == 'ORDINAL' or  entity['entity'] == 'choice', tracker.latest_message["entities"])) # tracker.get_slot('choice_list')
        
        if len(name) >= 1 and not tracker.slots['player_name']:
            name = name[0]['value']
            SlotSet("player_name", name)
        if len(team_name) >= 1 and not tracker.slots['team_name']:
            team_name = team_name[0]['value']
            SlotSet("team_name", team_name)
        if len(choice) >= 1 and not tracker.slots['choice_list']:
            choice = choice[0]['value']
            SlotSet("choice_list", choice)

        # managing empty slots
        if name is None or (name is not None and len(name) == 0):
            dispatcher.utter_message(response='utter_no_player')
            return [SlotSet("team_name", team_name)]
        if team_name is None or (team_name is not None and len(team_name) == 0):
            dispatcher.utter_message(response='utter_no_team')
            return [SlotSet("player_name", name)]

        dispatcher.utter_message(response='utter_searching')

        # searching for data
        players = sports_db.search_player(name)['player']
        teams = sports_db.search_team_by_name(team_name)['teams']
       
        # checking for empty results
        if players is None:
            dispatcher.utter_message(response='utter_no_player_name', player_name=name)
            return [SlotSet("player_name", None), 
                    SlotSet("choice_list", None)]
        if teams is None:
            dispatcher.utter_message(response='utter_no_team_name', team_name=team_name)
            return [SlotSet("player_name", None), 
                    SlotSet("choice_list", None)]

        # map for disag
        choice_map = {
            "first": 0,
            "second": 1,
            "third": 2,
            "fourth": 3,
            "fifth": 4,
            "last": len(players)-1,
        }

        if choice and choice == "none":
            dispatcher.utter_message(text='Ok')
            return [SlotSet("player_name", None), 
                    SlotSet("choice_list", None)]

        # if choice select player
        if choice and choice.lower() in choice_map.keys():
            players = sports_db.search_player(players[choice_map[choice.lower()]]['strPlayer'])['player']
        elif choice and choice.lower() not in choice_map.keys():
            dispatcher.utter_message(response='utter_negative_player_plays_in_team', player_name=name, team_name=team_name)
            return [SlotSet("player_name", None), 
                    SlotSet("choice_list", None)]
    
        print(len(players), len(teams))
        if len(players) == 1 and len(teams) >= 1:

            for team in teams:
                if team['idTeam'] == players[0]['idTeam']:
                    dispatcher.utter_message(response='utter_affermative_player_plays_in_team', player_name=name, team_name=team_name)
                    return [SlotSet("player_name", None), 
                            SlotSet("choice_list", None)]
            
            # player is not in the team
            dispatcher.utter_message(response='utter_negative_player_plays_in_team', player_name=name, team_name=team_name)
            return [SlotSet("player_name", None), 
                    SlotSet("choice_list", None)]

        elif len(players) > 1:
            dispatcher.utter_message(text="I got more than one result for {}:".format(name))
            for player in players[:5]:
                dispatcher.utter_message(text='{},'.format(player['strPlayer']))
            dispatcher.utter_message(text="Which one do you mean?")
            return [SlotSet("player_name", name), SlotSet("team_name", team_name)]
        else:
            # need to check 
            dispatcher.utter_message(response='utter_negative_player_plays_in_team', player_name=name, team_name=team_name)
        
        return [SlotSet("player_name", None), 
                SlotSet("choice_list", None)] # if len(players) == 0 or len(teams) == 0 else []


class ActionUpcomingEvents(Action):

    def name(self):
        return "action_upcoming_events"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        
        print("action_upcoming_events")

        sports_db = TheSportsDB()
        print(tracker.latest_message["entities"])
        print(tracker.slots)
        name = list(filter(lambda entity: entity['entity'] == 'ORG', tracker.latest_message["entities"])) # tracker.get_slot('player_name')
        choice = list(filter(lambda entity: entity['entity'] == 'ORDINAL' or  entity['entity'] == 'choice', tracker.latest_message["entities"])) # tracker.get_slot('choice_list')
        
        if len(name) >= 1:
            name = name[0]['value']
            SlotSet("team_name", name)        
        if len(choice) >= 1:
            choice = choice[0]['value']
            SlotSet("choice_list", choice)

        if name is None or len(name) == 0:
            dispatcher.utter_message(response='utter_no_team')
            return [SlotSet("player_name", None), 
                    SlotSet("choice_list", None)]

        dispatcher.utter_message(response='utter_searching')
        teams = sports_db.search_team_by_name(name)['teams']

        # checking for empty results
        if teams is None:
            dispatcher.utter_message(response='utter_no_team_name', team_name=name)
            return [SlotSet("player_name", None), 
                    SlotSet("choice_list", None)]
        
        choice_map = {
            "first": 0,
            "second": 1,
            "third": 2,
            "fourth": 3,
            "fifth": 4,
            "last": len(teams)-1,
        }

        if choice and choice == "none":
            dispatcher.utter_message(text='Ok')
            return [SlotSet("player_name", None), 
                    SlotSet("choice_list", None)]

        if choice:
            teams = sports_db.search_team_by_name(teams[choice_map[choice.lower()]]['strTeam'])['teams']

        if teams is None or len(teams) == 0:
            dispatcher.utter_message(text="Sorry, I have no idea of what {} is.".format(name))
        
        elif len(teams) > 1:
            exact_match = None
            # just getting the 5 results
            for team in teams[:5]:
                reg = REGEX_EXACT_MATCH.format(name)
                print("regex", reg)
                if re.match(reg, team['strTeam'], re.IGNORECASE):
                    exact_match = team
                    break

            if exact_match:
                dispatcher.utter_message(text="{}".format(exact_match['strHeight'].split("\n")[0]))
                events = sports_db.search_upcoming_events(teams[0]['idTeam'])
                dispatcher.utter_message(text="I got more than one result:")
                for event in events['events']:
                    dispatcher.utter_message(text='{} on {},'.format(event['strEvent'], event['dateEvent']))
                dispatcher.utter_message(response='utter_more_questions')
            else:
                dispatcher.utter_message(text="I got more than one result:")
                for team in teams[:5]:
                    dispatcher.utter_message(text='{},'.format(team['strTeam']))
                dispatcher.utter_message(text="Which one do you want to know more about?")
                return []
        else:
            # dispatcher.utter_message(text="{} plays {}".format(name, teams[0]['strSport']))
            if teams[0]['idTeam'] is not None:
                events = sports_db.search_upcoming_events(teams[0]['idTeam'])
                dispatcher.utter_message(text="I got more than one result:")
                for event in events['events']:
                    dispatcher.utter_message(text='{} on {},'.format(event['strEvent'], event['dateEvent']))
                # dispatcher.utter_message(text="{}".format(teams[0]['strHeight'].split("\n")[0]))
            else:
                dispatcher.utter_message(text="No description available.")
            # dispatcher.utter_message(response='utter_more_questions')

        return [] if len(teams) > 1 else [SlotSet("player_name", None), 
                                            SlotSet("choice_list", None)]


class ValidateBookingTicketForm(Action):

    def name(self):
        return "validate_booking_ticket_form"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):

        sports_db = TheSportsDB()
        print(tracker.latest_message["entities"])
        print(tracker.slots)

        team_name = tracker.slots['team_name'] if tracker.slots['team_name'] else list(filter(lambda entity: entity['entity'] == 'ORG', tracker.latest_message["entities"]))
        ticket_quantity = tracker.slots['ticket_quantity'] if tracker.slots['ticket_quantity'] else list(filter(lambda entity: entity['entity'] == 'QUANTITY', tracker.latest_message["entities"]))

        if len(team_name) == 0:
            team_name = None

        if len(ticket_quantity) == 0:
            ticket_quantity = None

        if team_name is not None and len(team_name) >= 1 and not tracker.slots['team_name']:
            print("team_name", team_name)
            teams = sports_db.search_team_by_name(team_name[0]['value'])['teams']
            if teams is None or len(teams) == 0:                
                dispatcher.utter_message(text="No team {} Found.".format(team_name))
                team_name = None
            else:
                team_name = teams[0]['strTeam']     
        if ticket_quantity is not None and len(ticket_quantity) >= 1 and not tracker.slots['ticket_quantity']:
            ticket_quantity = ticket_quantity[0]['value']

        
        if team_name and ticket_quantity:
            found_team = sports_db.search_team_by_name(team_name)['teams']
            if found_team is not None:                
                events = sports_db.search_upcoming_events(found_team[0]['idTeam'])
            else:
                events = None
            if events is not None and len(events) > 0:
                dispatcher.utter_message(response='utter_booking_confirmation', event_name=events['events'][0]['strEvent'], ticket_quantity=ticket_quantity)
                # dispatcher.utter_message(response='utter_booking_confirmed', event_name=events[0]['strEvent'], ticket_quantity=ticket_quantity)
                return [SlotSet('team_name', None),
                        SlotSet('ticket_quantity', None), 
                        ActiveLoop(None)]
            else:
                dispatcher.utter_message(text='Sorry, I cannot book because there are no upcoming events')
                return [SlotSet('team_name', None),
                        SlotSet('ticket_quantity', None), 
                        ActiveLoop(None)]

        return [SlotSet('team_name', team_name if team_name else None),
                SlotSet('ticket_quantity', ticket_quantity if ticket_quantity else None)]