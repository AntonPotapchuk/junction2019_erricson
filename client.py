#!/usr/bin/env python3

import enum
import json
import logging
import random
import time
import requests
import lxml.html as lh


class CarDirection(enum.Enum):
    north = 0
    east = 1
    south = 2
    west = 3


class Client:
    def __init__(self,
                 server_url="http://127.0.0.1:8080",
                 team_key="admin",
                 team_name="",
                 log_level=logging.DEBUG):

        self.server_url = server_url
        self.admin_url = server_url + "/" + team_key
        self.game_start_url = self.admin_url + '/start'
        self.game_stop_url = self.admin_url + '/stop'
        # TODO: Probably, should be self.server_url + f'/{team_name}/api/v1'
        self.api_base_url = self.server_url + f'/api/v1'
        self.world_status_url = self.api_base_url + '/world'
        self.scores_url = self.api_base_url + '/scores'
        self.team_base_url = self.admin_url + '/team'
        self.actions_url = self.api_base_url + '/actions'
        self.team_name = team_name

        self.__token = self.__get_token()
        if not self.__token:
            self.__token = self.__add_team_and_get_token()

    @staticmethod
    def __log_request(method, url, data=None):
        logging.debug(f'Sending {method} request to {url} with data: {data}')

    @staticmethod
    def __log_response(response):
        logging.debug(f'Server responded with status code {response.status_code}, data: {response.text}')

    def __send_get_request(self, url, data=None):
        self.__log_request('GET', url)
        r = requests.get(url)
        self.__log_response(r)
        return r

    def __send_put_request(self, url, data=None):
        self.__log_request('PUT', url, data)
        r = requests.put(url, data)
        self.__log_response(r)

    def __send_post_request(self, url, data=None):
        self.__log_request('POST', url, data)
        if self.__token:
            r = requests.post(url, data, headers={'Authorization': self.__token})
        else:
            r = requests.post(url, data)
        self.__log_response(r)
        return r

    def __get_token(self):
        token = None
        body = self.__send_get_request(self.admin_url)
        # Store the contents of the website under doc
        doc = lh.fromstring(body.text)
        tr_elements = doc.xpath('//tr')
        for e in tr_elements:
            if e[1].text_content() == self.team_name:
                token = e[2].text_content()

        logging.info(f'Added team {self.team_name}')
        return token

    def __add_team_and_get_token(self):
        body = self.__send_post_request(self.team_base_url, {'team_name': self.team_name})

        # Store the contents of the website under doc
        doc = lh.fromstring(body.text)
        tr_elements = doc.xpath('//tr')
        for e in tr_elements:
            if e[1].text_content() == self.team_name:
                token = e[2].text_content()

        logging.info(f'Added team {self.team_name}')
        return token

    def start_game(self):
        self.__send_put_request(self.game_start_url)
        logging.info('Started game')

    def stop_game(self):
        self.__send_put_request(self.game_stop_url)
        logging.info("Stopped game")

    def get_score(self):
        r = requests.get(self.scores_url)
        r = r.json()
        return r[self.team_name]["current"]

    def get_world(self):
        r = requests.get(self.world_status_url)
        world = r.json()

        logging.debug('Updated world data: %s', world)
        return world

    def get_cars(self):
        world = self.get_world()
        return world["cars"]

    def get_team_cars(self):
        cars = self.get_cars()
        team_id = self.get_team_id()
        return [car_id for car_id, car in cars.items() if str(car["team_id"]) == team_id]

    def get_teams(self):
        return self.get_world()["teams"]

    def get_team_id(self):
        teams = self.get_teams()
        return str([team_id for team_id, team in teams.items() if team["name"] == self.team_name][0])

    def move_car(self, car_id, direction):
        logging.debug('Moving car ID %d to the %s', car_id, direction.name)
        request_content = json.dumps({
            'type': 'move',
            'action': {
                'message': 'Moving car ID %s to the %s' % (car_id, direction.name),
                'carId': int(car_id),
                'moveDirection': direction.value
            }
        })
        self.__send_post_request(self.actions_url, request_content)
