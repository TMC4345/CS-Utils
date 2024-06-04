#!/usr/bin/env python3

"""
CS:GO patcher
Copyright (C) 2024  Sjvadstik3, TMC4345
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import sys
import platform
if platform.system() == "Windows":
    import winreg


# verbosity of log
PATCHER_LOG_VERBOSE = True


class AnsiColors:
    """ANSI terminal colours"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def log_info(x, ignore_verbose=False):
    """prints informational message"""
    if PATCHER_LOG_VERBOSE or ignore_verbose:
        print(f"{AnsiColors.OKCYAN}[i] {x}{AnsiColors.ENDC}")


def log_ok(x, ignore_verbose=False):
    """prints success message"""
    if PATCHER_LOG_VERBOSE or ignore_verbose:
        print(f"{AnsiColors.OKGREEN}[✓] {x}{AnsiColors.ENDC}")


def log_warning(x, ignore_verbose=False):
    """prints warning message"""
    if PATCHER_LOG_VERBOSE or ignore_verbose:
        print(f"{AnsiColors.WARNING}[!] {x}{AnsiColors.ENDC}")


def log_error(x, ignore_verbose=False):
    """prints error message"""
    if PATCHER_LOG_VERBOSE or ignore_verbose:
        print(f"{AnsiColors.FAIL}[X] {x}{AnsiColors.ENDC}")


def main(os_name: str):
    """patches cs:go"""
    log_info("checking if CS:GO needs patch...")
    match os_name:
        case "Windows":
            path = get_path_windows()
        case "Linux":
            path = get_path_linux()
        case "Darwin":
            # needs CS2 files to patch
            log_error("CS:GO patching is not yet implemented on macOS")
            log_error("aborting...")
            return None
            # path = get_path_mac()
        case _:
            log_error(f"unsupported OS '{os}'")
            log_error("aborting...")
            return None

    if path:
        log_info(f"CS:GO installation detected at '{path}'")

        try:
            apply_patch(path)
        except OSError as err:
            log_error(f"failed to patch CS:GO: '{err}'", True)

    else:
        log_error("CS:GO not detected", True)
        log_error("└─ try enabling csgo_legacy beta", True)
        log_error("aborting...")


def get_path_linux() -> str:
    """returns path of a cs:go installation on linux: returns a blank
    string if not found"""

    # getting steam install path
    home = os.environ.get("HOME", None)
    if home is None:
        log_error("home environment variable is unset")
        log_error("aborting...")
        return ""

    lib_folders = ""
    steam_detected = False
    for dir_path, dir_name, _ in os.walk(home):
        if "Steam" in dir_name:
            steam_detected = True
            install_path = os.path.join(dir_path,
                                        "Steam")
            lib_folders = os.path.join(dir_path,
                                       "Steam",
                                       "steamapps",
                                       "libraryfolders.vdf")
            break

    if not steam_detected:
        log_error("steam installation not detected")
        log_error("aborting...")
        return ""

    else:
        # the pylint warning here would be caught by the above check
        log_info(f"steam installation detected at '{install_path}'")

    try:
        with open(lib_folders, 'r', encoding="utf-8") as file:
            # pylint: disable=used-before-assignment
            vdf_contents = loads(file.read())
    except OSError:
        log_error("could not find steam library")
        return ""

    # extracting CS:GO executable path
    path = None
    for _, path_data in vdf_contents['libraryfolders'].items():
        if 'apps' in path_data and '730' in path_data['apps']:
            path = path_data['path']
            path = os.path.join(path.replace("//", "/"),
                                "steamapps",
                                "common",
                                "Counter-Strike Global Offensive")
            break

    if path is None:
        return ""

    if not os.path.exists(path):
        # not sure what would cause this
        return ""

    return path


