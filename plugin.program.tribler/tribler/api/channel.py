'''
Created on 26 Mar 2020

@author: boogie
'''

from . import common


class channel:
    @staticmethod
    def list(subscribed, first=1, last=500, sort_by="updated", sort_desc=1):
        resp = common.call("GET", "channels",
                           subscribed=1 if subscribed else None,
                           first=first,
                           last=last,
                           sort_by=sort_by,
                           sort_desc=sort_desc)
        return resp.get("results", []) if resp else []

    @staticmethod
    def get(chanid, publickey, first=1, last=20, sort_by="updated", sort_desc=1, include_total=1, hide_xxx=0):
        if not (
            resp := common.call(
                "GET",
                f"channels/{publickey}/{chanid}",
                first=first,
                last=last,
                sort_by=sort_by,
                sort_desc=sort_desc,
                include_total=include_total,
                hide_xxx=hide_xxx,
            )
        ):
            return 0, []
        results = resp.get("results")
        return (resp["total"], results) if results is not None else (0, [])
