'''
Created on 26 Mar 2020

@author: boogie
'''
from tinyxbmc import container

from . import common


class metadata(container.container):
    @staticmethod
    def torrenthealth(infohash, refresh=0, timeout=5):
        return common.call("GET", "metadata/torrents/%s/health" % infohash,
                           refresh=refresh,
                           timeout=timeout)