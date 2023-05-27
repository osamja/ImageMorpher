from rest_framework.exceptions import APIException

class FaceDetectException(APIException):
    status_code = 422
    default_detail = 'Face detection failed'
    default_code = 'face_detect_error'
