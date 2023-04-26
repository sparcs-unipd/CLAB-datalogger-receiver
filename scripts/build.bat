
pyinstaller ^
    --onefile --windowed ^
    --noconfirm ^
    --add-data "src\clab_datalogger_receiver\icons\*;icons" ^
    --add-data "templates\*\;templates" ^
    .\clab_datalogger_receiver_app.py    