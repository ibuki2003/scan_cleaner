import multiprocessing

# HACK: to use lambda
_func = None


def worker_init(func):
    global _func
    _func = func


def worker(x):
    if _func is None:
        raise Exception('worker_init is not called')
    return _func(x)


def xmap(func, iterable, processes=None):
    with multiprocessing.Pool(processes, initializer=worker_init, initargs=(func,)) as p:
        return p.map(worker, iterable)
