# Adapted from https://github.com/keras-rl/keras-rl/blob/master/examples/dqn_atari.py
from __future__ import division
import argparse

from PIL import Image
import numpy as np
import os
import gym

from keras.models import Sequential
from keras.layers import Dense, Activation, Dropout, Flatten, Permute, InputLayer
from keras.layers import Convolution2D, MaxPooling2D
from keras.optimizers import Adam
import keras.backend as K

from rl.agents.dqn import DQNAgent
from rl.policy import LinearAnnealedPolicy, BoltzmannQPolicy, EpsGreedyQPolicy
from rl.memory import SequentialMemory
from rl.core import Processor
from rl.callbacks import FileLogger, ModelIntervalCheckpoint
from keras.callbacks import TensorBoard


INPUT_SHAPE = (100, 100)
WINDOW_LENGTH = 8


def center_pad_observations(obs, receptor_size=100):
    npad_ = (receptor_size-obs.shape[1])//2 # make sure the receptive field is always 200
    npads = ((0, 0), (npad_, npad_), (npad_, npad_), (0, 0))
    return np.pad(obs, pad_width=npads, mode='constant', constant_values=0)


class SmartCityProcessor(Processor):
    def process_observation(self, observation):
        # print(type(observation))
        # print(observation['0'].shape) # FIXME: implement the abstract method for the environment step
        if isinstance(observation, dict):
            processed_observation = observation['0'] #center_pad_observations(observation)
        else:
            processed_observation = observation

        return processed_observation

    def process_state_batch(self, batch):
        processed_batch = center_pad_observations(batch[0])
        # print(processed_batch.shape)
        # print(len(processed_batch))
        return processed_batch
    
    def process_action(self, action):
        return action


parser = argparse.ArgumentParser()
parser.add_argument('--mode', choices=['train', 'test'], default='train')
parser.add_argument('--env-name', type=str, default='fastcity')
parser.add_argument('--weights', type=str, default=None)
args = parser.parse_args()

# Get the environment and extract the number of actions.
from client import CarDirection, Client
from env import JunctionEnvironment
team_name = "ipa"
team_key = "admin"
client = Client(team_name=team_name, team_key=team_key)
env = JunctionEnvironment(client)
# env = gym.make(args.env_name)
np.random.seed(123)
env.seed(123)
nb_actions = env.action_space.n
print(nb_actions)

# Next, we build our model. We use the same model that was described by Mnih et al. (2015).
input_shape = (100,100,8) #(WINDOW_LENGTH,) + INPUT_SHAPE
model = Sequential()
# if K.image_dim_ordering() == 'tf':
    # # (width, height, channels)
    # print("tf ran")
    # # model.add(Permute((2, 3, 1), input_shape=input_shape))
# elif K.image_dim_ordering() == 'th':
    # # (channels, width, height)
    # model.add(Permute((1, 2, 3), input_shape=input_shape))
# else:
    # raise RuntimeError('Unknown image_dim_ordering.')

