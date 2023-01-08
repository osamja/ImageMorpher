# The purpose of this file is to automatically delete user generated content older than a given time.
# This python file should be periodically executed through a cron job.

# CRON tab that runs this script every 24 hours
# crontab -e (for initiating crontab file)
# crontab -l for viewing cron tasks
# 0 0 * * * /usr/bin/python /home/sammy/ImageMorpher/imagemorpher/morph/utils/auto_delete.py >> /home/sammy/ImageMorpher/imagemorpher/morph/logs/auto-delete-cron.log 2>&1

"""
Algorithm:
For each file in our directory of saved morphed imgs
    if file older than 30 days
        delete file
"""

import os
import time
from datetime import timedelta, datetime, date

def get_date_x_days_ago(x_days_ago, date_from=None):
    return datetime.strptime(date_from, '%Y-%m-%d').date() - timedelta(x_days_ago) if date_from else date.today()-timedelta(x_days_ago)

# change to directory where morphed images are stored
path_of_saved_morphs = '/home/sammy/ImageMorpher/imagemorpher/morph/content/temp_morphed_images'
os.chdir(path_of_saved_morphs)

# get list of all filenames
morphed_filenames = os.listdir(path_of_saved_morphs)

# get current year-month
today = time.strftime("%Y-%m-%d")

# get date 30 days ago
previous_date = datetime.strftime(get_date_x_days_ago(x_days_ago=3, date_from=today), "%Y-%m-%d")

for morphed_filename in morphed_filenames:
    morphed_file_date = datetime.strptime(morphed_filename[:10], "%Y-%m-%d")
    previous_date_obj = datetime.strptime(previous_date, "%Y-%m-%d")
    
    if morphed_file_date < previous_date_obj:
        os.remove(morphed_filename)
