from tqdm import tqdm
import shlex
import subprocess
from sys import argv, platform
from Hex import extract_agents, get_main_cmd
from dataclasses import dataclass


@dataclass
class PlayerStats:
    win: bool
    time: int
    moves: int


def get_player_stats_from_line(line):
    win = True if line[0] == "True" else False
    time = int(line[1])
    moves = int(line[2])
    return PlayerStats(win, time, moves)


@dataclass
class GameStats:
    outcome: str
    p1stats: PlayerStats
    p2stats: PlayerStats


def extract_analytics_args(arguments):
    other_args = []
    number_of_experiments = 0
    for i in range(len(arguments)):
        argument = arguments[i]
        if "-n" in argument:
            value = arguments[i + 1]
            try:
                number_of_experiments = int(value)
            except Exception:
                print(f"Value '{value}' is not in correct format.")
        else:
            other_args.append(argument)
    return number_of_experiments, other_args


# def read_experiment_results(results_string):


def run_experiment(arguments, agents) -> GameStats:
    cmd = (
            get_main_cmd() + " " +
            " ".join(arguments) + " " +
            " ".join(agents)
    )
    if (platform != "win32"):
        cmd = shlex.split(cmd)

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Accessing the output
    output = result.stdout
    error = result.stderr

    line1, line2, line3, _ = [line.split(" ") for line in error.split("\n")]

    p1stats = get_player_stats_from_line(line2)
    p2stats = get_player_stats_from_line(line3)
    outcome = line1[0]

    return GameStats(outcome, p1stats, p2stats)


def main():
    """Checks that at most two agents are specified and that they
    are unique, then runs the main script with the given args.
    """

    agents, arguments = extract_agents(argv)
    if (len(agents)) > 2:
        print("ERROR: Too many agents specified. Aborted.")
        return
    elif (len(agents) != len(set(agents))):
        print("ERROR: Agent strings must be unique. Aborted.")

    n, arguments = extract_analytics_args(arguments)

    if n == 0:
        print(f"Running {n} experiments")

    p1wins = p2wins = 0
    for i in tqdm(range(n), desc="Running experiments"):
        gs = run_experiment(arguments, agents)
        if gs.outcome == "Win":
            if gs.p1stats.win:
                p1wins += 1
            else:
                p2wins += 1

    print(f"Player 1 wins: {p1wins}")
    print(f"Player 2 wins: {p2wins}")

    if p2wins == 0:
        p1win_rate = 100
    else:
        p1win_rate = (p1wins / (p1wins + p2wins)) * 100
    print(f"Player 1 win rate: {p1win_rate:.2f}%")


if __name__ == "__main__":
    main()
