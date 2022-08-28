'''
Created on 26 Mar 2020

@author: boogie
'''
from tribler.api import common


class download:
    @staticmethod
    def add(uri):
        try:
            hops = int(common.config.get("download_defaults", "number_hops"))
        except Exception:
            hops = 1
        try:
            anon_seed = 1 if common.config.get("download_defaults", "safeseeding_enabled") else 0
        except Exception:
            anon_seed = 1
        resp = common.call("PUT", "downloads", uri=uri,
                           anon_hops=hops,
                           safe_seeding=anon_seed)
        return resp.get("infohash")

    @staticmethod
    def setstate(ihash, state):
        if state == "stop":
            download.setvodmode(ihash, False)
        return common.call("PATCH", f"downloads/{ihash}", state=state)

    @staticmethod
    def setvodmode(ihash, vod_mode, fileindex=None):
        return (
            common.call(
                "PATCH", f"downloads/{ihash}", vod_mode=True, fileindex=fileindex
            )
            if vod_mode
            else common.call("PATCH", f"downloads/{ihash}", vod_mode=False)
        )

    @staticmethod
    def sethops(ihash, hops):
        return common.call("PATCH", f"downloads/{ihash}", anon_hops=hops)

    @staticmethod
    def delete(ihash, remove_data=None):
        return common.call("DELETE", f"downloads/{ihash}", remove_data=remove_data)

    @staticmethod
    def list(get_files=0):
        if downloads := common.call("GET", "downloads", get_files=get_files):
            return downloads.get("downloads", [])
        else:
            return []

    @staticmethod
    def files(infohash):
        resp = common.call("GET", f"downloads/{infohash}/files")
        return resp.get("files", []) if resp and "files" in resp else []
