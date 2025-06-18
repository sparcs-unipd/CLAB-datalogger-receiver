# CLAB-datalogger-receiver
This repo is a reimplementation of the MATLAB datalogger project in python.

This is to prevent some errors occurring during the ERTC
(Embedded Real-Time Control) course due MATLAB's
serial interface that was not working properly,
and also to increase code portability.

![datalogger-screenshot](docs/images/datalogger_screenshot.png)

## Docs

To have a better insight of te project, you can head over to the more extensive
[docs](/docs/index.md).

## WARNING

**You NEED to configure the data received structure via the** [`struct_cfg.yaml`](struct_cfg.yaml) **file**.

If it is not found in the folder where the executable is run,
it is created based on the [`templates/struct_cfg_template.yaml`](src/clab_datalogger_receiver/templates/struct_cfg_template.yaml).

### Editing the Configuration

You can edit the data structure configuration directly from the application UI:

- Click the **"Edit Config"** button in the main window.
- This opens a graphical editor for `struct_cfg.yaml`, where you can add, remove, or modify subplots and traces.
- After saving your changes, the application will automatically reload the configuration and redraw the plots to reflect your updates.

Alternatively, you can manually edit the `struct_cfg.yaml` file with a text editor.

## How-to

This is a runnable package, meaning that it is possible to run

```console
python -m clab_datalogger_receiver
```

or by launching the `run_receiver.bat` file.

Notice that the package needs first to be installed.

This can be done by running `install_package.bat`

On launch, it will connect to the serial port,
(asking which one, if multiple are available),
and send the `START_TRANSMISSION` token to the datalogger.

It is possible to stop the data recording both by pressing `CTRL+C` or by closing the plot window.

The script will then ask if it should save the data (default is yes).

## Packets configuration

It is possible to configure the serial data format in (mainly) two ways:

- By editing the file [`struct_cfg.yaml`](struct_cfg.yaml), that is loaded by the function call `PlottingStruct.from_yaml_file()`
- By calling the function `PlottingStruct.from_string_list(formats list)`, where formats is a list of format string that follows the convention of python's `struct`, as in [here](https://docs.python.org/3/library/struct.html#format-characters)