def get_path_windows() -> str:
    """returns path of a cs:go installation on windows: returns a blank
    string if not found"""

    # getting steam install path
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            os.path.join("SOFTWARE",
                                         "WOW6432Node",
                                         "Valve",
                                         "Steam")) as key:
            install_path, _ = winreg.QueryValueEx(key, "InstallPath")
        lib_folders = os.path.join(install_path,
                                   "steamapps",
                                   "libraryfolders.vdf")

        log_info(f"steam installation detected at '{install_path}'")

        try:
            with open(lib_folders, 'r', encoding="utf-8") as file:
                vdf_contents = loads(file.read())
        except OSError:
            log_error("could not find steam library")
            return ""

        # extracting CS:GO executable path
        path = None
        for _, path_data in vdf_contents['libraryfolders'].items():
            if 'apps' in path_data and '730' in path_data['apps']:
                path = path_data['path']
                path = os.path.join(path.replace('\\\\', '\\'),
                                    "steamapps",
                                    "common",
                                    "Counter-Strike Global Offensive")
                break

        if path is None:
            return ""

        if not os.path.exists(os.path.join(path, "csgo.exe")):
            # effectively a goto
            return ""

    except (OSError, ValueError, TypeError, UnboundLocalError):
        return ""

    return path


# def get_path_mac() -> str:
#     """returns path of a cs:go installation on macOS: returns a blank
#     string if not found"""

#     # getting steam install path
#     home = os.environ.get("HOME", None)
#     if home is None:
#         log_error("home environment variable is unset")
#         log_error("aborting...")
#         return ""

#     lib_folders = os.path.join(home, "Library", "Application Support",
#                                "Steam", "steamapps", "libraryfolders.vdf")

#     try:
#         with open(lib_folders, 'r', encoding="utf-8") as file:
#             # pylint: disable=used-before-assignment
#             vdf_contents = loads(file.read())
#     except OSError:
#         log_error("could not find steam library")
#         return ""

#     # extracting CS:GO executable path
#     path = None
#     for _, path_data in vdf_contents['libraryfolders'].items():
#         if 'apps' in path_data and '730' in path_data['apps']:
#             path = path_data['path']
#             path = os.path.join(path.replace("//", "/"),
#                                 "steamapps",
#                                 "common",
#                                 "Counter-Strike Global Offensive")
#             break

#     if path is None:
#         return ""

#     if not os.path.exists(path):
#         # not sure what would cause this
#         return ""

#     return path


def apply_patch(path: str):
    """apply patch to the cs:go installation"""
    log_info("applying patch...")

    # for mac to work we need to somehow pull this file off steam

    # replacing first line in path\csgo\steam.inf with that of
    # path\game\csgo\steam.inf (csgo client version number)
    with open(os.path.join(path, "game", "csgo", "steam.inf"),
              'r',
              encoding="utf-8") as file:
        file_patch = file.readline()

    log_ok("read patch")

    with open(os.path.join(path, "csgo", "steam.inf"),
              'r',
              encoding="utf-8") as file:
        file_content = file.readlines()

    log_ok("read target")

    if file_patch == file_content[0]:
        log_warning("CS:GO is already patched")
        log_warning("aborting...")
        return

    if file_content:
        file_content[0] = file_patch
    else:
        file_content.append(file_patch)

    with open(os.path.join(path, "csgo", "steam.inf"),
              'w',
              encoding="utf-8") as file:
        file.writelines(file_content)

    log_ok("successfully patched CS:GO", True)


if __name__ == "__main__":
    operating_system = platform.system()

    # argument parsing (completely needless tbh but TMC hates verbose logs)
    if "-h" in sys.argv or "--help" in sys.argv:
        print("CS:GO patcher script by Sjvadstik3 and TMC4345")
        print("arguments:\n\
-v          : decreases verbosity\n\
-h | --help : shows help message")
        sys.exit(0)

    if "-v" in sys.argv:
        PATCHER_LOG_VERBOSE = False

    # making sure the VDF module is installed properly
    try:
        from vdf import loads
    except ImportError:
        log_error("VDF reader module is not installed", True)
        log_error("├─ run 'pip install vdf' or 'pip install requirements.txt' \
to install", True)
        log_error("└─ linux users may need to install 'python3-vdf' with their\
 distro's package manager", True)
        log_error("aborting...")
    # if vdf was imported
    else:
        log_ok("VDF module is installed")
        main(operating_system)

    log_ok("Done.", True)

    match operating_system:
        case "Windows":
            os.system("pause")
        case _:  # linux, mac, etc.
            print("press enter to continue...", end="")
            input()
            print()
