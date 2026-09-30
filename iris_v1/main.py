import argparse
import logging

import ThermalImageLib as Til

# CONSTANTS
parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", action="store_true", help="Print complete output")
parser.add_argument("-q", "--quite", action="store_true", help="Print concise output")

args = parser.parse_args()

# GLOBAL VARIABLES


# HELPER FUNCTIONS


# MAIN
if __name__ == "__main__":
    print(f"Colormaps: {Til.available_color_maps}")
    print("Success!!!")
