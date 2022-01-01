import json


class Config:

    def __init__(self, dir):

        self.configDir = dir

        self.configData = {}

        with open(dir, 'r') as file:
            self.configData = json.load(file)