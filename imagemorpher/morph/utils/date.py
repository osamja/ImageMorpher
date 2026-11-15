import datetime
import logging
logging.basicConfig(filename='morph/logs/morph-app-perf.log', level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')


def getMorphDate():
  morphDate = str(datetime.datetime.now())
  morphDate = morphDate.replace(" ", "-")
  morphDate = morphDate.replace(":", "-")
  morphDate = morphDate.replace(".", "-")
  return morphDate
