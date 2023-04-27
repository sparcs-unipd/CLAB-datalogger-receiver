from .received_structure import PlottingStruct
from .qt_app_main import get_app_and_window


def main(argv):
    data_struct = PlottingStruct.from_yaml_file()

    app, window = get_app_and_window(data_struct, sys_argv=argv)

    window.show()

    app.exec()
