
python -m nuitka ^
    --onefile ^
    --windows-console-mode=disable ^
    --include-package=clab_datalogger_receiver ^
    --include-data-dir=src/clab_datalogger_receiver/templates=clab_datalogger_receiver/templates ^
    --include-data-dir=src/clab_datalogger_receiver/icons=clab_datalogger_receiver/icons ^
    --plugin-enable=pyside6 ^
    --nofollow-import-to=tkinter ^
    --output-dir=dist ^
    --onefile-tempdir-spec="{CACHE_DIR}/{COMPANY}/{PRODUCT}/{VERSION}" ^
    --company-name=sparcs-unipd ^
    --product-name=clab_datalogger_receiver ^
    --file-version=0.4.0 ^
    --product-version=0.4.0 ^
    --assume-yes-for-downloads ^
    %* ^
    .\clab_datalogger_receiver_app.py
