from matplotlib import pyplot as plt
import json
import numpy as np


def plot_airdrop_boost_dist(airdrop_file: str, figure_file:str):
    with open(airdrop_file) as f:
        airdrops = [json.loads(line) for line in f][0]
    
    # print(airdrops)

    cnc_boosts = [v["vlcnc_boost"] for v in airdrops if v["vlcnc_boost"] > 1]
    crv_boosts = [v["vecrv_boost"] for v in airdrops if v["vecrv_boost"] > 1]

    cnc_boosts_x = sorted(cnc_boosts)
    crv_boosts_x = sorted(crv_boosts)
    print("min cnc boost: ", min(cnc_boosts_x))
    print("min crv boost: ", min(crv_boosts_x))

    cnc_boosts_y = np.arange(1, len(cnc_boosts_x)+1)
    crv_boosts_y = np.arange(1, len(crv_boosts_x)+1)

    fig, ax = plt.subplots(1, 2)
    ax[0].plot(cnc_boosts_x, cnc_boosts_y, label='CNC boost CDF', c='orange')
    ax[1].plot(crv_boosts_x, crv_boosts_y, label='CRV boost CDF', c = 'blue')
    fig.legend()
    fig.savefig(figure_file)
    



