import torch
import random
import numpy as np
from collections import deque
from mainAI import SnakeGameAI, Direction, Point
from model import LinearQNet, QTrainer
from plot import plot

MAX_MEMORY = 100000
BATCH_SIZE = 1000
LR = 0.001


class Agent:

    def __init__(self):
        self.n_games = 0
        self.epsilon = 0  # randomness
        self.gamma = 0.9  # must be <1
        self.memory = deque(maxlen=MAX_MEMORY)
        self.model = LinearQNet(14, 256, 3)  # original = 256
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)

    def get_state(self, game):
        head = game.snake[0]
        point_l = Point(head.x - 20, head.y)
        point_r = Point(head.x + 20, head.y)
        point_u = Point(head.x, head.y - 20)
        point_d = Point(head.x, head.y + 20)

        dir_l = game.direction == Direction.LEFT
        dir_r = game.direction == Direction.RIGHT
        dir_u = game.direction == Direction.UP
        dir_d = game.direction == Direction.DOWN

        state = [
            # Danger straight
            (dir_r and game.is_collision(point_r)) or
            (dir_l and game.is_collision(point_l)) or
            (dir_u and game.is_collision(point_u)) or
            (dir_d and game.is_collision(point_d)),


            # danger right
            (dir_u and game.is_collision(point_r)) or
            (dir_d and game.is_collision(point_l)) or
            (dir_l and game.is_collision(point_u)) or
            (dir_r and game.is_collision(point_d)),

            # danger left
            (dir_d and game.is_collision(point_r)) or
            (dir_u and game.is_collision(point_l)) or
            (dir_r and game.is_collision(point_u)) or
            (dir_l and game.is_collision(point_d)),

            (dir_r and game.is_collision_bod(point_r)) or
            (dir_l and game.is_collision_bod(point_l)) or
            (dir_u and game.is_collision_bod(point_u)) or
            (dir_d and game.is_collision_bod(point_d)),

            # danger right
            (dir_u and game.is_collision_bod(point_r)) or
            (dir_d and game.is_collision_bod(point_l)) or
            (dir_l and game.is_collision_bod(point_u)) or
            (dir_r and game.is_collision_bod(point_d)),

            # danger left
            (dir_d and game.is_collision_bod(point_r)) or
            (dir_u and game.is_collision_bod(point_l)) or
            (dir_r and game.is_collision_bod(point_u)) or
            (dir_l and game.is_collision_bod(point_d)),

            # we like to move it move it
            dir_l,
            dir_r,
            dir_u,
            dir_d,

            # we like to food it food it
            game.food.x < game.head.x,
            game.food.x > game.head.x,
            game.food.y < game.head.y,
            game.food.y > game.head.y



        ]

        return np.array(state, dtype=int)

    def remember(self, state, action, reward, next_state, game_over):
        self.memory.append((state, action, reward, next_state, game_over))
        #rint(self.memory)

    def train_long_mem(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE)
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, game_overs = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, game_overs)

    def train_short_mem(self, state, action, reward, next_state, game_over):
        self.trainer.train_step(state, action, reward, next_state, game_over)

    def get_action(self, state):
        self.epsilon = 80 - self.n_games  # the more games we play the smaller epsilon gets, makes it less random
        # over time
        final_move = [0, 0, 0]
        if random.randint(0, 200) < self.epsilon:
            move = random.randint(0, 2)
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            final_move[move] = 1

        return final_move

def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    game = SnakeGameAI()
    while True:
        state_old = agent.get_state(game)

        final_move = agent.get_action(state_old)

        reward, game_over, score = game.play_step(final_move)
        state_new = agent.get_state(game)

        agent.train_short_mem(state_old, final_move, reward, state_new, game_over)

        agent.remember(state_old, final_move, reward, state_new, game_over)

        if game_over:
            game.reset()
            agent.n_games += 1
            agent.train_long_mem()

            if score > record:
                record = score
                agent.model.save()

            print("Game", agent.n_games, "Score", score, "Record:", record)

            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            plot(plot_scores, plot_mean_scores)




if __name__ == "__main__":
    train()
