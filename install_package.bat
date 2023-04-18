#!bin/bash

echo "This can take a while"

timeout 5 || sleep 5

python -m pip install .

pause
