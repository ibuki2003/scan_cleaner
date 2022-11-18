import iso_papers

def get_size_in_dots(size, dpi):
    if size in iso_papers.papers:
        return tuple(
            int(round(x * dpi / 25.4))
            for x in iso_papers.papers[size]
        )
    elif 'x' in size:
        return tuple(
            int(round(float(x) * dpi / 25.4))
            for x in size.split('x')
        )
    else:
        raise ValueError('Invalid paper size')

