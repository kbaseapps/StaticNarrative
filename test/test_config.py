import os
from configparser import ConfigParser


CONFIG_FILE = "./deploy.cfg"


def get_test_config():
    config_file = os.environ.get('KB_DEPLOYMENT_CONFIG', CONFIG_FILE)
    print(config_file)
    cfg_dict = dict()
    config = ConfigParser()
    config.read(config_file)
    for nameval in config.items('StaticNarrative'):
        cfg_dict[nameval[0]] = nameval[1]
    return cfg_dict
