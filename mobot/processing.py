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
        self.segment_length_sum = abs(segment[1] - segment[0])
        self.max_height = height
        self.roots = set()

    def addNext(self, other):
        self.next.add(other)
        other.prev.add(self)

        height = other.height
        length_sum = self.segment_length_sum + other.segment_length_sum
        roots = self.roots.union(other.roots)
        other.refresh_graph(height, length_sum, roots)

    def refresh_graph(self, height, length_sum, roots):
        if height > self.max_height:
            self.graph_size += height - self.max_height
            self.max_height = height
        self.roots = roots
        self.segment_length_sum = length_sum
        # for node in self.next:
        #     node.set_graph_size(size)
        # This only propagates backwards
        for node in self.prev:
            node.refresh_graph(height, length_sum, roots)

    def get_hashables(self):
        return (self.segment[0], self.segment[1], self.height)

    def __hash__(self):
        return hash(self.get_hashables())

    def __eq__(self, other):
        return (isinstance(other, SegmentNode) and 
            self.segment == other.segment and self.height == other.height)

    def __repr__(self):
        return ("(%d, %d), size %d at height %d" % 
            (self.segment[0], self.segment[1], self.graph_size, self.height))

    def is_root(self):
        return len(self.prev) == 0

class BifurcationState(object):

    STATES = ["SINGLE_LINE", "APPROACH_CONVERGE", 
        "APPROACH_DIVERGE", "ON_DIVERGE", "PASS_DIVERGE"]

    EDGE = 0.1
    THERESHOLD_TIME = 4
    THERESHOLD_HEIGHT = 5
    THERESHOLD_COUNT = 3

    def __init__(self, width, height, choices):
        self.state = STATES[0]
        self.img_width = width
        self.img_height = height
        self.time = 0
        self.edge_segments = 1
        self.converge = None
        self.diverge = None
        self.converge_count = 0
        self.diverge_count = 0

        self.bifurcation_count = 0
        self.choices = choices
        self.choice = choices[0]

    def update(self, root_node):
        if self.state != "SINGLE_LINE":
            self.time += 1
            self.converge = None
            self.converge_count = 0
        roots = root_node.roots
        # Find the number of roots on the edge of the frame
        edge_segments = 0
        edge = BifurcationState.EDGE * self.img_width
        for root in roots:
            if (root.height <= 1 or
                root.segment[0] < edge or
                root.segment[1] > self.img_width - edge):
                edge_segments += 1
        self.edge_segments = edge_segments

        # Find first diverge
        diverge = get_split(roots)
        diverge_height = None
        if diverge != None:
            diverge_height = diverge.height

        if self.state == "SINGLE_LINE":
            # Find first converge
            # We only care about converge in this state
            converge = get_converge(roots)
            if converge != None:
                if (self.converge == None or 
                    self.converge.height >= converge.height):
                    self.converge_count += 1
                    self.converge = converge
                if (self.time > BifurcationState.THERESHOLD_TIME and
                    self.converge_count >= BifurcationState.THERESHOLD_COUNT and
                    converge.height <= BifurcationState.THERESHOLD_HEIGHT):
                    self.state == "APPROACH_CONVERGE"
                    self.time = 0
                    self.diverge_count = 0
            if diverge != None:
                if (self.diverge == None or 
                    self.diverge.height >= diverge.height):
                    self.diverge_count += 1
                    self.diverge = diverge
                if (self.time > BifurcationState.THERESHOLD_TIME and
                    self.diverge_count >= BifurcationState.THERESHOLD_COUNT and
                    diverge.height <= BifurcationState.THERESHOLD_HEIGHT and
                    edge_segments == 1):
                    self.state == "ON_DIVERGE"
                    self.diverge_count = 0
                    self.time = 0
                
        elif self.state == "APPROACH_CONVERGE":
            # This state is a safety that prevents us from missing the diverge
            if diverge != None:
                if (self.diverge == None or 
                    self.diverge.height >= diverge.height):
                    self.diverge_count += 1
                    self.diverge = diverge
                if (self.time > BifurcationState.THERESHOLD_TIME or 
                    diverge.height <= BifurcationState.THERESHOLD_HEIGHT or
                    edge_segments == 1):
                    self.state == "ON_DIVERGE"
                    self.diverge_count = 0
                    self.time = 0

        elif self.state == "ON_DIVERGE":
            # We need to be ready to make the choice here
            if diverge != None:
                if (self.diverge == None or 
                    self.diverge.height >= diverge.height):
                    self.diverge_count += 1
                    self.diverge = diverge
            else:
                self.diverge_count += 1
            if (self.time > BifurcationState.THERESHOLD_TIME and 
                (diverge == None or 
                diverge.height > BifurcationState.THERESHOLD_HEIGHT) and
                self.diverge_count >= BifurcationState.THERESHOLD_COUNT):
                self.diverge = None
                self.diverge_count = 0
                self.state == "PASS_DIVERGE"
                self.time = 0

        elif self.state == "PASS_DIVERGE":
            if(self.time > BifurcationState.THERESHOLD_TIME):
                self.state = "SINGLE_LINE"
                self.time = 0
                self.bifurcation_count += 1


        return ("TIME: %d STATE: %s DIVERGE: %s COUNT: %d EDGE_SEGMENTS: %d" 
            %(self.time, self.state, 
                str(diverge_height), self.diverge_count,
                self.edge_segments))

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
    return get_threshold(sample)

