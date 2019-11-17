# FastCity
<img src="/images/logo.png" width=300/>

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

The main effort in 1 and 2 is to make learning in step 3 easier, and faster. The imitation learning and DAgger has shown number of success in both practice and acedemia in recent years.

