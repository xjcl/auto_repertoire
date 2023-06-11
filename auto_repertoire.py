import pandas as pd

df = pd.read_csv("lichess_2000_slow_depth9.csv")
# df = pd.read_csv("lichess_1400_slow_depth8.csv")
# df = pd.read_csv("lichess_1200_slow.csv")
# df = pd.read_csv("out.csv")

# TODO: argparse




# def get_children(i0):
#     children = []
#     parent = df.loc[i0]

#     for i in range(i0+1, len(df)):
#         row = df.loc[i]
#         status = "to be checked"

#         for num in range(9):
#             if row[f"mv{num}"] == parent[f"mv{num}"]:
#                 continue

#             elif pd.isnull(row[f"mv{num}"]) and pd.isnull(parent[f"mv{num}"]):
#                 continue

#             elif row[f"mv{num}"] and pd.isnull(parent[f"mv{num}"]):
#                 if status == "to be checked":
#                     status = "potential child"
#                 elif status == "potential child":
#                     status = "not a child"
#                     break

#             else:
#                 status = "not a child"
#                 break

#         if status == "potential child":
#             children.append(i)
#         else:
#             break

#     return children


"""
Step 1: Calculate how often you get a move with free choice (wfreq/bfreq)
Step 2: Identify which positions should be in your reportorie (wnode/bnode)
Step 3: Calculate expected values recursively (wev/bev), by modelling the player
    as playing bestmoves and opponent as playing according to move frequencies
Step 4: TODO, nice output, as rows or maybe even a document

wfreq -- how often you will get this position when playing with white (1 = 100%)
wnode -- if True, this position is modeled to be "in White's repertorie",
    i.e. a position they have studied and know the best move for
wev -- white expected value, if white plays best moves and black plays
    probability-weighted moves, expressed as white-win-% minus black-win-%

"""





def get_children(i0):
    # TODO: optimize this
    return df.index[df["parent"] == i0].tolist()


def write_freqs(i0, wfreq=1, bfreq=1, white_move=False):
    df.loc[i0, "wfreq"] = wfreq_succ = wfreq
    df.loc[i0, "bfreq"] = bfreq_succ = bfreq
    print("WRITE FREQ", i0, wfreq, bfreq)

    children = get_children(i0)

    for i in children:
        if white_move:
            bfreq_succ = bfreq * df.loc[i, "freq"] / df.loc[i0, "freq"]
        if not white_move:
            wfreq_succ = wfreq * df.loc[i, "freq"] / df.loc[i0, "freq"]

        write_freqs(i, wfreq_succ, bfreq_succ, not white_move)


write_freqs(0, white_move=True)


# Include positions that happen in at least 1% of chess games if you always play the same moves
df["wnode"] = df["wfreq"] >= 0.001
df["bnode"] = df["bfreq"] >= 0.001


def _write_average_ev(i0, children, column):
    """Store average expected value"""
    df.loc[i0, column] = sum(
        df.loc[i, column] * (df.loc[i, "freq"] / df.loc[i0, "freq"])
        for i in children
    )


def _write_best_ev(i0, children, column, depth):
    """Recurse over children and store bestmove + its value"""
    # only store moves which are at least somewhat common (we want at least 200-ish games) to prevent statistical flukes
    children = [i for i in children if df.loc[i, "freq"] >= 0.02 * df.loc[i0, "freq"] and df.loc[i, "freq"] >= 0.00001]
    if not children:
        df.loc[i0, column] = df.loc[i0, "EV"]
        return

    best_nev = (max if column == "wev" else min)(df.loc[i, column] for i in children)
    best_child = next(i for i in children if df.loc[i, column] == best_nev)

    df.loc[i0, column] = best_nev
    df.loc[i0, "best_move"] = df.loc[best_child, f"mv{depth}"]


def write_evs(i0, white_move=True, depth=0):
    children = get_children(i0)
    print(children)

    if not children:
        df.loc[i0, "wev"] = df.loc[i0, "EV"]
        df.loc[i0, "bev"] = df.loc[i0, "EV"]
        return

    for i in children:
        write_evs(i, not white_move, depth + 1)

    if white_move:
        if df.loc[i0, "wnode"]:
            _write_best_ev(i0, children, "wev", depth)
        else:
            df.loc[i0, "wev"] = df.loc[i0, "EV"]
        _write_average_ev(i0, children, "bev")
    else:
        _write_average_ev(i0, children, "wev")
        if df.loc[i0, "bnode"]:
            _write_best_ev(i0, children, "bev", depth)
        else:
            df.loc[i0, "bev"] = df.loc[i0, "EV"]


write_evs(0)
df["wrep"] = False
df["brep"] = False

def find_repertoire(i0, for_white=True, my_move=True, depth=0):
    children = get_children(i0)

    if my_move:
        if not pd.isnull(df.loc[i0, "best_move"]):
            df.loc[i0, "wrep" if for_white else "brep"] = True
            i1 = [i for i in children if df.loc[i, f"mv{depth}"] == df.loc[i0, "best_move"]]
            if i1:
                find_repertoire(i1[0], for_white, not my_move, depth + 1)
    else:
        # recurse into all moves if >= 0.02
        children = [i for i in children if df.loc[i, "freq"] >= 0.02 * df.loc[i0, "freq"] and df.loc[i, "freq"] >= 0.00001]
        for i in children:
            find_repertoire(i, for_white, not my_move, depth + 1)



find_repertoire(0, for_white=True, my_move=True)
find_repertoire(0, for_white=False, my_move=False)

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.expand_frame_repr', False)

df_best = df[~pd.isnull(df["best_move"])]
print("\nFull analysis results:\n", df_best, len(df_best))

df_first2 = df[pd.isnull(df["mv2"])]
print("\nOpening comparison:\n", df_first2)

df_white = df[df["wrep"]]
print("\nWhite repertoire:\n", df_white, len(df_white))

df_black = df[df["brep"]]
print("\nBlack repertoire:\n", df_black, len(df_black))

