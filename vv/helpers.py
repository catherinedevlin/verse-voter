# -*- coding: utf-8 -*-
import configparser

def get_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    config.read('config.secret.ini')
    return config
