import time
import cv2
import cv2.cv as cv
import math
import random
import io
import Image
# from apiclient.http import MediaIoBaseUpload

"""
Rectangles are coordinates of upper left and lower right corners.
Colors are in BGR??
"""


# Ratio of width to height of timeline images.
RATIO = 0.66

def face_detect(img, cascade_fn='haarcascades/haarcascade_frontalface_alt.xml',
           scaleFactor=1.3, minNeighbors=2, minSize=(20, 20),
           flags=cv.CV_HAAR_SCALE_IMAGE):
    """
    Given an image, find the faces.
    """
    cascade = cv2.CascadeClassifier(cascade_fn)
    rects = cascade.detectMultiScale(img, scaleFactor=scaleFactor,
                                     minNeighbors=minNeighbors,
                                     minSize=minSize, flags=flags)
    print "RECT", rects
    if len(rects) == 0:
        return []
    rects[:, 2:] += rects[:, :2]
    return rects


def draw_rects(img, rects, color):
    """
    Given an image, sets of rectangles, and a color, draw them on img. img will be now be the image + rectangles.
    """
    for x1, y1, x2, y2 in rects:
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)


def draw_circles(img, circles, color):
    """
    Given rectangles, create and draw circles with center point at the center of the rectangle and with radius = half
    the diagonal of the rectangle.
    """
    for rect in circles:
        center = center_of_rectangle(rect)
        radius = radius_of_rectangle(rect)
        print "RCR", rect, center, radius
        cv2.circle(img, center, int(radius * .75), color, thickness=20)


def center_of_rectangle(rect):
    """
    Standard center point of rectangle formula (truncated)
    """
    x1, y1, x2, y2 = rect
    return int((x2 + x1) / 2), int((y2 + y1) / 2)


def distance(x1, y1, x2, y2):
    """
    Standard distance formula (truncated)
    """
    return int(math.sqrt((x1 - x2)**2 + (y1 - y2)**2))


def radius_of_rectangle(rect):
    """
    Given rectangle, find half the diameter (truncated)
    """
    return int(distance(rect[0], rect[1], rect[2], rect[3]) / 2)


def power_level(rect):
    """
    Figure out power level based on how much blonde hair is in the picture.
    """
    return "9001"


def write_text(img, rect, text, font_color):
    """
    Try to intelligently write the give text above (preferred) or below the image.
    """

    cv2.putText(img, text, (rect[0] -100, rect[2] -100), cv2.FONT_HERSHEY_SIMPLEX, 8.0, font_color,
            thickness=20, lineType=cv2.CV_AA)


def slice_face(rect, img):
    """
    Given a rectangle and the image, attempts to slice an image of the appropriate dimensions.
    Returns filename of image.
    """
    # Decide image width
    width = rect[3] - rect[1]
    height = width + width / 2
    # Extra bit to add on to the top and bottom of image so we get an image of appropriate height for our card.
    extra_crop = width / 4
    print "hxw", height, width
    filename = '%030x' % random.randrange(16**30)
    print filename
    cv2.imwrite('/tmp/{0}.jpg'.format(filename) ,img[rect[1]-extra_crop:rect[3]+extra_crop, rect[0]:rect[2]])
    size= 240, 360
    im = Image.open('/tmp/{0}.jpg'.format(filename))
    im.thumbnail(size, Image.ANTIALIAS)
    im.save('/tmp/{0}.jpg'.format(filename), "JPEG")
    return filename


def create_card(face, power):
    """
    Creates the HTML and meta data for a timeline Glass card from a face and a power level.
    """

    # timeline_item = {'text': 'Hello world'}
    # media_body = MediaIoBaseUpload(
    #     io.BytesIO(face), mimetype="image/jpeg", resumable=True)
    # service.timeline().insert(body=timeline_item, media_body=media_body).execute()


def scout(image_in):
    """
    Returns an array of tuples in the form (filename, power level)
    """
    print ">>> Loading image..."
    # Save it, then read it in. What a pain.
    # filename = '%030x' % random.randrange(16**30)
    # with open('/tmp/{0}.jpg'.format(filename), 'w') as f:
    #     f.write(image_in)
    font_color = (68,205,228)
    img_color = cv2.imread(image_in)
    img_gray = cv2.cvtColor(img_color, cv.CV_RGB2GRAY)
    img_gray = cv2.equalizeHist(img_gray)
    print image_in, img_gray.shape
 
    print ">>> Detecting faces..."
    start = time.time()
    rects = face_detect(img_gray)
    print 'rects', rects
    end = time.time()
    print 'time:', end - start
    img_out = img_color.copy()
    faces = []
    cards = []
    for rect in rects:
        faces.append(slice_face(rect, img_out))
    for face in faces:
        power = power_level(face)
        power_tuple = (face, power)
        cards.append(power_tuple)
    return cards
    # cv2.imwrite(image_out, img_out)
 
 
def main():
    """
    Just for testing!
    """
    for pic in ['img/kuhn.jpg',]:
    # for pic in ['pic.jpg', 'pic1.jpg', 'pic2.jpg', 'pic3.jpg', 'pic4.jpg', 'kuhn.jpg']:
        scout(pic, )
 
 
if __name__ == '__main__':
    main()
