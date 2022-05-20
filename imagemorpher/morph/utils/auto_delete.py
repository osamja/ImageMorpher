# The purpose of this file is to automatically delete user generated content older than a given time.
# This python file should be periodically executed through a cron job.

# CRON tab that runs this script every 24 hours
# crontab -e (for initiating crontab file)
# crontab -l for viewing cron tasks
# 0 0 * * * /usr/bin/python /home/sammy/ImageMorpher/imagemorpher/morph/utils/auto_delete.py >/dev/null 2>&1

"""
Algorithm

#   Get current month-year
#   Go one month back (if 1 => 12) 
#   Get list of files from previous month (Hmm we'll need to use something like find)
#       remove each file (os.remove)
#   Run crontab on server executing this python script
"""

import os
import time
from datetime import timedelta, datetime, date

def get_date_x_days_ago(x_days_ago, date_from=None):
    return datetime.strptime(date_from, '%Y-%m-%d').date() - timedelta(x_days_ago) if date_from else date.today()-timedelta(x_days_ago)

# change to directory where morphed images are stored
os.chdir('/home/sammy/ImageMorpher/imagemorpher/morph/content/temp_morphed_images')

# get list of all filenames
morphed_filenames = os.listdir()

# get current year-month
today = time.strftime("%Y-%m-%d")

# get date 30 days ago
previous_date = datetime.strftime(get_date_x_days_ago(x_days_ago=30, date_from=today), "%Y-%m-%d")

for morphed_filename in morphed_filenames:
    if morphed_filename.startswith(previous_date):
        os.remove(morphed_filename)
