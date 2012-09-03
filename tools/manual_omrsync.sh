#!/bin/bash

# */5 * * * * /bin/bash /home/mvp/sms/tools/manual_omrsync.sh >/dev/null 2>&1
cd /home/mvp/src/childcount/childcount
if ps aux | grep -v grep | grep manual_omrsync.py > /dev/null
then
    echo "manual_omrsync.py is running!." 
else
    echo "starting manual_omrsync.py ..."
    /home/mvp/src/childcount/childcount/tools/manual_omrsync.py 10000 > /dev/null
fi
