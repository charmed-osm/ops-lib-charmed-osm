import sys


import mock


class OCIImageResourceErrorMock(Exception):
    pass


sys.path.append("src")

oci_image = mock.MagicMock()
oci_image.OCIImageResourceError = OCIImageResourceErrorMock
sys.modules["oci_image"] = oci_image
