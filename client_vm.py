import gym
import logging
import numpy as np
import dill as pickle
import os

from threading import Thread, Lock
from time import sleep
from client2 import CarDirection, Client
from env import JunctionEnvironment
from matplotlib import pyplot as plt
from alg_astar import *

logger = logging.getLogger(None)
logger.setLevel(logging.WARNING)

team_name = "turing"
team_key = "gozwislx6txtylar9jsr6i6xkgkafjf8"
N_GAMES = 1

class Runner(Thread):
    def __init__(self, car_id, game_id, env, lock):
        super().__init__()
        self.car_id = car_id
        self.game_id = game_id
        self.env = env
        self.lock = lock
        
        self.prev_obs = None
        
        self.obss = []
        self.scores = []
        self.actions = []
        
        self.current_target = None


    def megaalg(self, obs):
        car_x, car_y = np.where(obs[:,:,4])[0][0], np.where(obs[:,:,4])[1][0]
        customer_positions = []
        customer_dists = []
        paths_to_clients = []
        maze = 1-obs[:,:,0]
        statuses = []

        if obs[:,:,3].sum() > 0:
            # go to destination
            if self.current_target is None:
                self.current_target = np.where(obs[:,:,3])[0][0], np.where(obs[:,:,3])[1][0]
            x, y = self.current_target
            path, _ = search(maze, 1, (car_x, car_y), (x ,y))
            if not path:
                self.current_target = None
                return 4
            target_cell = path[0]
            if len(path)==1:
                self.current_target = None
        else:
            # look for customer

            if obs[:,:,1].sum() == 0:
                return 4
            coords = np.where(obs[:,:,1])

            if self.current_target is None:
                for i in range(len(coords[0])):
                    x, y = coords[0][i], coords[1][i]
                    customer_positions.append((x,y))
                    dist = np.abs(car_x - x) + np.abs(car_y - y)
                    customer_dists.append(dist)
                    path, status = search(maze, 1, (car_x, car_y), (x ,y))
                    paths_to_clients.append(path)
                    statuses.append(status)

                completed_paths = [p for p,s in zip(paths_to_clients, statuses) if s==0]
                if len(completed_paths)>0:
                    min_path = min(completed_paths, key = lambda p: len(p))
                else:
                    min_ind = np.argmin(np.array(customer_dists))
                    min_path = paths_to_clients[min_ind]

                self.current_target = min_path[-1]

                #current_target, path = min(zip(customer_dists, paths_to_clients), key = lambda p: len(p[1]))
                target_cell = min_path[0]
            else:
                x, y = self.current_target
                #print(car_x, car_y)
                path, _ = search(maze, 1, (car_x, car_y), (x ,y))
                if not path:
                    self.current_target = None
                    return 4
                target_cell = path[0]
                if len(path)==1:
                    self.current_target = None

        #print(target_cell, car_x, car_y)
        if target_cell is None:
            return 4
        if target_cell[0] == car_x and target_cell[1] == car_y - 1:
            #return 3
            return 3
        if target_cell[0] == car_x and target_cell[1] == car_y + 1:
            #return 1
            return 1
        if target_cell[0] == car_x - 1 and target_cell[1] == car_y:
            #return 2
            return 2
        if target_cell[0] == car_x + 1 and target_cell[1] == car_y:
            #return 0
            return 0
        return 4

        
    def run(self):
        # Need to do some initial action to fetch observations
        obs, score, done, _ = self.env.step(1, self.car_id)
        self.prev_obs = obs
        
        while True:
            try:
                new_action = self.megaalg(self.prev_obs)
                self.lock.acquire()
                #print(new_action)
                obs, score, done, _ = self.env.step(new_action, self.car_id)
                # print(score, done)
            except Exception as ex:
                # print(f"{self.car_id}: {ex}")
                raise ex
            finally:
                try:
                    self.lock.release()
                except:
                    pass
            if done:
                break

            action = new_action

            self.obss.append(self.prev_obs)
            self.scores.append(score)
            self.actions.append(action)

            self.prev_obs = obs                
           # sleep(0.5) 
        
        self.obss = np.array(self.obss)
        self.scores = np.array(self.scores)
        self.actions = np.array(self.actions)

        print('Max score:', max(self.scores))
        print('Last score:', self.scores[-1])


game_ids = []

if __name__ == "__main__":
    print("In main thread")
    client = Client(team_name=team_name, team_key=team_key)
    env = JunctionEnvironment(client)

    lock = Lock()

    i=0
    while True:
        print("Running game", i)
        i += 1
        game_id = i
        msg = env.reset()
        if msg is None:
            sleep(1)
            print('Sleeping...')
            continue

        processes = []
        for car_id in env.car_ids:
            process = Runner(car_id, game_id, env, lock)
            processes.append(process)
            

        for process in processes:
            process.start()

        for process in processes:
            process.join()
        print(f"Game {i} finished")
        game_ids.append(game_id)
        
