'''
Created on 26 Mar 2020

@author: boogie
'''
from tribler import defs
from . import common


class metadata:
    @staticmethod
    def torrenthealth(infohash, refresh=0, timeout=defs.DHT_TIMEOUT):
        return common.call(
            "GET",
            f"metadata/torrents/{infohash}/health",
            refresh=refresh,
            timeout=timeout,
        )

    @staticmethod
    def subscribe(chanid, publickey, subscribed=True):
        return common.call(
            "PATCH", f"metadata/{publickey}/{chanid}", subscribed=subscribed
        )
