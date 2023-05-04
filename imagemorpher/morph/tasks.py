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

from .models import Morph

@dramatiq.actor(max_retries=0)
def processMorph(morph_id_str ,push_token=None):

    morph_id = uuid.UUID(morph_id_str)
    morph_instance = Morph.objects.get(id=morph_id)

    isMorphSequence = morph_instance.is_morph_sequence
    stepSize = morph_instance.step_size
    img1_path = morph_instance.first_image_ref
    img2_path = morph_instance.second_image_ref
    morphSequenceTime = morph_instance.morph_sequence_time
    morph_uri = morph_instance.morphed_image_ref
    morph_filepath = morph_instance.morphed_image_filepath
    duration = morph_instance.duration

    morph_instance.status = 'processing'
    morph_instance.save()

    img1 = getCroppedImageFromPath(img1_path)
    img2 = getCroppedImageFromPath(img2_path)

    # img1 = skio.imread('/home/sammy/development/ImageMorpher/imagemorpher/morph/images/obama_small.jpg')
    # img2 = skio.imread('/home/sammy/development/ImageMorpher/imagemorpher/morph/images/george_small.jpg')

    try:
        if (isMorphSequence):
            morphed_img_uri_list = []

            for i in range(0, 101, stepSize):
                t = float(i / 100) or 0
                _img1 = np.copy(img1)
                _img2 = np.copy(img2)
                morphed_img_filename, morphed_im = morph(_img1, _img2, t)
                morphed_img_uri_list.append((morphed_img_filename, morphed_im))

            morphed_im_list = []
            for i, im in enumerate(morphed_img_uri_list):
                morphed_im_filename = 'morph/content/temp_morphed_images/' + im[0]
                morphed_im = Image.open(morphed_im_filename)
                morphed_im_list.append(morphed_im)
            first_image = morphed_im_list[0]
            appended_images = morphed_im_list[1:]
            first_image.save(morph_filepath, save_all=True, append_images=appended_images, loop=0, duration=duration)

            # Remove all generated jpgs except the GIF
            for i, im in enumerate(morphed_img_uri_list):
                img_filename = 'morph/content/temp_morphed_images/' + im[0]
                # os.remove(img_filename)

            # Delete the originally uploaded photos
            # deleteImg(img1_path)
            # deleteImg(img2_path)

            # update morph status to complete
            morph_instance.status = 'complete'
            morph_instance.save()

            if (push_token):
                title = 'Morph Complete'
                body = 'Your morph is ready!'
                send_message(push_token, title, body, morph_uri)

            return morph_uri
        else:
            morph_filepath, morphed_im = morph(img1, img2, morphSequenceTime, morph_filepath)
            # deleteImg(img1_path)
            # deleteImg(img2_path)

            if (push_token):
                title = 'Morph Complete'
                body = 'Your morph is ready!'
                send_message(push_token, title, body, morph_uri)

            # update morph status to complete
            morph_instance.status = 'complete'
            morph_instance.save()
            return morph_uri
    except Exception as e:
        logger.error(e)
        morph_instance.status = 'failed'
        morph_instance.save()
        return None

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
