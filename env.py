import gym
import numpy as np

from scipy.spatial.distance import cityblock
from gym import spaces
from client import CarDirection, Client


class JunctionEnvironment(gym.Env):
    r"""The main OpenAI Gym class. It encapsulates an environment with
        arbitrary behind-the-scenes dynamics. An environment can be
        partially or fully observed.

        The main API methods that users of this class need to know are:

            step
            reset
            render
            close
            seed

        And set the following attributes:

            action_space: The Space object corresponding to valid actions
            observation_space: The Space object corresponding to valid observations
            reward_range: A tuple corresponding to the min and max possible rewards

        Note: a default reward range set to [-inf,+inf] already exists. Set it if you want a narrower range.

        The methods are accessed publicly as "step", "reset", etc.. The
        non-underscored versions are wrapper methods to which we may add
        functionality over time.
        """

    def __init__(self, car_id: str, client: Client):
        super().__init__()

        self.car_id = str(car_id)
        self.client = client

        self.reward_range = (-float('inf'), float('inf'))
        self._setup()

    def _setup(self):
        world = self.client.get_world()
        if not world:
            self.client.start_game()
            world = self.client.get_world()

        # north, east, south, west, nothing
        self.action_space = spaces.Discrete(5)
        self.width = world["height"]
        self.height = world["width"]

        self.observation_space = spaces.Box(low=0, high=100, shape=(self.height, self.width, 8), dtype=np.uint8)

    def step(self, action):
        """Run one timestep of the environment's dynamics. When end of
        episode is reached, you are responsible for calling `reset()`
        to reset this environment's state.

        Accepts an action and returns a tuple (observation, reward, done, info).

        Args:
            action (object): an action provided by the agent

        Returns:
            observation (object): agent's observation of the current environment
            reward (float) : amount of reward returned after previous action
            done (bool): whether the episode has ended, in which case further step() calls will return undefined results
            info (dict): contains auxiliary diagnostic information (helpful for debugging, and sometimes learning)
        """
        if action < 4:
            self.client.move_car(self.car_id, CarDirection(action))
        else:
            # Do nothing (stay)
            pass

        obs = self.__process_observations(self.client.get_world())
        reward = self.client.get_score()
        done = "grid" in obs
        info = {}
        return obs, reward, done, info

    def reset(self):
        """Resets the state of the environment and returns an initial observation.

        Returns:
            observation (object): the initial observation.
        """
        self.client.stop_game()
        self.client.start_game()
        self._setup()
        return self.__process_observations(self.client.get_world())

    def render(self, mode='human'):
        """Renders the environment.

        The set of supported modes varies per environment. (And some
        environments do not support rendering at all.) By convention,
        if mode is:

        - human: render to the current display or terminal and
          return nothing. Usually for human consumption.
        - rgb_array: Return an numpy.ndarray with shape (x, y, 3),
          representing RGB values for an x-by-y pixel image, suitable
          for turning into a video.
        - ansi: Return a string (str) or StringIO.StringIO containing a
          terminal-style text representation. The text can include newlines
          and ANSI escape sequences (e.g. for colors).

        Note:
            Make sure that your class's metadata 'render.modes' key includes
              the list of supported modes. It's recommended to call super()
              in implementations to use the functionality of this method.

        Args:
            mode (str): the mode to render with

        Example:

        class MyEnv(Env):
            metadata = {'render.modes': ['human', 'rgb_array']}

            def render(self, mode='human'):
                if mode == 'rgb_array':
                    return np.array(...) # return RGB frame suitable for video
                elif mode == 'human':
                    ... # pop up a window and render
                else:
                    super(MyEnv, self).render(mode=mode) # just raise an exception
        """
        raise NotImplementedError

    def close(self):
        """Override close in your subclass to perform any necessary cleanup.

        Environments will automatically close() themselves when
        garbage collected or when the program exits.
        """
        self.client.stop_game()

    def _index_to_coordinates(self, index):
        x = index % self.width
        y = index // self.width
        return x, y

    def _coordinates_to_index(self, x, y):
        return x + self.width * y

    def __process_observations(self, obs):
        map_space = np.array(obs["grid"]).reshape(self.height, self.width)[::-1, :]
        customers, distance, destinations = self.__process_customers(obs["customers"])
        my_locations, my_avail_capacity = self.__process_myself(obs["cars"])
        others_locations, others_avail_capacity = self.__process_others(obs["cars"])

        return (map_space, customers, distance, destinations,
                my_locations, my_avail_capacity, others_locations, others_avail_capacity)

    def __process_customers(self, customers):
        customers = [c for c in customers.values() if c["status"] == "waiting"]
        customer_matrix = np.zeros((self.height, self.width))
        distance_matrix = np.zeros((self.height, self.width))
        destination_matrix = np.zeros((self.height, self.width))

        for customer in customers:
            origin_x, origin_y = self._index_to_coordinates(customer["origin"])
            destination_x, destionation_y = self._index_to_coordinates(customer["destination"])

            customer_matrix[origin_y, origin_x] = 1
            distance_matrix[origin_y, origin_x] = cityblock((origin_x, origin_y), (destination_x, destionation_y))
            destination_matrix[destionation_y, destination_x] = 1

        return customer_matrix, distance_matrix, destination_matrix

    def __process_myself(self, cars):
        car = [car for car_id, car in cars.items() if str(car_id) == self.car_id][0]

        locations = np.zeros((self.height, self.width))
        x, y = self._index_to_coordinates(car["position"])
        locations[y, x] = 1
        avail_capacity = np.full((self.height, self.width), car["capacity"] - car["used_capacity"])

        return locations, avail_capacity

    def __process_others(self, cars):
        cars = [car for car_id, car in cars.items() if str(car_id) != self.car_id]

        locations = np.zeros((self.height, self.width))
        avail_capacity = np.zeros((self.height, self.width))
        for car in cars:
            x, y = self._index_to_coordinates(car["position"])
            locations[y, x] = 1
            avail_capacity[y, x] = car["capacity"] - car["used_capacity"]

        return locations, avail_capacity

        return self.__add_cars(cars)
