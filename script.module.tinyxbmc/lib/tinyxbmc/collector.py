'''
Created on Nov 6, 2021

@author: boogie
'''
import os
import platform
import requests
import io
import json
import pprint
from datetime import datetime

import xbmc
import traceback

from tinyxbmc import tools
from tinyxbmc import abi
from tinyxbmc import gui
import six


db_api_url = "https://content.dropboxapi.com/"


def collect_log(name, content, token):
    mid = abi.getmachineid()
    osname = abi.detect_os()
    try:
        abiinfo = abi.getelfabi()
    except Exception:
        abiinfo = None

    fname = "%s_%s_%s_%s" % (name, datetime.utcnow().strftime("%Y%m%d-%H%M%S"), mid, osname)
    fname = fname.replace(" ", "_").replace("/", "-").replace(":", "-").replace("?", "-").replace(".", "-")

    # platform data
    log = u"MACHINE ID      : %s\r\n" % mid
    log += "PLATFORM        : %s\r\n" % abi.detect_os()
    if abiinfo:
        log += "ABI             : %s\r\n" % str(abiinfo)
    log += "RELEASE         : %s\r\n" % platform.release()
    log += "ENVIRONMENT     : %s\r\n" % str(os.environ)
    log += "XBMC VERSION    : %s\r\n" % xbmc.getInfoLabel("System.BuildVersion")
    log += "PYTHON VERSION  : %s\r\n" % platform.python_version()
    log += "LOG             : \r\n%s\r\n" % content

    # kodilog
    log_path = tools.translatePath('special://logpath')
    kodilog = None
    for filename in ["kodi.log", "xbmc.log", "spmc.log"]:
        fullpath = os.path.join(log_path, filename)
        if os.path.exists(fullpath):
            for encoding in ["latin-1", "utf-8"]:
                try:
                    with io.open(fullpath, encoding=encoding) as f:
                        kodilog = f.read()
                        break
                except Exception:
                    continue
    if kodilog:
        log += "KODI LOG             :\r\n%s\r\n" % kodilog

    # addondata
    data = {"jsonrpc": "2.0",
            "method": "Addons.GetAddons",
            "id": 1,
            "params": {"properties": ["name", "version", "path", "dependencies", "enabled", "broken"], "enabled": True}
            }
    addons = json.loads(xbmc.executeJSONRPC(json.dumps(data)))
    log += "ADDONS          : \r\n%s\r\n" % pprint.pformat(addons["result"]["addons"])

    # send log
    headers = {'Authorization': 'Bearer %s' % token,
               'Dropbox-API-Arg': '{\"path\": \"/%s.zip\",\"mode\": \"add\",\"autorename\": true,\"mute\": false,\"strict_conflict\": false}' % fname,
               'Content-Type': 'application/octet-stream'}

    msg = "Do you want to help to fix this problem by sending the kodilogs and error trace to a public space where developers can analyze in the detail?"
    if(gui.yesno("Send Error Report: %s" % name, msg)):
        zipf = tools.memzip([(fname + ".txt", log.encode("utf-8"))])
        requests.post('%s/2/files/upload' % db_api_url, headers=headers, data=zipf)


class LogException():
    def __init__(self, name, token=None, ignore=False):
        self.name = name
        self.ignore = ignore
        self.token = token
        self.hasexception = False
        self.msg = ""

    def __enter__(self):
        return self

    def onexception(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type and not exc_type == SystemExit:
            self.hasexceptionn = exc_type
            tb = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
            if self.token:
                self.msg += "TRACEBACK: \r\n%s\r\n" % tb
                collect_log(self.name, self.msg, self.token)
            if not self.ignore:
                raise
            else:
                # TO-DO: backward compat?
                xbmc.log(tb, xbmc.LOGERROR)
                self.onexception()
                return True
            self.onexception()


def loggingsafeiter(iterable, name="", token=None):
    if hasattr(iterable, "next") or hasattr(iterable, "__next__"):
        while True:
            try:
                yield six.next(iterable)
            except StopIteration:
                break
            except Exception:
                msg = "TRACEBACK: \r\n%s\r\n" % traceback.format_exc()
                xbmc.log(msg, xbmc.LOGERROR)
                if token:
                    collect_log(name, msg, token)
