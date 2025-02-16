import os

from dotenv import load_dotenv

# the variables in .env will be loaded by VSCode beforehand, WITHOUT VARIABLES EXPANSION
# so they need to be overridden...
load_dotenv(override=True)

DEV_MODE = bool(os.getenv('DEV', '0') == '1')
