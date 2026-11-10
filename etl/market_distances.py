import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import get_context
from time import perf_counter

import numpy as np
from scipy.sparse.csgraph import dijkstra

_STATE = None


def initialize(graph, city_nodes, point_nodes):
    global _STATE
    _STATE = (graph, city_nodes, point_nodes)


def source_distances(index):
    graph, cities, points = _STATE
    distances = dijkstra(graph, directed=True, indices=int(cities[index]))
    return index, distances[points].astype(np.float32), distances[cities]


def market_distances(graph, city_nodes, point_nodes, workers=None):
    global _STATE
    count = len(city_nodes)
    points = np.empty((count, len(point_nodes)), dtype=np.float32)
    cities = np.empty((count, count), dtype=np.float64)
    workers = int(os.environ.get('ACCESS_WORKERS', '1')) if workers is None else workers
    if not 1 <= workers <= 4:
        raise ValueError('ACCESS_WORKERS must be between 1 and 4')
    started = perf_counter()
    if workers == 1:
        initialize(graph, city_nodes, point_nodes)
        results = map(source_distances, range(count))
        for completed, (index, point_times, city_times) in enumerate(results, 1):
            points[index], cities[index] = point_times, city_times
            if completed % 8 == 0 or completed == count:
                print(f'markets={completed}/{count} seconds={perf_counter() - started:.1f}', flush=True)
    else:
        with ProcessPoolExecutor(max_workers=workers, mp_context=get_context('fork'),
                                 initializer=initialize, initargs=(graph, city_nodes, point_nodes)) as pool:
            tasks = [pool.submit(source_distances, index) for index in range(count)]
            for completed, task in enumerate(as_completed(tasks), 1):
                index, point_times, city_times = task.result()
                points[index], cities[index] = point_times, city_times
                if completed % 8 == 0 or completed == count:
                    print(f'markets={completed}/{count} seconds={perf_counter() - started:.1f}', flush=True)
    _STATE = None
    return points, cities
