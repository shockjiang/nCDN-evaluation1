import os, os.path
ROOT_PATH = os.path.split(os.path.realpath(__file__))[0]

UPDATE_FILE = os.path.join(ROOT_PATH, "../output/out.log")
DATA_LINE_IGNORE_FLAG = "#"

UPDATE_FLAG = "change status from"
INTEREST_FLAG = ">Interest for"
DATA_FLAG = "<Respodning with ContentObject"

START_FLAGS = [UPDATE_FLAG, INTEREST_FLAG, DATA_FLAG]
IGNORE_FLAGS = [DATA_LINE_IGNORE_FLAG]