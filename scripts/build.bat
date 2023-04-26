
pyinstaller ^
    --onefile --windowed ^
    --add-data "src\clab_datalogger_receiver\icons\SPARCS_logo_v2_nobackground.png;icons" ^
    .\qt_app.py ^
    