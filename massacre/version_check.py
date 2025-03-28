"""
This Module contains logic to check for new Updates in a separate Thread
"""
import os
import subprocess
import sys
import threading

from requests import get
from massacre.logger_factory import logger
from pathlib import Path
from typing import Callable

_version_url = "https://raw.githubusercontent.com/ckx000/EDMC-Massacres/master/version"
download_url = "https://github.com/ckx000/EDMC-Massacres/releases"


def __is_current_version_outdated(current_version: str, callback: Callable[[bool], None]) -> None:
    """
    **RUN THIS IN A THREAD!**

    Gets the String located at _version_url and compares to the local string.
    If the Version URL is invalid, or some other Error occurs, false is returned.

    A Version looks like this: 1.0.3

    If there is a length-mismatch, the shorter string gets filled with 0s
    """
    is_outdated = False
    try:
        response = get(_version_url)

        current_version_split = list(map(lambda x: int(x), current_version.split(".")))
        response_version_split = list(map(lambda x: int(x), response.text.split(".")))

        longer_len = max([len(current_version_split), len(response_version_split)])

        current_delta = longer_len - len(current_version_split)
        response_delta = longer_len - len(response_version_split)
        """
        Example:
        current:  1.0.0.1
        response: 0.1.0.1
        -----------------
                  ^- current > response -> current is more recent
        
        Example2:
        current:  1.0.1
        response: 1.0.1
        ---------------
                  ^-equal, go to next
                    ^- equal, go to next
                      ^- equal, go to next
                        | - is equal
                        
        Example3
        current:  1.0.0
        response: 1.0.2
                  ^- equal, go next
                    ^- equal, go next
                      ^- response > current -> current is outdated.
        """
        while current_delta > 0:
            current_version_split.append(0)
            current_delta -= 1
        while response_delta > 0:
            response_version_split.append(0)
            response_delta -= 1

        for i in range(longer_len):
            if response_version_split[i] > current_version_split[i]:
                is_outdated = True
                break
            if response_version_split[i] < current_version_split[i]:
                break

    except IOError:
        logger.error("Failed to get Version from Remote. Ignoring...")

    callback(is_outdated)


def __get_current_version_string():
    """
    Gets the current version, located in the version-File
    """
    version_file = Path(__file__).parent.with_name("version")
    with version_file.open("r", encoding="utf8") as file:
        current_version = str(file.read())
        return current_version


def __worker(cb: Callable[[bool], None]):
    """
    Function invoked by the new Thread used to check if the Version is outdated.
    """
    current_version = __get_current_version_string()
    __is_current_version_outdated(current_version, cb)


def build_worker(cb: Callable[[bool], None]) -> threading.Thread:
    """
    Creates a new Thread used to check version. Does not start the thread.
    """
    thread = threading.Thread(target=__worker, args=[cb])
    thread.name = "Massacre Version Check"
    thread.daemon = True

    return thread


def open_download_page():
    """
    Opens link to the Download URL in Browser
    """
    platform = sys.platform

    if platform == "darwin":
        subprocess.Popen(["open", download_url])
    elif platform == "win32":
        os.startfile(download_url) # type: ignore
    else:
        try:
            subprocess.Popen(["xdg-open", download_url])
        except OSError:
            logger.error("Failed to open URL")
