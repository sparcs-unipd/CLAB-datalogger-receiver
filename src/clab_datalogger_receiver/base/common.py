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


def resource_path(relativePath: str, subfolder: str = '') -> str:
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        basePath = sys._MEIPASS
    except Exception:
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            basePath = sys._MEIPASS2
        except Exception:
            basePath = os.path.join(os.path.abspath("."), subfolder)
            print('bp: ', basePath)
    path = os.path.join(basePath, relativePath)
    print('p: ', path)
    return path
