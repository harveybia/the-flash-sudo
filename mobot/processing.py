#from utils import init, info, warn, term2
import numpy as np
import cv2
from matplotlib import pyplot as plt

def get_grey(pic, sample_rows = 5, col_step = 5, rank = 5):
    # Get the prefect grey value from a black/white picture
    # @params
    # sample_rows: (int) # of random rows to sample
    # col_step: (int) # of columns to skip
    # rank: (int) record the top *rank* most white/black pixel
    sample_index = range(len(pic))
    random.shuffle(sample_index)
    sample = []
    for i in ranges(sample_rows):
        row = sample_index[i]
        for j in xrange(0, len(row), col_step):
            pixel = row[j]
            sample.append(pixel)
    return get_thereshold(sample)

def get_white_segments_from_row(pic, row, 
        sample_rows = 5, buckets = 50, min_length = 30, max_gap = 4):
    # Get the white segments from the bottom few rows of a black/white picture
    # @params
    # row: (int) Normally should be larger than sample_rows
    # sample_rows: (int) # of concequtive bottom rows to sample
    # buckets: (int) the resolution of sampling
    # min_length: (int) the minimum length a valid segment can have
    # min_interval: (int) the maximum gap interms of # of buckets
    # between two segments that allows them to be merged
    height = len(pic)
    width = len(pic[0])
    sample = pic[max(0, row - sample_rows): row]
    bucket_size = (width - 1) / buckets + 1
    histogram = get_histogram(sample, buckets)
    thereshold = get_thereshold(histogram)
    assert len(histogram) == buckets
    # Find the starts and ends for the white segments
    black_flag = True   # We start from black region
    result = []
    start, end = 0, None
    gap = None
    for i in range(buckets):
        value = histogram[i]
        if value > thereshold:
        # We are seeing a white region
            if black_flag:
                black_flag = False
                if gap != None and gap < max_gap:
                # We are just seeing white with a little interuption
                    pass
                else:
                    if end != None: 
                        # This is not the first time we've seen white
                        result.append((start, end))
                    start = i * bucket_size
            gap = 0
        else:
        # We are seeing a black region
            if gap != None:
                # We've seen white, counting the gap 
                gap += 1
            if not black_flag:
                black_flag = True
                end = i * bucket_size
                # result.append((start, end))
    if start > end:
        # We need to add the last segment
        result.append((start, width))
    else: result.append((start, end))
    assert result != []
    # get rid of segments that are too short
    i = 0
    while i < len(result):
        segment = result[i]
        if abs(segment[1] - segment[0]) < min_length:
            result.pop(i)
        else: i += 1

    if len(result) > 2: 
        print("More than 2 white lines detected, possible error!")
    return result

def get_histogram(A, buckets):
    # Get the histogram from a 2D list A
    # (Add numbers to buckets that correspond to col intervals)
    # @params
    # A: (list<list<int>>) the rows of numbers to sample
    # buckets: (int) the # of buckets
    assert A != []
    n = len(A[0])
    assert n > 0
    bucket_size = (n - 1) / buckets + 1
    result = [0] * buckets
    for row in A:
        # The input should be rectangular
        assert len(row) == n
        for i in range(n):
            bucket = i / bucket_size
            result[bucket] += row[i]
    return result

def get_thereshold(l, rank = 2):
    # Get the mid(separator) value from a list of integers
    # @params
    # l: (list<int>) the list of intergers
    # rank: (int) discard the top *rank* highest/lowest entries
    assert rank > 0
    if len(l) < rank: 
        warn("List too short for rank!")
        rank = len(l)
    sorted_list = sorted(l)
    lo = sorted_list[rank - 1]
    hi = sorted_list[len(l) - rank]
    return (lo + hi) / 2

def test_perspective():
    img = cv2.imread('../tests/1.jpg')
    rows,cols,ch = img.shape
    cv2.line(img,(0,0),(1000,511),(0,0,250),5)
    pts1 = np.float32([[0,0],[cols,0],[0,rows],[cols,rows]])
    pts2 = np.float32([[0,0],[cols,rows/3],[0,rows],[cols,rows * 2 / 3]])

    M = cv2.getPerspectiveTransform(pts1,pts2)

    dst = cv2.warpPerspective(img,M,(cols,rows))

    plt.subplot(121),plt.imshow(img),plt.title('Input')
    plt.subplot(122),plt.imshow(dst),plt.title('Output')
    plt.show()

def test_get_line_segment():
    img = cv2.imread('../tests/4.jpg')
    height, width = 300, 300
    img = cv2.resize(img,(width, height), interpolation = cv2.INTER_CUBIC)
    rows,cols,ch = img.shape
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    interval = 15
    for i in xrange(15):
        row = height - i * interval
        result = get_white_segments_from_row(img, row)
        print(result)
        for segment in result:
            cv2.line(img,(segment[0],row),(segment[1], row),(0,0,255),5)
    plt.imshow(img, cmap = 'gray', interpolation = 'bicubic')
    plt.xticks([]), plt.yticks([])  # to hide tick values on X and Y axis
    plt.show()

def test():pass

if __name__ == '__main__':
    test_get_line_segment()
