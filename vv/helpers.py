# -*- coding: utf-8 -*-
import configparser

from . import models

"""Main module."""

def get_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    config.read('config.secret.ini')
    return config
