from utils import init, info, warn, term2

def get_grey(pic, sample_rows = 5, col_step = 5, rank = 10):
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

def get_white_segments_from_bot(pic, sample_rows = 5, buckets = 50):
    # Get the white segments from the bottom few rows of a black/white picture
    # @params
    # sample_rows: (int) # of concequtive bottom rows to sample
    # buckets: (int) the resolution of sampling
    height = len(pic)
    width = len(pic[0])
    sample = pic[height - sample_rows:]
    bucket_size = (width - 1) / buckets + 1
    histogram = get_histogram(sample, buckets)
    thereshold = get_thereshold(histogram)
    assert len(histogram) = buckets
    # Find the starts and ends for the white segments
    black_flag = True   # We start from black region
    result = []
    start, end = 0, 0
    for i in range(buckets):
        value = histogram[i]
        if value > thereshold:
        # We are seeing a white region
            if black_flag:
                black_flag = False
                start = i * bucket_size
        else:
        # We are seeing a black region
            if !black_flag:
                black_flag = True
                end = i * bucket_size
                result.append((start, end))
    if start > end:
        # We need to add the last segment
        result.append((start, width))
    assert result != []
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
    if type(A[0]) != list: A = [A]
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

def get_thereshold(l, rank):
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



