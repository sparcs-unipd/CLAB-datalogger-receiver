# from __future__ import annotations


import sys

from clab_datalogger_receiver.received_structure import PlottingStruct
from clab_datalogger_receiver.qt_app_main import get_app_and_window

data_struct = PlottingStruct.from_yaml_file()


app, window = get_app_and_window(data_struct, sys_argv=sys.argv)

window.show()

app.exec()
