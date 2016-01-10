# coding: utf-8
import urllib
from xml.dom import minidom
import xbmcgui
import os
import hashlib
from xbmcaddon import Addon

firmwareArray = []
linkArray = []
md5Array = []
webfile = ""


def langString(id):
    # Return string based on language and id
    return Addon().getLocalizedString(id)


def messageOK(message):
    # print dialogue window with OK button based on message
    dialog = xbmcgui.Dialog()
    dialog.ok(langString(32002), message)


def findChildNodeByName(parent, name):
    # Return parent childnode that match name
    for node in parent.childNodes:
        if node.nodeType == node.ELEMENT_NODE and node.localName == name:
            return node
    return None


def downloadFirmwareList(source):
    # Download firmware list and store relevant data in arrays
    try:
        response = urllib.urlopen(source)
        doc = minidom.parse(response)
        firmwares = doc.getElementsByTagName('Version')

        for firmware in firmwares:
            versionDate = firmware.getAttribute('Updated')
            basic = findChildNodeByName(firmware, 'Basic')
            firmwareArray.append(basic.getAttribute('name') + langString(32003) + versionDate)
            linkArray.append(basic.getAttribute('URL'))
            md5Array.append(basic.getAttribute('MD5'))

    except:
        messageOK(langString(32030))
        quit()


def DownloaderClass(url, dest):
    # download file and display progress in dialog progress window
    dp = xbmcgui.DialogProgress()
    dp.create(langString(32004), langString(32005), url)
    urllib.urlretrieve(url, dest, lambda nb, bs, fs, url=url: _pbhook(nb, bs, fs, url, dp))


def _pbhook(numblocks, blocksize, filesize, url=None, dp=None):
    try:
        percent = min((numblocks * blocksize * 100) / filesize, 100)
        print percent
        dp.update(percent)
    except:
        percent = 100
        dp.update(percent)
        dp.close()
    if dp.iscanceled():
        dp.close()
        os.remove('/recover/update.img')
        messageOK(langString(32031))


def md5ErrorMessage():
    # display error message
    messageOK(langString(32036))
    quit()


def shellErrorMessage(message):
    # display error message
    messageOK(message)
    quit()


def recoverCommand():
    # issue shell command to install selected firmware and reset to factory settings if specify in the setting file
    if (Addon().getSetting('factoryReset') == 'true'):
        shellCommand = 'echo -e "--update_package=/cache/update.img\n--wipe_cache\n--wipe_data" > /recovery/recovery/command || exit 1'
    else:
        shellCommand = 'echo -e "--update_package=/cache/update.img\n--wipe_cache" > /recovery/recovery/command || exit 1'
    result = os.system(shellCommand)
    if result != 0:
        messageOK(langString(32033))
        quit()
    else:
        dialog = xbmcgui.Dialog()
        dialog.notification(langString(32009), langString(32016), icon='', time=3000)
        shellCommand = 'reboot recovery'
        os.system(shellCommand)

    
def md5(fname):
    # return md5 of the file fname
    dpMd5 = xbmcgui.DialogProgress()
    message = langString(32017)
    dpMd5.create(langString(32018), message)
    fileSize = os.path.getsize('/recovery/update.img')
    stepSize = round(fileSize/409600)
    percent = 0
    count = 0
    hash = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash.update(chunk)
            dpMd5.update(percent)
            count = count + 1
            if count > stepSize and percent < 100:
                percent += 1
                count = 0
    dpMd5.close()
    return hash.hexdigest()


def firmwareUpdate(message):
    # control the firmware selected installation
    dialog = xbmcgui.Dialog()
    message = message + langString(32006)
    runscript = dialog.yesno(langString(32002), message)

    if (runscript):
        runscript = dialog.yesno(langString(32007), langString(32008))

        if (runscript):
            DownloaderClass(linkArray[ret], '/recovery/update.img')
            if md5('/recovery/update.img') <> md5Array[ret]:
                md5ErrorMessage()
            else:
                dialog = xbmcgui.Dialog()
                dialog.notification(langString(32019), langString(32020), icon='', time=3000)
            recoverCommand()
        else: quit()
    else: quit()


def checkHardware():
    # Check hardware to determine correct firmware list link
    device = Addon().getSetting('device')
    if device == '1':
        return 'http://update.pivosgroup.com/linux/mx/update.xml'
    elif device == '2':
        return 'http://update.pivosgroup.com/linux/m3/update.xml'
    elif device == '3':
        return 'http://update.pivosgroup.com/linux/m1/update.xml'
    else:
        messageOK(langString(32035))
        quit()


# firmware update.xml URL
imageListLink = checkHardware()

# download firmware list for selection
downloadFirmwareList(imageListLink)

# display firmware list in a dialogue for selection. ret = position of selection
ret = xbmcgui.Dialog().select(langString(32001), firmwareArray)  #

# proceed with firmware installation based on firmware selected.
firmwareUpdate(firmwareArray[ret])

quit()
