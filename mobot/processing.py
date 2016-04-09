from utils import init, info, warn, term2
import numpy as np
import random
import cv2
if __name__ == "__main__":
    from matplotlib import pyplot as plt

class SegmentNode(object):
    def __init__(self, segment, height):
        self.segment = segment
        # bottom row has 0 height
        self.height = height
        self.center = (int(segment[1]) + int(segment[0])) / 2
        self.prev = set()
        self.next = set()
        self.graph_size = 1

    def addNext(self, other):
        self.next.add(other)
        other.prev.add(self)

        size = self.graph_size + other.graph_size
        self.set_graph_size(size)

    def set_graph_size(self, size):
        if self.graph_size == size: return
        self.graph_size = size
        for node in self.next:
            node.set_graph_size(size)
        for node in self.prev:
            node.set_graph_size(size)

    def is_root(self):
        return len(self.prev) == 0

def get_gray(pic, sample_rows = 5, col_step = 5, rank = 5):
    # Get the prefect gray value from a black/white picture
    # @params
    # sample_rows: (int) # of random rows to sample
    # col_step: (int) # of columns to skip
    # rank: (int) discard the top *rank* most white/black pixel
    sample_index = range(len(pic))
    random.shuffle(sample_index)
    sample = []
    for i in range(sample_rows):
        row = pic[sample_index[i]]
        for j in xrange(0, len(row), col_step):
            pixel = row[j]
            sample.append(pixel)
    # print(sample)
    return get_threshold(sample, rank)

def get_white_segments_from_row(pic, row,
        sample_rows = 5, buckets = 50, min_length = 20, max_gap = 4):
    # Get the white segments from the bottom few rows of a black/white picture
    # @params
    # row: (int) Normally should be larger than sample_rows
    # sample_rows: (int) # of consecutive bottom rows to sample
    # buckets: (int) the resolution of sampling
    # min_length: (int) the minimum length a valid segment can have
    # min_interval: (int) the maximum gap interms of # of buckets
    # between two segments that allows them to be merged
    height = len(pic)
    width = len(pic[0])
    sample = pic[max(0, row - sample_rows): row]
    bucket_size = (width - 1) / buckets + 1
    histogram = get_histogram(sample, buckets)
    thereshold = get_threshold(histogram)
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
        warn("More than 2 white lines detected, possible error!")
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

def get_threshold(l, rank = 2):
    # Get the mid(separator) value from a list of integers
    # @params
    # l: (list<int>) the list of integers
    # rank: (int) discard the top *rank* highest/lowest entries
    assert rank > 0
    if len(l) < rank:
        warn("List too short for rank!")
        rank = len(l)
    sorted_list = sorted(l)
    lo = sorted_list[rank - 1]
    hi = sorted_list[len(l) - rank]
    return (int(lo) + int(hi)) / 2

def gen_segment_nodes(all_segments):
    # Generates a node for each segment.
    # Returns a list of rows of nodes
    # @params
    # all_segments: (list<list<(int, int)>>) A list of rows of segements
    result = []
    for height in xrange(len(all_segments)):
        row_segment = all_segments[height]
        row_nodes = []
        for segment in row_segment:
            row_nodes.append(SegmentNode(segment, height))
        result.append(row_nodes)
    return result

def link_segments(all_segments):
    # Generates a node for each segment and links them together.
    # Returns a list of "root" nodes (those that don't have a previous node)
    # @params
    # all_segments: (list<list<(int, int)>>) A list of rows of segements
    all_nodes = gen_segment_nodes(all_segments)
    roots = []
    for height in xrange(1, len(all_nodes)):
        row_nodes = all_nodes[height]
        for segment_node in row_nodes:
            # Link the node to some overlapping node in previous row
            for prev_node in all_nodes[height - 1]:
                if overlap(prev_node.segment, segment_node.segment):
                    prev_node.addNext(segment_node)
            if segment_node.is_root(): roots.append(segment_node)
    # Segments in the first line are always roots
    roots += all_nodes[0]
    return roots

