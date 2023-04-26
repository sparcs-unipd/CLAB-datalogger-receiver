
pyinstaller ^
    --onefile --windowed ^
    --noconfirm ^
    --add-data "src\clab_datalogger_receiver\icons\SPARCS_logo_v2_nobackground.png;icons" ^
    --add-data "templates\struct_cfg_template.yaml\;templates" ^
    .\clab_datalogger_receiver_app.py    