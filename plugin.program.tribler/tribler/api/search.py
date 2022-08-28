'''
Created on 26 Mar 2020

@author: boogie
'''
from . import common


class search:
    @staticmethod
    def query(txt_filter, first=1, include_total=1, hide_xxx=1):
        if resp := common.call(
            "GET", "search", txt_filter=txt_filter, first=first, hide_xxx=hide_xxx
        ):
            return resp.get("results", [])
        else:
            return []