def get_converge(roots):
    # Get the first segment where two lines converge
    # Returns a segment node (possibly None)
    # @params
    # roots: (list<SegmentNode>) A list of root nodes
    result = None
    for root in roots:
        curr = find_converge_from_node(root)
        if curr == None: continue
        height = curr.height
        if result == None or result.height > height:
            result = curr
    return result

def find_converge_from_node(curr):
    # Get the first segment where two lines converge recursively
    # Returns a segment node (possibly None)
    # @params
    # roots: (list<SegmentNode>) A list of root nodes
    if len(curr.prev) > 1: return curr
    best = None
    for node in curr.next:
        result = find_converge_from_node(node)
        if result != None:
            height = result.height
            if best == None or best.height > height:
                best = result
    return best

def get_split(roots):
    # Get the first segment where one line splits into two lines
    # Returns a segment node (possibly None)
    # @params
    # roots: (list<SegmentNode>) A list of root nodes
    result = None
    for root in roots:
        curr = find_split_from_node(root)
        if curr == None: continue
        height = curr.height
        if result == None or result.height > height:
            result = curr
    return result

def find_split_from_node(curr):
    # Get the first segment where one line splits into two lines recursively
    # Returns a segment node (possibly None)
    # @params
    # roots: (list<SegmentNode>) A list of root nodes
    if len(curr.next) > 1: return curr
    best = None
    for node in curr.next:
        result = find_split_from_node(node)
        if result != None:
            height = result.height
            if best == None or best.height > height:
                best = result
    return best

def overlap(s1, s2):
    # Returns true if two segments s1 and s2 overlap
    # @params
    # s1, s2: ((int, int)) two segments
    assert s1[0] < s1[1] and s2[0] < s2[1]
    return (s1[0] <= s2[0] and s1[1] >= s2[0]
        or s2[0] <= s1[0] and s2[1] >= s1[0])

################################
# test functions
################################

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
    for i in xrange(interval):
        row = height - i * interval
        result = get_white_segments_from_row(img, row, min_length = 10)
        # print(result)
        for segment in result:
            cv2.line(img,(segment[0],row),(segment[1], row),(0,0,255),5)
    plt.imshow(img, cmap = 'gray', interpolation = 'bicubic')
    plt.xticks([]), plt.yticks([])  # to hide tick values on X and Y axis
    plt.show()

def test_get_grey():
    img = cv2.imread('../tests/4.jpg')
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    print(get_gray(img))

def test_segment_node():
    s1 = SegmentNode((0,10), 1)
    s2 = SegmentNode((5,15), 2)
    assert overlap(s1.segment, s2.segment) and overlap(s2.segment, s1.segment)
    s1.addNext(s2)
    assert(s1.graph_size == 2 and s2.graph_size == 2)
    s3 = SegmentNode((0,0), 3)
    s1.addNext(s3)
    assert(s1.graph_size == 3 and s2.graph_size == 3 and s3.graph_size == 3)

def test_segment_tree():
    img = cv2.imread('../tests/7.jpg')
    height, width = 300, 300
    img = cv2.resize(img,(width, height), interpolation = cv2.INTER_CUBIC)
    rows,cols,ch = img.shape
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    segments = []
    interval = 15
    rows = 20
    for i in xrange(rows):
        row = height - i * interval
        result = get_white_segments_from_row(img, row, min_length = 10)
        for segment in result:
            cv2.line(img,(segment[0],row),(segment[1], row),(0,0,255),5)
        segments.append(result)

    roots = link_segments(segments)
    for root in roots:
        print root.segment, root.graph_size

    converge = get_converge(roots)
    if converge != None: converge = converge.height * interval
    split = get_split(roots)
    if split != None: split = split.height * interval
    print "Converge: ", converge
    print "Split: ", split

    plt.imshow(img, cmap = 'gray', interpolation = 'bicubic')
    plt.xticks([]), plt.yticks([])  # to hide tick values on X and Y axis
    plt.show()

def test(): pass

if __name__ == '__main__':
    test()