def get_white_segments_from_row(pic, row,
        sample_rows = 10, buckets = 50, min_length = 0, max_gap = 0):
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
    thereshold = new_get_gray(pic, row, sample_rows = sample_rows)
    thereshold *= bucket_size * sample_rows
    # print "thereshold:", thereshold
    # print "old thereshold:", thereshold_old
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
        #warn("More than 2 white lines detected, possible error!")
        pass
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

def get_threshold(l, hi_rank = 2, lo_rank = 2):
    # Get the mid(separator) value from a list of integers
    # @params
    # l: (list<int>) the list of integers
    # rank: (int) discard the top *rank* highest/lowest entries
    rank = max(lo_rank, hi_rank)
    assert rank > 0
    if len(l) < rank:
        warn("List too short for rank!")
        rank = len(l)
    sorted_list = sorted(l)
    lo = sorted_list[lo_rank - 1]
    hi = sorted_list[len(l) - hi_rank]
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

def link_segments(all_segments, display = None, 
    interval = 0, img_height = 0, skip = False):
    # Generates a node for each segment and links them together.
    # Returns a list of "root" nodes (those that don't have a previous node)
    # @params
    # all_segments: (list<list<(int, int)>>) A list of rows of segements
    all_nodes = gen_segment_nodes(all_segments)
    roots = []
    for node in all_nodes[0]:
        node.roots.add(node)
    for height in xrange(1, len(all_nodes)):
        row_nodes = all_nodes[height]
        for segment_node in row_nodes:
            # Link the node to some overlapping node in previous row
            flag = False
            for prev_node in all_nodes[height - 1]:
                if overlap(prev_node.segment, segment_node.segment):
                    prev_node.addNext(segment_node)
                    flag = True
            # If the previous row has no connections
            # Go to the second previous row
            if skip and (not flag) and height > 1:
                for prev_node in all_nodes[height - 2]:
                    if overlap(prev_node.segment, segment_node.segment):
                        prev_node.addNext(segment_node)
                        if display != None:
                            row = img_height - (height - 1) * interval
                            cv2.line(display, (prev_node.segment[0], row),
                                (prev_node.segment[1], row), (255, 255, 255), 3)
            if segment_node.is_root(): 
                segment_node.roots.add(segment_node)
                roots.append(segment_node)
    # Segments in the first line are always roots
    roots += all_nodes[0]
    return display, roots

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
    if len(curr.prev) == 2: 
        prev_segments = list(curr.prev)
        if not has_repetition(prev_segments[0].prev, prev_segments[1].prev):
            return curr
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

def has_repetition(s1):
    for item in s1:
        if item in s2: return True
    return False

def find_split_from_node(curr):
    # Get the first segment where one line splits into two lines recursively
    # Returns a segment node (possibly None)
    # @params
    # roots: (list<SegmentNode>) A list of root nodes
    if len(curr.next) == 2: 
        next_segments = list(curr.next)
        if not has_repetition(next_segments[0].next, next_segments[1].next):
            return curr
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

def get_image_histogram(img, step = 2):
    # Get the histogram of the image
    # @params
    # img: (List<list<int>>) the image
    result = [0] * 256
    for row in img:
        for i in xrange(0, len(row), step):
            pixel = row[i]
            result[pixel] += 1
    return result

