'''
Created on 26 Mar 2020

@author: boogie
'''
import json
import hashlib
import bencode

from . import common


class torrentinfo:
    @staticmethod
    def get(uri, hops=None, infohash=None):
        if not uri:
            uri = common.makemagnet(infohash)
        kwargs = {"uri": uri}
        if hops:
            kwargs["hops"] = hops
        resp = common.call("GET", "torrentinfo", **kwargs)
        if not resp or not resp.get("metainfo"):
            return resp
        metainfo = json.loads(resp["metainfo"].decode("hex"))
        metainfo["info"]["pieces"] = metainfo["info"]["pieces"].decode("hex")
        metainfo["infohash"] = hashlib.sha1(bencode.encode(metainfo['info'])).digest().encode("hex")
        return metainfo
