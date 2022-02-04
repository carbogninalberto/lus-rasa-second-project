import os
import json
import statistics

with open('./results.json', 'r') as f:
    data = json.load(f)
    for item in data:
        print("{} & {:.2f} & {:.2f} & {:.2f} & {:.2f} \\\\".format(
                item,
                statistics.mean([data[item][0][3],
                                data[item][1][3],
                                data[item][2][3]]),
                statistics.mean([data[item][0][2],
                                data[item][1][2],
                                data[item][2][2]]),
                statistics.mean([data[item][0][1],
                                data[item][1][1],
                                data[item][2][1]]),
                statistics.mean([data[item][0][0],
                                data[item][1][0],
                                data[item][2][0]]),
                ))