def new_get_gray(img, row, sample_rows = 10, thereshold = 20):
    # Get the prefect grey value by separating the rightmost peak in histogram
    # @params
    # row: (int) The row to sample
    # sample_rows: (int) # of consecutive bottom rows to sample
    # thereshold: (int) The most important param: when we increase bar
    # from x to x+1, if intersection with the histogram
    # decreases more than [thereshold], we get past a peak
    sample = img[row - sample_rows:row]
    histogram = get_image_histogram(sample)
    bar = 1
    index = None
    new_index = None
    while (index == None or
        index - new_index < thereshold) and bar <= max(histogram):
        index = new_index
        for i in xrange(255):
            value = histogram[255 - i]
            if value >= bar:
                new_index = 255 - i
                break
        bar += 1
    return (index + new_index) / 2

def get_good_pts(grayimg, display, sample_rows = 5,
        interval = 15, pt_count = 10,
        max_length = 0.5, max_segments = 4, skip = False, 
        choose_thin = False, debug = False):
    # Get the white segments from picture and filter bad points
    # Currently returns a list of only the most reasonable tracking point
    # @params
    # grayimg: (List<List<int>>) The image to process (gray and blurred)
    # display: (List<List<int>>) The image we want to display (not blurred)
    # sample_rows: (int) The # of adjacent rows to sample
    # for a certain row of segments
    # interval: (int) The interval between rows sampled
    # pt_count: (int) The # of rows to sample
    # max_segments: (int) The maximum number of segments a row can have
    # If one row have more segments, it is rendered invalid
    # max_length: (int) max_length * row is the maximum length a
    # valid segment can have at a certain row
    rows, cols = grayimg.shape
    # Find tracking segments
    pts = []
    segments = []
    for i in xrange(pt_count):
        # With the assumption that the mobot always turn left on turn:
        # TODO: The turning decision is to be made
        row = rows - i * interval
        result = get_white_segments_from_row(grayimg, row, 
            sample_rows = sample_rows)
        good_results = []
        if result != [] and len(result) <= max_segments:
            for seg in result:
                if seg[1] - seg[0] < max_length * row:
                    cv2.line(display, (seg[0], row),
                        (seg[1], row), (0, 0, 255), 3)
                    good_results.append(seg)
            if good_results != []: segments.append(good_results)
    # For safety
    if segments == []:
        print "Warning! No good segments detected!"
        return display, None   # Center point of image...
    # Build segment "tree" out of segments
    # Get rid of small trees
    # Return the x coord of the most reasonable point to track
    # Which is the root with the minimum height
    display, roots = link_segments(segments, display = display, 
        interval = interval, img_height = rows, skip = skip)
    largest_tree = None
    largest_size = 0
    sec_largest_size = 0
    sec_largest_tree = None
    for root in roots:
        if debug:
            print root.segment, root.graph_size, root.segment_length_sum
        if not choose_thin:
            if root.graph_size >= largest_size:
                sec_largest_size = largest_size
                sec_largest_tree = largest_tree
                largest_size = root.graph_size
                largest_tree = root
            elif root.graph_size >= sec_largest_size:
                sec_largest_size = root.graph_size
                sec_largest_tree = root
        else:
            # We also take in account the "wideness" of the segments
            weighted_size = (root.graph_size ** 2 / 
                (float)(root.segment_length_sum))
            if weighted_size >= largest_size:
                sec_largest_size = largest_size
                sec_largest_tree = largest_tree
                largest_size = weighted_size
                largest_tree = root
            elif weighted_size >= sec_largest_size:
                sec_largest_size = weighted_size
                sec_largest_tree = root
    return display, [largest_tree, sec_largest_tree]

