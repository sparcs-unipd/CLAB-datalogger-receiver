
pyinstaller ^
    --onefile --windowed ^
    --noconfirm ^
    --add-data "src\clab_datalogger_receiver\icons\SPARCS_logo_v2_nobackground.png;icons" ^
    .\clab_datalogger_receiver_app.py    