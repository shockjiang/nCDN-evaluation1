import os, os.path
ROOT_PATH = os.path.split(os.path.realpath(__file__))[0]
UPDATE_FLAG = "ndn.fib.Entry:UpdateStatus"
UPDATE_IGNORE_FLAGS = ["dev=loca"]
UPDATE_FILE = os.path.join(ROOT_PATH, "../output/out.log")
DATA_LINE_IGNORE_FLAG = "#"

