import os


class AminerDataset(object):
    def __init__(self, path):
        self.fn = os.path.join(path, 'data.txt')
