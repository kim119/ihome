# coding:utf-8
import os
import string
from random import random

from PIL.Image import Image
from six import StringIO


def captcha(self, path=None, fmt='JPEG'):
    image = Image.new('RGB', (self.width, self.height), (255, 255, 255))
    image = self.background(image)
    image = self.text(image, self.fonts, drawings=['warp', 'rotate', 'offset'])
    image = self.curve(image)
    image = self.noise(image)
    image = self.smooth(image)
    name = "".join(random.sample(string.lowercase + string.uppercase + '3456789', 24))
    text = "".join(self._text)
    out = StringIO()
    image.save(out, format=fmt)

    if path:
        image.save(os.path.join(path, name), fmt)
    return name, text, out.getvalue()


def generate_captcha(self):
    self.initialize()
    return self.captcha("")
