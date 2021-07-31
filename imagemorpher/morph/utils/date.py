import sys
# morph is essentially the src root directory in this file now
#   aka import all files with morph/<file-path>
sys.path.insert(0, '/app/imagemorpher/morph')

import datetime
import logging
logging.basicConfig(filename='morph/logs/morph-app-perf.log', level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')


def getMorphDate():
  morphDate = str(datetime.datetime.now())
  morphDate = morphDate.replace(" ", "-")
  morphDate = morphDate.replace(":", "-")
  morphDate = morphDate.replace(".", "-")
  return morphDate
