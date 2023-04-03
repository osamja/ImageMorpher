import dramatiq
import uuid
import numpy as np
import datetime
from PIL import Image
import logging
import requests
logger = logging.getLogger(__name__)
from pytz import timezone

from .morph import morph
from .utils.date import getMorphDate
from .utils.image_sources import saveImg, deleteImg
from .utils.graphics import getCroppedImagePath, getCroppedImageFromPath

# Assuming a redis container named "my-redis" is running
# docker run --name my-redis -p 6379:6379 -d redis

# And that you have a container named "face-morpher-api" running linked to my-redis with the redis alias
# docker container run -it --link my-redis:redis -v /home/sammy/ImageMorpher:/app face-morpher-api bash

# We can setup the broker to connect to the redis container
# redis_broker = RedisBroker(host="redis")
# dramatiq.set_broker(redis_broker)

@dramatiq.actor(max_retries=0)
def processMorph(isMorphSequence, stepSize, duration, img1_path, img2_path, morphSequenceTime, push_token=None):
    img1 = getCroppedImageFromPath(img1_path)
    img2 = getCroppedImageFromPath(img2_path)

    # img1 = skio.imread('/home/sammy/development/ImageMorpher/imagemorpher/morph/images/obama_small.jpg')
    # img2 = skio.imread('/home/sammy/development/ImageMorpher/imagemorpher/morph/images/george_small.jpg')

    if (isMorphSequence):
        morphed_img_uri_list = []

        for i in range(0, 101, stepSize):
            t = float(i / 100) or 0
            _img1 = np.copy(img1)
            _img2 = np.copy(img2)
            morphed_img_filename, morphed_im = getMorphedImgUri(_img1, _img2, t)
            morphed_img_uri_list.append((morphed_img_filename, morphed_im))
        
        fileHash = uuid.uuid4()
        morphDate = getMorphDate()
        gif_filename = morphDate + '-' + fileHash.hex + '.gif'
        morphed_gif_path = 'morph/content/temp_morphed_images/' + gif_filename    # location of saved image
        morphed_gif_uri = 'https://pyaar.ai/facemorphs/' + gif_filename     # /facemorphs directory serves static content via nginx

        morphed_im_list = []
        for i, im in enumerate(morphed_img_uri_list):
            morphed_im_filename = 'morph/content/temp_morphed_images/' + im[0]
            morphed_im = Image.open(morphed_im_filename)
            morphed_im_list.append(morphed_im)
        first_image = morphed_im_list[0]
        appended_images = morphed_im_list[1:]
        first_image.save(morphed_gif_path, save_all=True, append_images=appended_images, loop=0, duration=duration)

        # Remove all generated jpgs except the GIF
        for i, im in enumerate(morphed_img_uri_list):
            img_filename = 'morph/content/temp_morphed_images/' + im[0]
            # os.remove(img_filename)

        # Delete the originally uploaded photos
        # deleteImg(img1_path)
        # deleteImg(img2_path)

        body = 'Your morph is ready!'

        if (push_token):
            send_message(push_token, 'Morph Complete', body, morphed_gif_uri)

        return morphed_gif_uri
    else:
        morphed_img_filename, morphed_im = getMorphedImgUri(img1, img2, morphSequenceTime)
        morphed_img_uri = 'https://pyaar.ai/facemorphs/' + morphed_img_filename
        # deleteImg(img1_path)
        # deleteImg(img2_path)
        body = 'Your morph is ready!'

        if (push_token):
            send_message(push_token, 'Morph Complete', body, morphed_img_uri)

        return morphed_img_uri

def getMorphedImgUri(img1, img2, t):
    try:
        log_message = str(datetime.datetime.now(timezone('UTC'))) + ': Morphing images' 
        logging.info(log_message)
        morphed_img_filename, morphed_im = morph(img1, img2, t)
        return morphed_img_filename, morphed_im
    except Exception as e:
        logging.error('Error %s', exc_info=e)
        raise

def send_message(expo_token, title, body, url):
    message = {
        'to': expo_token,
        'title': title,
        'body': body,
        'data': {
            'url': url
        }
    }
    return requests.post('https://exp.host/--/api/v2/push/send', json=message)
