import os
import sys

SRC_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, SRC_DIR) 

def get_relative_path(*path_parts):
    return os.path.join(SRC_DIR, *path_parts)