# model.add(Convolution2D(32, (8, 8), strides=(4, 4), input_shape=input_shape))
# model.add(Activation('relu'))
# model.add(Convolution2D(64, (4, 4), strides=(2, 2)))
# model.add(Activation('relu'))
# model.add(Convolution2D(64, (3, 3), strides=(1, 1)))
# model.add(Activation('relu'))
# model.add(Flatten())
# model.add(Dense(512))
# model.add(Activation('relu'))
# model.add(Dense(nb_actions))
# model.add(Activation('linear'))
def create_model_1():
    model = Sequential()

    model.add(Convolution2D(32, 8, 8, border_mode='same',
                            input_shape=input_shape))
    model.add(Activation('relu'))
    model.add(Convolution2D(32, 8, 8))
    model.add(Activation('relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))

    model.add(Convolution2D(64, 8, 8, border_mode='same'))
    model.add(Activation('relu'))
    model.add(Convolution2D(64, 8, 8))
    model.add(Activation('relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))

    model.add(Convolution2D(128, 8, 8, border_mode='same'))
    model.add(Activation('relu'))
    model.add(Convolution2D(128, 8, 8))
    model.add(Activation('relu'))
    model.add(MaxPooling2D(pool_size=(2, 2)))
    model.add(Dropout(0.25))

    model.add(Flatten())
    model.add(Dense(256))
    model.add(Activation('relu'))
    model.add(Dropout(0.5))
    model.add(Dense(nb_actions, activation='softmax'))
    return model

model = create_model_1()

print(model.summary())

# Finally, we configure and compile our agent. You can use every built-in Keras optimizer and
# even the metrics!
memory = SequentialMemory(limit=1000000, window_length=1)#WINDOW_LENGTH) # FIXME: make the windo length work!
processor = SmartCityProcessor() #AtariProcessor()

# Select a policy. We use eps-greedy action selection, which means that a random action is selected
# with probability eps. We anneal eps from 1.0 to 0.1 over the course of 1M steps. This is done so that
# the agent initially explores the environment (high eps) and then gradually sticks to what it knows
# (low eps). We also set a dedicated eps value that is used during testing. Note that we set it to 0.05
# so that the agent still performs some random actions. This ensures that the agent cannot get stuck.
policy = LinearAnnealedPolicy(EpsGreedyQPolicy(), attr='eps', value_max=1., value_min=.1, value_test=.05,
                              nb_steps=1000000)

# The trade-off between exploration and exploitation is difficult and an on-going research topic.
# If you want, you can experiment with the parameters or use a different policy. Another popular one
# is Boltzmann-style exploration:
# policy = BoltzmannQPolicy(tau=1.)
# Feel free to give it a try!
batch_size = 32
dqn = DQNAgent(model=model, nb_actions=nb_actions, policy=policy, memory=memory,
               processor=processor, nb_steps_warmup=50000, gamma=.99, target_model_update=10000,
               train_interval=4, delta_clip=1., batch_size=batch_size)
dqn.compile(Adam(lr=.00025), metrics=['sparse_categorical_crossentropy', 'accuracy'])

if args.mode == 'train':
    # Okay, now it's time to learn something! We capture the interrupt exception so that training
    # can be prematurely aborted. Notice that now you can use the built-in Keras callbacks!

    # Load weights from previously learned model
    #weights_filename = os.path.join("checkpoints", "dqn", f'dqn_{args.env_name}_weights.h5f')
    if args.weights: # or from direct path e.g. from the imitated model
        weights_filename = args.weights
        dqn.load_weights(weights_filename)
        print(f"Loaded weights from {weights_filename}")

    # Path to save weights learned
    dagger_experiment = np.random.randint(0, 1000000)
    weights_filename = os.path.join("checkpoints", "dqn", f'dqn_{args.env_name}_weights.h5f')
    checkpoint_dir = os.path.dirname(weights_filename)
    checkpoint_weights_filename = 'dqn_' + args.env_name + '_weights_{step}.h5f'
    log_filename = 'dqn_{}_log.json'.format(args.env_name)
    callbacks = [ModelIntervalCheckpoint(checkpoint_weights_filename, interval=250000)]
    callbacks += [FileLogger(log_filename, interval=100)]
    callbacks += [TensorBoard(log_dir=f'./logs/dagger_{dagger_experiment}', batch_size=batch_size)]
    dqn.fit(env, callbacks=callbacks, nb_steps=1750000, log_interval=10000)

    # After training is done, we save the final weights one more time.
    dqn.save_weights(weights_filename, overwrite=True)

    # Finally, evaluate our algorithm for 10 episodes.
    dqn.test(env, nb_episodes=10, visualize=False)
elif args.mode == 'test':
    weights_filename = f'dqn_{args.env_name}_weights.h5f'
    if args.weights:
        weights_filename = args.weights
    dqn.load_weights(weights_filename)
    dqn.test(env, nb_episodes=10, visualize=True)