def get_tracking_data(grayimg, display, state, sample_rows = 5,
        interval = 15, pt_count = 10,
        max_length = 0.5, max_segments = 4, skip = False, 
        choose_thin = False, debug = False, 
        split_detection = False, 
        root_height_threshold = 2, root_size_threshold = 4):
    rows, cols = grayimg.shape
    display, roots = get_good_pts(grayimg, display, sample_rows = sample_rows,
        interval = interval, pt_count = pt_count,
        max_length = max_length, max_segments = max_segments, skip = skip, 
        choose_thin = choose_thin, debug = debug)
    if roots == None:
        return display, [(cols / 2, rows)]
    else:
        point = [0,0]
        if split_detection:
            output = state.update(roots[0])
            print output
            choice = state.choice
            if state.state == "ON_DIVERGE":
                if choice.upper() == "L":
                    point[0] = roots[0].segment[0]
                    point[1] = rows - interval * roots[0].height
                else:
                    assert choice.upper() == "R"
                    point[0] = roots[0].segment[1]
                    point[1] = rows - interval * roots[0].height
            elif state.state == "PASS_DIVERGE":
                if choice.upper() == "L":
                    selected_root = roots[0]
                    if (roots[1] != None and 
                        roots[1].segment[0] < selected_root.segment[0] and
                        roots[1].height <= root_height_threshold and
                        roots[1].size >= root_size_threshold):
                        selected_root = roots[1]
                    point[0] = selected_root.segment[0]
                    point[1] = rows - interval * selected_root.height
                else:
                    assert choice.upper() == "R"
                    selected_root = roots[0]
                    if (roots[1] != None and 
                        roots[1].segment[1] > selected_root.segment[1] and
                        roots[1].height <= root_height_threshold and
                        roots[1].size >= root_size_threshold):
                        selected_root = roots[1]
                    point[0] = selected_root.segment[1]
                    point[1] = rows - interval * selected_root.height
            else:
                # Just the normal stuff
                point[0] = roots[0].center
                point[1] = rows - interval * roots[0].height
        else:
            point[0] = roots[0].center
            point[1] = rows - interval * roots[0].height
        cv2.circle(display, (point[0], point[1]), 10,(255,255,255),2)
        return display, [point]


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
    img = cv2.imread('../tests/7.jpg')
    height, width = 300, 300
    img = cv2.resize(img,(width, height), interpolation = cv2.INTER_CUBIC)
    rows,cols,ch = img.shape
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    img = cv2.GaussianBlur(img,(11,11),0)
    interval = 15
    for i in xrange(interval):
        row = height - i * interval
        result = get_white_segments_from_row(img, row)
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
    img = cv2.imread('../tests/out.jpg')
    height, width = 300, 300
    img = cv2.resize(img,(width, height), interpolation = cv2.INTER_CUBIC)
    rows,cols,ch = img.shape
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    img = cv2.bitwise_not(img)
    segments = []
    interval = 15
    rows = 20
    for i in xrange(rows):
        row = height - i * interval
        result = get_white_segments_from_row(img, row, sample_rows = 5)
        for segment in result:
            cv2.line(img,(segment[0],row), (segment[1], row),(0,0,255),5)
        segments.append(result)

    temp, roots = link_segments(segments)
    for root in roots:
        print root.segment, root.graph_size

    converge = get_converge(roots)
    print "Converge = ", converge
    if converge != None: converge = converge.height * interval
    split = get_split(roots)
    print "Split = ", split
    for node in split.roots: 
        print node
    if split != None: split = split.height * interval
    print "Converge: ", converge
    print "Split: ", split

    plt.imshow(img, cmap = 'gray', interpolation = 'bicubic')
    plt.xticks([]), plt.yticks([])  # to hide tick values on X and Y axis
    plt.show()

def test_new_get_gray():
    img = cv2.imread('../tests/1.jpg')
    height, width = 300, 300
    img = cv2.resize(img,(width, height), interpolation = cv2.INTER_CUBIC)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(img,(11,11),0)
    rows,cols = img.shape
   #plt.subplot(1,4,1),plt.hist(img)
    #n, bins, patches = plt.hist(blur, 20)
    #print n[0]
    #print bins
    #print patches
    #plt.subplot(1,4,2),plt.hist(blur, 20)
    plt.subplot(1,4,3),plt.imshow(blur, cmap = 'gray')
    row = 200
    sample = blur[row - 10:row]
    thereshold = new_get_gray(blur, row)
    print thereshold
    ret,thresh1 = cv2.threshold(blur,thereshold,255,cv2.THRESH_BINARY)
    plt.subplot(1,4,4),plt.plot(get_image_histogram(sample))
    plt.subplot(1,4,1),plt.imshow(thresh1,'gray')
    plt.show()

def test_node():
    print "Testing SegmentNode..."
    s1 = SegmentNode((0,0),1)
    s2 = SegmentNode((1,1),2)
    s3 = SegmentNode((1,1),2)
    set1 = set()
    set1.add(s1)
    assert s1 in set1
    assert s2 not in set1
    set1.add(s2)
    assert s1 in set1
    assert s2 in set1
    assert s3 in set1
    print "Passed!"

def test_get_good_pts():
    img = cv2.imread('../tests/12.jpg')
    height, width = 300, 300
    img = cv2.resize(img,(width, height), interpolation = cv2.INTER_CUBIC)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    img = cv2.GaussianBlur(img,(11,11),0)
    img, pts = get_tracking_data(img, img, None, pt_count = 20, skip = True, 
        debug = True, choose_thin = True)
    print pts[0]
    plt.imshow(img, cmap = 'gray', interpolation = 'bicubic')
    plt.xticks([]), plt.yticks([])  # to hide tick values on X and Y axis
    plt.show()

def test():pass

if __name__ == '__main__':
    test()
