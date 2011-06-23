Frequently Asked Questions
============================

.. contents::

How can I copy the MySQL database from the server to my local machine?
-----------------------------------------------------------------------
Run the following commands in a local shell/terminal::

    # Connect to the CC+ server, replacing
    # CC_SERVER_IP with the IP address of your
    # ChildCount+ server
    ssh mvp@CC_SERVER_IP
    
    # Dump CC+ database to a file called "childcount_dump.sql"
    # in the mvp home directory
    mysqldump -u childcount -pchildcount childcount > ~/childcount_dump.sql

    # Quit SSH connection to server
    exit

    # Now you are on your local machine.
    # Copy the SQL file from the server to your
    # local machine.
    scp mvp@CC_SERVER_IP:~/childcount_dump.sql ~/childcount_dump.sql

    # Load the file into your development database
    mysql -u childcount -pchildcount childcount < ~/childcount_dump.sql

That's it!

How can I update the translations for my language?
---------------------------------------------------

Each app is translated independently,
but for ChildCount+ to work, all apps should be translated.
The ChildCount+ apps are listed in :doc:`api/apps/index`.

Here is how you update the translations from an Ubuntu machine::
   
    # Make sure you have poedit installed
    sudo apt-get install poedit

    # Change to the directory of the app that you want to 
    # translate. For example, if ChildCount+ is installed in 
    # ~/sms, here is how you translate apps/childcount:
    cd ~/sms/apps/childcount

    # Make sure that you're on the development branch
    git checkout ccdev

    # Make sure that the locale directory exists
    mkdir locale

    # Update message file with new untranslated strings.
    # Replace "fr" with the two-letter code for your 
    # language.
    django-admin.py makemessages -l fr -e html,json,py

    # Edit the .po file for your language. Replace "fr"
    # with the two-letter code for your language.
    poedit locale/fr/LC_MESSAGES/django.po

    # After saving the .po file, compile the translations.
    django-admin.py compilemessages

    # Add the files to git and commit them.
    git add locale
    git commit -m "New translations"
    
    # Push new files to the repository
    git push
    

