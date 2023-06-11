import datetime
import requests
import argparse
import json
import time


parser = argparse.ArgumentParser()
parser.add_argument('--ratings', type=int, default=2000,
    choices=[400, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2500],
    help='average player rating on Lichess')
parser.add_argument('--depth', type=int, default=6,
    help='search $depth moves deep from the starting position')

args = parser.parse_args()


def recurse(moves=[], freq=1, parent=0):
    if len(moves) > args.depth:
        return


    print(datetime.datetime.now().replace(microsecond=0).isoformat(" "), "GET", moves)

    d = {}
    while not d:
        try:
            time.sleep(0.5)
            mvs = ','.join(moves)
            txt = requests.get(f"https://explorer.lichess.ovh/lichess?play={mvs}&speeds=rapid,classical,correspondence&modes=rated&ratings={args.ratings}").text
            d = json.loads(txt)
        except Exception:
            time.sleep(20)


    # write moves games and score
    games = d["white"] + d["draws"] + d["black"]

    for succ in d["moves"]:

        moves_succ = moves + [succ["uci"]]

        games_succ = succ["white"] + succ["draws"] + succ["black"]
        freq_succ = games_succ / games
        freq_total = freq * freq_succ

        ev_succ = (succ["white"] - succ["black"]) / games_succ * 100

        with open("out.csv", "a") as f:
            mvs = ','.join(moves_succ)
            f.write(f"{freq_total},{ev_succ},{parent},{mvs}\n")
            global ENTRY
            ENTRY += 1

        if freq_succ >= 0.02 and games_succ >= 10_000:
            recurse(moves_succ, freq_total, ENTRY)



with open("out.csv", "w") as f:
    f.write("freq,EV,parent,mv0,mv1,mv2,mv3,mv4,mv5,mv6,mv7,mv8,mv9\n")
    f.write("1,0\n")


ENTRY = 0
recurse()
