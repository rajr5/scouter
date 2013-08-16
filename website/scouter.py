from __future__ import division
import time
import cv2
import cv2.cv as cv
import math
import random
import io
import Image
import os
import logging
# from apiclient.http import MediaIoBaseUpload

"""
Rectangles are coordinates of upper left and lower right corners.
Colors are in BGR??
"""
blond_color_range = {'r': (209, 255), 'g': (137, 242), 'b': (65, 154)}
black_color_range = {'r': (0, 40), 'g': (0, 40), 'b': (0, 40)}
red_color_range = {'r': (123, 252), 'g': (11, 252), 'b': (51, 252)}

logger = logging.getLogger('debugger')

# Ratio of width to height of timeline images.
RATIO = 0.66

"""
General form of power level calculation:
pl = min + (max-min/100000) * power level
"""


# def ssj1(percent):
#     """
#     Given blond percentage, return a power level. Accodring to http://dragonball.wikia.com/wiki/List_of_Power_Levels,
#     SSJ should go from about 150mil to 2.5bil.
#     @param percent:
#     @type percent:
#     @return:
#     @rtype:
#     """
#     if percent < 1:
#         return 0
#     if percent > 10:
#         percent = 10
#     return ((25000000000/100000) * (percent ** 4))
#
# def kaio_ken(percent):
#     """
#     Given the red percentage, return a power level. We see Kaio-ken power levels from 8k (normal v Vegeta)
#     to 60mil (x20, against Frieza)
#     @param percent:
#     @type percent:
#     @return:
#     @rtype:
#     """
#     if percent < 1:
#         return 0
#     if percent > 10:
#         percent = 10
#     return (60000000/10000) * (percent ** 4)

def saiyan(percent):
    """
    Given the black percentage, return a power level. We see non SSJ Saiyans from about 1k (Raditz) to let's say 8k.
    @param percent:
    @type percent:
    @return:
    @rtype:
    """
    if percent < 1:
        return 0
    if percent > 10:
        percent = 10
    return 5000 + ((50000/2000) * (percent ** 4))

def percent_in_color_range(pic,x,y,color_range):
    """
    Checks each pixel to see if its rgb color is between all the upper and lower bounds in color_range. Returns
    a percent of the image that is in the range from 0 to 100.
    @param pic: An image loaded by PIL via Image.open(file).load()
    @type pic: PIL loaded image
    @param x: width in px
    @type x: int
    @param y: height in v
    @type y: int
    @param color_range: {'r': (lower bound, upperbound), 'g': (l, u), 'b': (l, u)}
    @type color_range: dict
    @return: percent of image that is a color from 0 to 100.
    @rtype: float
    """
    total_px = 0
    color_px = 0
    rl, ru = color_range['r']
    gl, gu = color_range['g']
    bl, bu = color_range['b']
    for i in range(0, int(y)):
        for j in range(0, int(x / 4)):
            r, g, b = pic[j * 4, i]
            # print r, g, b
            # If the pix color is inside the range (inclusive), add one.
            if rl <= r <= ru and gl <= g <= gu and bl <= b <= bu:
                color_px += 1
            total_px += 1
    logger.debug("Percent in color, color: {0}, total: {1}, returning: {2}".format(color_px, total_px, color_px / total_px * 100))
    return color_px / total_px * 100



def power_level(face):
    """
    Given a face file, analyze for power levels.
    @param face:
    @type face:
    @return:
    @rtype:
    """

    im = Image.open(face)
    size_of_image = im.size
    x = size_of_image[0]
    y = size_of_image[1]

    pic = im.load()
    # blond = percent_in_color_range(pic, x, y, blond_color_range)
    black = percent_in_color_range(pic, x, y, black_color_range)
    # red = percent_in_color_range(pic, x, y, red_color_range)
    # logger.debug("Image colors: blond {0}, black {1}".format(blond, black))
    logger.debug("Image colors: black {0}".format(black))
    # TODO Apply a weighting algorithm to see which type of power level we're looking at (SSJ or SSJ4).
    # blond_power = ssj1(blond)
    black_power = saiyan(black)
    # red_power = kaio_ken(red)
    # print "Blond, black, red power: ", blond_power, black_power, red_power
    # power = max(blond_power, black_power, red_power)
    power = black_power
    if power < 1000:
        return random.randint(1,206)
    else:
        return int(power)


def face_detect(img, cascade_fn='haarcascades/haarcascade_frontalface_alt.xml',
                scaleFactor=1.3, minNeighbors=2, minSize=(100, 100),
                flags=cv.CV_HAAR_SCALE_IMAGE):
    """
    Given an image, find the faces.
    """
    cascade = cv2.CascadeClassifier(cascade_fn)
    rects = cascade.detectMultiScale(img, scaleFactor=scaleFactor,
                                     minNeighbors=minNeighbors,
                                     minSize=minSize, flags=flags)
    if len(rects) == 0:
        return []
    rects[:, 2:] += rects[:, :2]
    return rects


def slice_face(rect, img, store_faces_path):
    """
    Given a rectangle and the image, attempts to slice an image of the appropriate dimensions.
    Returns filename of image.
    """
    # Decide image width
    width = rect[3] - rect[1]
    height = width + width / 2
    logger.debug("Face height/width: {0} x {1}".format(height, width))
    # Extra bit to add on to the top and bottom of image so we get an image of
    # appropriate height for our card.
    extra_crop = width / 4
    filename = '%030x' % random.randrange(16 ** 30)
    file_path = os.path.join(store_faces_path, filename + '.jpg')
    logger.debug("Cropping: {0}, {1}, {2}, {3}".format(rect[1] - extra_crop, rect[3] + extra_crop, rect[0], rect[2]))
    cv2.imwrite('/tmp/{0}.jpg'.format(filename), img[rect[1] - extra_crop:rect[3] + extra_crop, rect[0]:rect[2]])
    size = 240, 360
    im = Image.open('/tmp/{0}.jpg'.format(filename))
    im.thumbnail(size, Image.ANTIALIAS)
    im.save(file_path, "JPEG")
    return file_path


def scout(image_in, store_faces_path='/tmp/'):
    """
    Returns an array of tuples in the form (filename, power level)
    """
    # Save it, then read it in. What a pain.
    # filename = '%030x' % random.randrange(16**30)
    # with open('/tmp/{0}.jpg'.format(filename), 'w') as f:
    #     f.write(image_in)
    # font_color = (68, 205, 228)
    img_color = cv2.imread(image_in)
    img_gray = cv2.cvtColor(img_color, cv.CV_RGB2GRAY)
    img_gray = cv2.equalizeHist(img_gray)
    start = time.time()
    rects = face_detect(img_gray)
    img_out = img_color.copy()
    faces = []
    cards = []
    for rect in rects:
        faces.append(slice_face(rect, img_out, store_faces_path))
    for face in faces:
        power = power_level(face)
        cards.append({'power_level': power, 'face': face})
        logger.debug("Wrote face to {0} from original image {1} with power level: {2}".format(image_in, face, power))
    end = time.time()
    logger.debug("Found {0} face(s) in {1} seconds".format(len(cards), end-start))
    return cards
    # cv2.imwrite(image_out, img_out)


def main():
    """
    Just for testing!
    """
    for pic in ['davis.jpg', ]:
    # for pic in ['pic.jpg', 'pic1.jpg', 'pic2.jpg', 'pic3.jpg', 'pic4.jpg',
    # 'kuhn.jpg']:
        print scout(pic, )


if __name__ == '__main__':
    main()
