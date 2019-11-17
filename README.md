# FastCity
<img src="/images/logo.png" width=300/>
FastCity; City transportation of the futuer!

This is our repository for the solution with came up with for th HackJunction 2019 Erricson Challenge. In this challenge, we use a combination of classical path finding and assignment algorithm to operate cars in a city to deliver customers. Our goal is to distribute the cars to more customers with least amount of movement as fast as possible which has implications on less ecological footprint and a better service to the customers when it comes to the reality.

# Environment
A grid world environment was provided by the challenge host where a set of cars owned by each team had to pick up randomly generated customers in the world and deliver them to their destinations. The problem has two main aspects:

1. Assignment (of cars to customers)
2. Path Finding/Planning (the optimal route to customer and its destination)

As in reality each car has a capacity and may pick up and deliver multiple customers/passengers at the same time. Delivering customers and not making redundant moves (leaving footprint) rewarded in the simulation.

# Our Solution
This problem could be addressed with different levels of sophistication. We chose to get benefit from classical path planning approaches as a foundation for a more general solution based on Reinforcement Learning. And so our solution is a stack of sub-solutions:

1. A* Path Planning with a Greedy Assignment (baseline)
2. [Imitation Learning](http://ciml.info/dl/v0_99/ciml-v0_99-ch18.pdf) and [DAgger](https://www.cs.cmu.edu/~sross1/publications/Ross-AIStats11-NoRegret.pdf) (A Deep Learning model trained to imitate the baseline)
3. A [DQN](https://en.wikipedia.org/wiki/Q-learning#Variants) [Reinforcement Learning](https://en.wikipedia.org/wiki/Reinforcement_learning) model for decentralized execution inspired by [Atari DQN](https://github.com/keras-rl/keras-rl/blob/master/examples/dqn_atari.py)

The main effort in 1 and 2 is to make learning in step 3 easier, and faster. The imitation learning and DAgger has shown number of successes in both practice and acedemia in recent years. First we create pairs of observations and actions based on the A* algorithm and construct a dataset for supevised learning using these pairs. Then we train a neural network model on these samples. This should give us a performance at least better than random actions. Then this model is used to train a reinforcement learning agent.

### Key Features

Our solution is:
- adaptable with different maps with different sizes and dynamics
- learned in decentralized fashion, each agent is autonomous but communicates with others (as in reality)
- suitable for decentralized execution yet with the possibility for centralizing coordination

### Deployment
Each car is controlled by an instance of the model trained in step 3 which would act as the brain for that agent.


# Structure of the Repo

- `alg_astar.py` (A* algorithm for the baseline
- `env.py` (a reinforcement learning environment developed for the challenge)
- `dqn_fastcity.py` (The final DQN agent)
- `notebooks/` (experiments conducted in Jupter-Notebooks specifically for imitation learning, etc.)
- `visualization/` (a web-based visualizer provided by the challenge host)
- `logs/` (tensorboard log directory, created by script)
- `checkpoints/` (saved model weights, created by script)
- `cache/` (some cached data such as the 
- `images/` (to store some repo related images)


## Future works

- Improve the baseline
- Improve the assignment algorithm
- Work further on the RL agent
