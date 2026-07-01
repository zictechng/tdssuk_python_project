
def get_page_range(page_obj, window=2):
    current = page_obj.number
    start = max(current - window, 1)
    end = min(current + window, page_obj.paginator.num_pages)
    return range(start, end + 1)