'''
Created on Feb 18, 2023

@author: boogie
'''
from tinyxbmc import addon
from tinyxbmc import const
from tinyxbmc import net
from tinyxbmc.distversion import LooseVersion
from tinyxbmc.stubmod import isstub

import six
import ghub
import xbmc
import os
import re
import traceback

if addon.has_addon("plugin.program.aceengine"):
    addon.depend_addon("plugin.program.aceengine")
    import aceengine
else:
    aceengine = None


def installwidevine():
    HASWV = False
    CDMVER = None
    try:
        ishelper = ghub.load("emilsvennesson", "script.module.inputstreamhelper", "master", period=24 * 7, path=["lib"])
        fname = os.path.join(ishelper, "lib", "inputstreamhelper", "kodiutils.py")
        with open(fname) as f:
            src = f.read()
        src = re.sub("script\.module\.inputstreamhelper", "script.module.tinyxbmc", src)
        with open(fname, "w") as f:
            f.write(src)
        import inputstreamhelper
        inputstreamhelper.ok_dialog = lambda *args, **kwargs: True
        inputstreamhelper.widevine_eula = lambda *args, **kwargs: True
        helper = inputstreamhelper.Helper("mpd")
        HASWV = inputstreamhelper.has_widevinecdm()
        canwv = helper._supports_widevine()
        if not canwv:
            addon.log("MPD: Widewine is not supported by platform")
        if not HASWV and canwv:
            helper.install_widevine()
            HASWV = True
        if HASWV:
            CDMVER = LooseVersion(helper._get_lib_version(inputstreamhelper.widevinecdm_path()))
            addon.log("MPD: Widewine is enabled with CDM version %s" % CDMVER)
    except Exception as _e:
        print(traceback.format_exc())

    return HASWV, CDMVER


class url(dict):
    HASISA = addon.has_addon(const.INPUTSTREAMADAPTIVE) and addon.addon_details(const.INPUTSTREAMADAPTIVE).get("enabled")
    HASFFDR = addon.has_addon(const.INPUTSTREAFFMPEGDIRECT) and addon.addon_details(const.INPUTSTREAFFMPEGDIRECT).get("enabled")

    def __init__(self, url=None, manifest=None, adaptive=True, ffmpegdirect=True, noinputstream=True, **kwargs):
        self.url = url
        self.adaptive = adaptive
        self.ffmpegdirect = ffmpegdirect
        self.noinputstream = noinputstream
        self.manifest = manifest
        for k, v in kwargs.items():
            setattr(self, k, v)
        dict.__init__(self,
                      url=url,
                      manifest=self.manifest,
                      adaptive=self.adaptive,
                      ffmpegdirect=self.ffmpegdirect,
                      noinputstream=self.noinputstream,
                      **kwargs)

    def props(self):
        props = {}
        if self.inputstream:
            if int(xbmc.getInfoLabel('System.BuildVersion')[:2]) >= 19:
                props['inputstream'] = self.inputstream
            else:
                props['inputstreamaddon'] = self.inputstream
        if self.manifest:
            props['inputstream.adaptive.manifest_type'] = self.manifest
        return props

    @property
    def inputstream(self):
        if self.HASISA and self.adaptive:
            return const.INPUTSTREAMADAPTIVE
        elif self.HASFFDR and self.ffmpegdirect:
            return const.INPUTSTREAFFMPEGDIRECT
        return None


class hlsurl(url):
    HASWV = False
    CDMVER = None
    manifest = const.MANIFEST_HLS

    if url.HASISA:
        HASWV, CDMVER = installwidevine()
    else:
        addon.log("MPD: Inputstream.adaptive is not installed")

    if isstub():
        HASWV = True

    def __init__(self, url, headers=None, adaptive=True, ffmpegdirect=True, noinputstream=True,
                 lurl=None, lheaders=None, lbody="R{SSM}", lresponse="", lic="com.widevine.alpha", mincdm=None):
        headers = headers or {}
        lheaders = lheaders or {}
        if isinstance(mincdm, six.string_types):
            mincdm = LooseVersion(mincdm)
        else:
            mincdm = None
        super(hlsurl, self).__init__(url, self.manifest, adaptive, ffmpegdirect, noinputstream, headers=headers,
                                     lurl=lurl, lheaders=lheaders, lbody=lbody, lresponse=lresponse, lic=lic,
                                     mincdm=mincdm)

    @property
    def kodiurl(self):
        return net.tokodiurl(self.url, headers=self.headers, pushverify="false", pushua=const.USERAGENT)

    @property
    def kodilurl(self):
        if self.lurl:
            lurl = net.tokodiurl(self.lurl, headers=self.lheaders)
            if "|" not in lurl:
                return lurl + "|"
            return "%s|%s|%s" % (lurl, self.lbody, self.lresponse)
        else:
            lurl = net.tokodiurl(self.url, headers=self.lheaders)
            if "|" not in lurl:
                return "|"
            return "|%s" % lurl.split("|")[1]

    def props(self):
        props = super(hlsurl, self).props()
        headers = self.kodiurl.split("|")
        headers = headers[1] if len(headers) == 2 else ""
        props['inputstream.adaptive.manifest_type'] = self.manifest
        props['inputstream.adaptive.stream_headers'] = headers
        props['inputstream.adaptive.manifest_headers'] = headers
        if self.lurl:
            props['inputstream.adaptive.license_type'] = self.license
            self.lurl, self.lheaders = net.fromkodiurl(net.tokodiurl(self.lurl, headers=self.lheaders, pushua=const.USERAGENT, pushverify="false"))
        props['inputstream.adaptive.license_key'] = self.kodilurl
        return props

    @property
    def inputstream(self):
        inputstream = None
        if self.lurl:
            if self.HASWV:
                if self.mincdm:
                    if self.mincdm <= self.CDMVER:
                        inputstream = const.INPUTSTREAMADAPTIVE
                    else:
                        addon.log("MPD: Available CDM version (%s) is not >= minimum required (%s): %s" % (self.CDMVER,
                                                                                                           self.mincdm,
                                                                                                           self.url))
                else:
                    inputstream = const.INPUTSTREAMADAPTIVE
            else:
                addon.log("MPD: DASH stream requires drm but widewine is not available: %s" % (self.url))
        elif self.HASISA:
            inputstream = const.INPUTSTREAMADAPTIVE
        return inputstream


class mpdurl(hlsurl):
    manifest = const.MANIFEST_MPD


class acestreamurl(url):

    def __init__(self, url, adaptive=False, ffmpegdirect=True, noinputstream=True):
        super(acestreamurl, self).__init__(url, const.MANIFEST_ACE, adaptive, ffmpegdirect, noinputstream)
        if aceengine:
            self.aceurl = aceengine.acestream(self.url)
        else:
            self.aceurl = None

    @property
    def kodiurl(self):
        if aceengine:
            return self.aceurl.httpurl


def urlfromdict(url):
    if isinstance(url, dict):
        manifest = url.pop("manifest")
        if manifest == const.MANIFEST_HLS:
            return hlsurl(**url)
        elif manifest == const.MANIFEST_MPD:
            return mpdurl(**url)
        elif manifest == const.MANIFEST_ACE:
            return acestreamurl(**url)
    else:
        return url
