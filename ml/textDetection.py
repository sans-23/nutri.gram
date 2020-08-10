from imutils.object_detection import non_max_suppression
import numpy as np
import argparse
import time
import cv2
import tesserocr
from PIL import Image

import re
from fuzzywuzzy import fuzz

from os import path

PATH = path.abspath('./tessdata')
H = W = None
rW = rH = None
# Note: width and height should be multiple of 32


def load_and_resize(path, width, height):
    global W, H, rW, rH
    # load the input image and grab the image dimensions
    image = cv2.imread(path)
    orig = image.copy()
    (H, W) = image.shape[:2]
    # set the new width and height and then determine the ratio in change
    # for both the width and height
    (newW, newH) = (width, height)
    rW = W / float(newW)
    rH = H / float(newH)
    # print(W, H, rW, rH)
    # resize the image and grab the new image dimensions
    image = cv2.resize(image, (newW, newH))
    (H, W) = image.shape[:2]
    return image, orig


# load the pre-trained EAST text detector
print("[INFO] loading EAST text detector...")
net = cv2.dnn.readNet('./models/frozen_east_text_detection.pb')


def detectTextsArea(image, orig, confidence):
    global W, H, rW, rH

    readTexts = []
    # define the two output layer names for the EAST detector model that
    # we are interested -- the first is the output probabilities and the
    # second can be used to derive the bounding box coordinates of text
    layerNames = [
        "feature_fusion/Conv_7/Sigmoid",
        "feature_fusion/concat_3"]

    # construct a blob from the image and then perform a forward pass of
    # the model to obtain the two output layer sets
    blob = cv2.dnn.blobFromImage(image, 1.0, (W, H),
                                 (123.68, 116.78, 103.94), swapRB=True, crop=False)
    start = time.time()
    net.setInput(blob)
    (scores, geometry) = net.forward(layerNames)
    end = time.time()

    # show timing information on text prediction
    print("[INFO] text detection took {:.6f} seconds".format(end - start))

    # grab the number of rows and columns from the scores volume, then
    # initialize our set of bounding box rectangles and corresponding
    # confidence scores
    (numRows, numCols) = scores.shape[2:4]
    rects = []
    confidences = []

    # loop over the number of rows
    for y in range(0, numRows):
        # extract the scores (probabilities), followed by the geometrical
        # data used to derive potential bounding box coordinates that
        # surround text
        scoresData = scores[0, 0, y]
        xData0 = geometry[0, 0, y]
        xData1 = geometry[0, 1, y]
        xData2 = geometry[0, 2, y]
        xData3 = geometry[0, 3, y]
        anglesData = geometry[0, 4, y]

        # loop over the number of columns
        for x in range(0, numCols):
            # if our score does not have sufficient probability, ignore it
            if scoresData[x] < confidence:
                continue

            # compute the offset factor as our resulting feature maps will
            # be 4x smaller than the input image
            (offsetX, offsetY) = (x * 4.0, y * 4.0)

            # extract the rotation angle for the prediction and then
            # compute the sin and cosine
            angle = anglesData[x]
            cos = np.cos(angle)
            sin = np.sin(angle)

            # use the geometry volume to derive the width and height of
            # the bounding box
            h = xData0[x] + xData2[x]
            w = xData1[x] + xData3[x]

            # compute both the starting and ending (x, y)-coordinates for
            # the text prediction bounding box
            endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
            endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
            startX = int(endX - w)
            startY = int(endY - h)

            # add the bounding box coordinates and probability score to
            # our respective lists
            rects.append((startX, startY, endX, endY))
            confidences.append(scoresData[x])

    # apply non-maxima suppression to suppress weak, overlapping bounding
    # boxes
    boxes = non_max_suppression(np.array(rects), probs=confidences)
   
    # loop over the bounding boxes
    for (startX, startY, endX, endY) in boxes:
        # scale the bounding box coordinates based on the respective
        # ratios
        startX = int(startX * rW)
        startY = int(startY * rH)
        endX = int(endX * rW)
        endY = int(endY * rH)

        # print(startX, endX)
        # print(startY, endY)
        box_offset_neg = -15
        box_offset_pos = 15

        text = readText(orig[startY+box_offset_neg:endY+box_offset_pos,
                             startX+box_offset_neg:endX+box_offset_pos])
        readTexts.append(text.replace('\n',''))
        # draw the bounding box on the image
        cv2.rectangle(orig, (startX, startY), (endX, endY), (0, 255, 0), 2)
       # print(text)
        cv2.putText(orig, text, (startX, startY-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, 255)
    
    return readTexts

def detectTexts(image,orig):
    global W, H, rW, rH

    texts = []
    matched = []
    keyval = {}
    text = readText(orig)

    texts = text.split('\n')
    for line in texts:
        words = line.lower().replace('total ','').replace('total','').split(' ')
        print(words)
        result = matchText(words,dbTexts)
        matched.extend(result)
        keyval[result[0]] = ' '.join(result[1:])


    print("TExts: ",texts)
    print("Matched: ", matched)
    print(keyval)
    
    return keyval


def readText(roi):
    # cv2.imshow("Area", roi)
    # cv2.waitKey(0)
    img = Image.fromarray(roi)

    return tesserocr.image_to_text(img, path=PATH)
def matchText(readTexts,dbTexts):
    '''
        Match the texts read by application to the keywords defined in database
        readTexts: list of texts that application read
        dbTexts: list of tags user set to track
    '''

    matchRatio = 40

    print("Matching Texts")
    for i,text in enumerate(readTexts):
        maxRatio = 0
        maxj = 0
        # print(text)
        newText = re.sub(r'^[0-9]+','',text,5)

        if(len(newText)==0): continue

        if(newText != text):
            continue
        # print(text)
        for j,tag in enumerate(dbTexts):
            ratio = fuzz.ratio(text,tag)
            print(text,tag,ratio)
            if ratio > matchRatio and ratio > maxRatio:
                maxRatio = ratio
                maxj = j
        if(maxRatio > matchRatio):
            readTexts[i] = dbTexts[maxj]
    return readTexts

dbTexts = [
        'Carbohydrate', 'Calories', 'Protein', 'Fat', 'Carbs', 'KCal', 'g', 'gm'
    ]

if __name__ == "__main__":
    image, orig = load_and_resize('./images/threshold_cropped.jpg', 640,480)

    

    # texts = detectTextsArea(image, orig, 0.4)
    texts = detectTexts(image,orig)
    # print(orig.shape)
    cv2.imshow("TextDetection", orig)
    cv2.imshow("TextDetection ", orig)

    cv2.waitKey(0)
   
    
