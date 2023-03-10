import os

# Set a variable to refer to the base directory of this repo
STATIC_NARRATIVE_BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print("STATIC_NARR_BASE_DIR: " + STATIC_NARRATIVE_BASE_DIR)
