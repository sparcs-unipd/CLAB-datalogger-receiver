import sys
import os


# def resource_path(relative):
#     return os.path.join(
#         os.environ.get(
#             "_MEIPASS2",
#             os.path.abspath("."),
#         ),
#         relative,
#     )

is_nuitka = "__compiled__" in globals()


def resource_path_nuitka(relative_path: str, subfolder: str = '') -> str:
    """
    Returns the path of a file relative to the script.
    If the program is built with nuitka, then returns the same file into \
        the .exe
    """
    # This will find a file *near* your onefile.exe
    # path = os.path.join(os.path.dirname(sys.argv[0]), relativePath)
    # This will find a file *inside* your onefile.exe
    # path = os.path.join(os.path.dirname(__file__), relativePath)

    # print('is_nuitka: ', is_nuitka)

    if is_nuitka:
        path = os.path.join(
            os.path.dirname(__file__), os.path.pardir, relative_path
        )
    else:
        path = os.path.join(subfolder, relative_path)

    # print('path:', path)
    if os.path.exists(path):
        # print('returning path')
        return path
    return path


# def resource_path_pyinstaller(relativePath: str, subfolder: str = '') -> str:
#     """Get absolute path to resource, works for dev and for PyInstaller"""
#     try:
#         # PyInstaller creates a temp folder and stores path in _MEIPASS
#         basePath = sys._MEIPASS
#     except Exception:
#         try:
#             # PyInstaller creates a temp folder and stores path in _MEIPASS
#             basePath = sys._MEIPASS2
#         except Exception:
#             basePath = os.path.join(os.path.abspath("."), subfolder)
#             # print('bp: ', basePath)
#     path = os.path.join(basePath, relativePath)
#     # print('p: ', path)
#     return path


def resource_path(relativePath: str, subfolder: str = '') -> str:
    return resource_path_nuitka(relativePath, subfolder)
