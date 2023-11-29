from unionfind import UnionFind
from meta import GameMeta
from random import choice

class GameState:
    """
    Stores information representing the current state of a game of hex, namely
    the board and the current turn. Also provides functions for playing game.
    """
    # dictionary associating numbers with players
    # PLAYERS = {"none": 0, "red": 1, "blue": 2}

    # move value of -1 indicates the game has ended so no move is possible
    # GAME_OVER = -1

    # represent edges in the union find structure for detecting the connection
    # for player 1 Edge1 is high and EDGE2 is low
    # for player 2 Edge1 is left and EDGE2 is right

    # neighbor_patterns = ((-1, 0), (0, -1), (-1, 1), (0, 1), (1, 0), (1, -1))

    def __init__(self, board_size, colour):
        """
        Initialize the game board and give red first turn.
        Also create our union find structures for win checking.

        Args:
            size (int): The board size
        """
        colourMap = {"R": GameMeta.PLAYERS["red"], "B": GameMeta.PLAYERS["blue"]}
        self.to_play = GameMeta.PLAYERS['red']
        self.board_size = board_size
        self.board = [[GameMeta.PLAYERS['none'] for i in range(board_size)] for i in range(board_size)]
        self.colour = colourMap[colour] # string
        self.turn_count = 0

        self.red_played = 0
        self.blue_played = 0
        self.red_groups = UnionFind()
        self.blue_groups = UnionFind()
        self.red_groups.set_ignored_elements([GameMeta.EDGE1, GameMeta.EDGE2])
        self.blue_groups.set_ignored_elements([GameMeta.EDGE1, GameMeta.EDGE2])

    def play(self, cell: tuple) -> None:
        """
        Play a stone of the player that owns the current turn in input cell.
        Args:
            cell (tuple): row and column of the cell
        """
        # self.board[cell[0]][cell[1]] = self.colour
        # self.colour = self.opp_colour()
        # print("PLAY: ", cell)
        if self.to_play == GameMeta.PLAYERS['red']:
            self.place_red(cell)
            self.to_play = GameMeta.PLAYERS['blue']
        elif self.to_play == GameMeta.PLAYERS['blue']:
            self.place_blue(cell)
            self.to_play = GameMeta.PLAYERS['red']

    def place_red(self, cell: tuple) -> None:
        """
        Place a red stone regardless of whose turn it is.

        Args:
            cell (tuple): row and column of the cell
        """
        x, y = cell
        if self.board[x][y] == GameMeta.PLAYERS['none']:
            self.board[x][y] = GameMeta.PLAYERS['red']
            self.red_played += 1
        else:
            print("INVALID MOVE: ", (x, y))
            print(self)
            raise ValueError("Cell occupied")
        # if the placed cell touches a red edge connect it appropriately
        if cell[0] == 0:
            self.red_groups.join(GameMeta.EDGE1, cell)
        if cell[0] == self.board_size - 1:
            self.red_groups.join(GameMeta.EDGE2, cell)
        # join any groups connected by the new red stone
        for n in self.neighbors(cell):
            x2, y2 = n
            if self.board[x2][y2] == GameMeta.PLAYERS['red']:
                self.red_groups.join(n, cell)

    def place_blue(self, cell: tuple) -> None:
        """
        Place a blue stone regardless of whose turn it is.

        Args:
            cell (tuple): row and column of the cell
        """
        x, y = cell
        if self.board[x][y] == GameMeta.PLAYERS['none']:
            self.board[x][y] = GameMeta.PLAYERS['blue']
            self.blue_played += 1
        else:
            print("INVALID MOVE: ", (x, y))
            print(self)
            raise ValueError("Cell occupied")
        # if the placed cell touches a blue edge connect it appropriately
        if cell[1] == 0:
            self.blue_groups.join(GameMeta.EDGE1, cell)
        if cell[1] == self.board_size - 1:
            self.blue_groups.join(GameMeta.EDGE2, cell)
        # join any groups connected by the new blue stone
        for n in self.neighbors(cell):
            x2, y2 = n
            if self.board[x2][y2] == GameMeta.PLAYERS['blue']:
                self.blue_groups.join(n, cell)

    def get_num_played(self) -> dict:
        return {'red': self.red_played, 'blue': self.blue_played}

    def would_lose(self, cell: tuple, color: int) -> bool:
        # TODO: use UnionFind to detect if player has won/lost
        pass

    def neighbors(self, cell: tuple) -> list:
        """
        Return list of neighbors of the passed cell.

        Args:
            cell tuple):
        """
        x = cell[0]
        y = cell[1]
        return [(n[0] + x, n[1] + y) for n in GameMeta.NEIGHBOR_PATTERNS
                if (0 <= n[0] + x < self.board_size and 0 <= n[1] + y < self.board_size)]

    def moves(self) -> list:
        """
        Get a list of all moves possible on the current board.
        """
        # print("board: ", self)
        moves = []
        for y in range(self.board_size):
            for x in range(self.board_size):
                if self.board[x][y] == GameMeta.PLAYERS['none']:
                    moves.append((x, y))
        # print(f"POSSIBLE MOVES: {moves}")
        return moves
    
    def turn(self) -> int:
        """
        Return the player with the next move.
        """
        return self.to_play
    
    def opp_colour(self):
        """Returns the char representation of the colour opposite to the
        current one.
        """
        if self.colour == GameMeta.PLAYERS['red']:
            return GameMeta.PLAYERS['blue']
        elif self.colour == GameMeta.PLAYERS['blue']:
            return GameMeta.PLAYERS['red']
        else:
            return GameMeta.PLAYERS['none']
        
    @property
    def winner(self) -> int:
        """
        Return a number corresponding to the winning player,
        or none if the game is not over.
        """
        if self.red_groups.connected(GameMeta.EDGE1, GameMeta.EDGE2):
            return GameMeta.PLAYERS['red']
        elif self.blue_groups.connected(GameMeta.EDGE1, GameMeta.EDGE2):
            return GameMeta.PLAYERS['blue']
        else:
            return GameMeta.PLAYERS['none']


    def __str__(self):
        """
        Print an ascii representation of the game board.
        Notes:
            Used for gtp interface
        """
        red = 'R'
        blue = 'B'
        empty = '.'
        ret = '\n'
        coord_size = len(str(self.board_size))
        offset = 1
        ret += ' ' * (offset + 1)
        for x in range(self.board_size):
            ret += chr(ord('A') + x) + ' ' * offset * 2
        ret += '\n'
        for y in range(self.board_size):
            ret += str(y + 1) + ' ' * (offset * 2 + coord_size - len(str(y + 1)))
            for x in range(self.board_size):
                if self.board[x][y] == GameMeta.PLAYERS['red']:
                    ret += red
                elif self.board[x][y] == GameMeta.PLAYERS['blue']:
                    ret += blue
                else:
                    ret += empty
                ret += ' ' * offset * 2
            ret += red + "\n" + ' ' * offset * (y + 1)
        ret += ' ' * (offset * 2 + 1) + (blue + ' ' * offset * 2) * self.board_size
        return ret