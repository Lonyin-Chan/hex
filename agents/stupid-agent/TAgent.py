import socket
from random import choice
from time import sleep
from TGameState import GameState
from uct_mcstsagent import UctMctsAgent



class Agent():
    """This class describes the default Hex agent. It will randomly send a
    valid move at each turn, and it will choose to swap with a 50% chance.
    """

    HOST = "127.0.0.1"
    PORT = 1234

    def __init__(self, board_size=0, colour="NA"):
        self.s = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )

        self.s.connect((self.HOST, self.PORT))
        
        self.state = None
        self.agent = None
        self.board_size = board_size
        self.colour = "NA"
        self.turn_count = 0

    def run(self):
        """Reads data until it receives an END message or the socket closes."""

        while True:
            data = self.s.recv(1024)
            if not data:
                break
            # print(f"{self.colour} {data.decode('utf-8')}", end="")
            if (self.interpret_data(data)):
                break

        # print(f"Naive agent {self.colour} terminated")

    def interpret_data(self, data):
        """Checks the type of message and responds accordingly. Returns True
        if the game ended, False otherwise.
        """

        messages = data.decode("utf-8").strip().split("\n")
        messages = [x.split(";") for x in messages]
        # print(messages)
        for s in messages:
            print(s, self.colour)
            if s[0] == "START":
                self.state = GameState(int(s[1]), s[2])
                self.board = [[0] * self.board_size for i in range(self.board_size)]
                self.agent = UctMctsAgent(self.state)
                self.colour = s[2]
                if self.colour == "R":
                    self.make_move()

            elif s[0] == "END":
                return True

            elif s[0] == "CHANGE":
                if s[3] == "END":
                    return True
                elif s[1] == "SWAP":
                    self.swapColour()
                elif s[3] == self.colour: # Our agents move
                    print()
                    x, y = [int(x) for x in s[1].split(",")]
                    self.processOpposingAgentMove(x, y)
                # if updateing opposing agents move on our end

        return False
    
    def swapColour(self, turn):
        self.state.colour = self.state.opp_colour()
        if turn == self.state.colour:
            self.make_move()
    
    def processOpposingAgentMove(self, x, y):
        self.state.board[x][y] = self.state.opp_colour()
        # TODO: update tree
        # self.make_move()
        self.make_move()
        # 
    
    def make_move(self):
        if self.colour == "B" and self.turn_count == 0 and choice([0, 1]) == 1:
            # decide whether to swap or not
            # ones on edges may be less desirable compared to those in middle
                self.s.sendall(bytes("SWAP\n", "utf-8"))
                return

        self.agent.search(5)
        move = self.agent.best_move()
        self.state.play(move)
        self.agent.move(move)
        
        self.s.sendall(bytes(f"{move[0]},{move[1]}\n", "utf-8"))
        
        # 2. run monte carlo algo
        # 3. once move made, update tree structure for our move
        # 4. send our move as message to engine
        # update tree struct once move is made
        
        self.turn_count += 1

if (__name__ == "__main__"):
    agent = Agent()
    agent.run()

'''
python Hex.py “a=PNA;python stupid-agent/TAgent.py” “a=JNA;java -classpath agents\DefaultAgents/NaiveAgent” -v

'''