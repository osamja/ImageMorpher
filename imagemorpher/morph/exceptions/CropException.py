from rest_framework.exceptions import APIException

class CropException(APIException):
    status_code = 422
    default_detail = 'Could not crop image, try different image.'
    default_code = 'crop_error'
