from math import sqrt, log
from copy import deepcopy
from random import choice, random
from time import time as clock

from TGameState import GameState
from uct_mcstsagent import Node, UctMctsAgent
from meta import *


class RaveNode(Node):
    def __init__(self, move=None, parent=None):
        """
        Initialize a new node with optional move and parent and initially empty
        children list and rollout statistics and unspecified outcome.

        """
        super(RaveNode, self).__init__(move, parent)

    @property
    def value(self, explore: float = MCTSMeta.EXPLORATION, rave_const: float = MCTSMeta.RAVE_CONST) -> float:
        """
        Calculate the UCT value of this node relative to its parent, the parameter
        "explore" specifies how much the value should favor nodes that have
        yet to be thoroughly explored versus nodes that seem to have a high win
        rate.
        Currently explore is set to zero when choosing the best move to play so
        that the move with the highest win_rate is always chosen. When searching
        explore is set to EXPLORATION specified above.

        """
        # unless explore is set to zero, maximally favor unexplored nodes
        if self.N == 0:
            return 0 if explore is 0 else GameMeta.INF
        else:
            # rave valuation:
            alpha = max(0, (rave_const - self.N) / rave_const)
            UCT = self.Q / self.N + explore * sqrt(2 * log(self.parent.N) / self.N)
            AMAF = self.Q_RAVE / self.N_RAVE if self.N_RAVE is not 0 else 0
            return (1 - alpha) * UCT + alpha * AMAF


class RaveMctsAgent(UctMctsAgent):

    def __init__(self, state):
        self.root_state = deepcopy(state)
        self.root = RaveNode()
        self.run_time = 0
        self.node_count = 0
        self.num_rollouts = 0

    def set_gamestate(self, state: GameState) -> None:
        """
        Set the root_state of the tree to the passed gamestate, this clears all
        the information stored in the tree since none of it applies to the new
        state.
        """
        self.root_state = deepcopy(state)
        self.root = RaveNode()

    def move(self, move: tuple) -> None:
        """
        Make the passed move and update the tree appropriately. It is
        designed to let the player choose an action manually (which might
        not be the best action).
        Args:
            move:
        """
        if move in self.root.children:
            child = self.root.children[move]
            child.parent = None
            self.root = child
            self.root_state.play(child.move)
            return

        # if for whatever reason the move is not in the children of
        # the root just throw out the tree and start over
        self.root_state.play(move)
        self.root = RaveNode()

    def search(self, time_budget: int) -> None:
        """
        Search and update the search tree for a specified amount of time in secounds.
        """
        start_time = clock()
        num_rollouts = 0

        # do until we exceed our time budget
        while clock() - start_time < time_budget:
            node, state = self.select_node()
            turn = state.turn()
            outcome, black_rave_pts, white_rave_pts = self.roll_out(state)
            self.backup(node, turn, outcome, black_rave_pts, white_rave_pts)
            num_rollouts += 1
        run_time = clock() - start_time
        node_count = self.tree_size()
        self.run_time = run_time
        self.node_count = node_count
        self.num_rollouts = num_rollouts

    def select_node(self) -> tuple:
        """
        Select a node in the tree to preform a single simulation from.
        """
        node = self.root
        state = deepcopy(self.root_state)

        # stop if we reach a leaf node
        while len(node.children) != 0:
            max_value = max(node.children.values(),
                            key=lambda n:
                            n.value).value
            # descend to the maximum value node, break ties at random
            max_nodes = [n for n in node.children.values() if
                         n.value == max_value]
            node = choice(max_nodes)
            state.play(node.move)

            # if some child node has not been explored select it before expanding
            # other children
            if node.N == 0:
                return node, state

        # if we reach a leaf node generate its children and return one of them
        # if the node is terminal, just return the terminal node
        if self.expand(node, state) and node.children:
            node = choice(list(node.children.values()))
            state.play(node.move)
        return node, state

    @staticmethod
    def expand(parent: RaveNode, state: GameState) -> bool:
        """
        Generate the children of the passed "parent" node based on the available
        moves in the passed gamestate and add them to the tree.

        Returns:
            object:
        """
        children = []
        if state.winner != GameMeta.PLAYERS["none"]:
            # game is over at this node so nothing to expand
            return False

        for move in state.moves():
            children.append(RaveNode(move, parent))

        parent.add_children(children)
        return True

    @staticmethod
    def roll_out(state: GameState) -> tuple:
        """
        Simulate a random game except that we play all known critical
        cells first, return the winning player and record critical cells at the end.

        """
        moves = state.moves()
        while state.winner == GameMeta.PLAYERS["none"] and moves:
            move = choice(moves)
            state.play(move)
            moves.remove(move)

        black_rave_pts = []
        white_rave_pts = []

        for x in range(state.board_size):
            for y in range(state.board_size):
                if state.board[x][y] == GameMeta.PLAYERS["blue"]:
                    black_rave_pts.append((x, y))
                elif state.board[x][y] == GameMeta.PLAYERS["red"]:
                    white_rave_pts.append((x, y))

        return state.winner, black_rave_pts, white_rave_pts

    def backup(self, node: RaveNode, turn: int, outcome: int, black_rave_pts: list, white_rave_pts: list) -> None:
        """
        Update the node statistics on the path from the passed node to root to reflect
        the outcome of a randomly simulated playout.
        """
        # note that reward is calculated for player who just played
        # at the node and not the next player to play
        reward = -1 if outcome == turn else 1

        while node is not None:
            if turn == GameMeta.PLAYERS["red"]:
                for point in white_rave_pts:
                    if point in node.children:
                        node.children[point].Q_RAVE += -reward
                        node.children[point].N_RAVE += 1
            else:
                for point in black_rave_pts:
                    if point in node.children:
                        node.children[point].Q_RAVE += -reward
                        node.children[point].N_RAVE += 1

            node.N += 1
            node.Q += reward
            turn = GameMeta.PLAYERS['red'] if turn == GameMeta.PLAYERS['blue'] else GameMeta.PLAYERS['blue']
            reward = -reward
            node = node.parent
