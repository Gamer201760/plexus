from collections import deque


def corridor_pairs(pairs: list[tuple[int, int]], source: int, target: int) -> set[tuple[int, int]]:
    neighbors: dict[int, set[int]] = {}
    for a, b in pairs:
        if a != b:
            neighbors.setdefault(a, set()).add(b)
            neighbors.setdefault(b, set()).add(a)
    if source not in neighbors or target not in neighbors or source == target:
        return set()
    discovery, low, parents = {source: 0}, {source: 0}, {source: -1}
    stack = [(source, iter(sorted(neighbors[source])))]
    edges: list[tuple[int, int]] = []
    blocks: list[set[tuple[int, int]]] = []
    while stack:
        v, iterator = stack[-1]
        w = next(iterator, None)
        if w is None:
            stack.pop()
            parent = parents[v]
            if parent >= 0:
                low[parent] = min(low[parent], low[v])
                if low[v] >= discovery[parent]:
                    block = set()
                    while edges:
                        edge = edges.pop()
                        block.add((min(edge), max(edge)))
                        if edge == (parent, v):
                            break
                    blocks.append(block)
            continue
        if w == parents[v]:
            continue
        if w not in discovery:
            parents[w] = v
            discovery[w] = low[w] = len(discovery)
            edges.append((v, w))
            stack.append((w, iter(sorted(neighbors[w]))))
        elif discovery[w] < discovery[v]:
            low[v] = min(low[v], discovery[w])
            edges.append((v, w))
    tree: dict[tuple[str, int], list[tuple[str, int]]] = {}
    for i, block in enumerate(blocks):
        bkey = ("block", i)
        for v in {n for pair in block for n in pair}:
            vkey = ("vertex", v)
            tree.setdefault(vkey, []).append(bkey)
            tree.setdefault(bkey, []).append(vkey)
    start, end = ("vertex", source), ("vertex", target)
    queue = deque([start])
    previous: dict[tuple[str, int], tuple[str, int] | None] = {start: None}
    while queue:
        vkey = queue.popleft()
        for neighbor in tree.get(vkey, []):
            if neighbor not in previous:
                previous[neighbor] = vkey
                queue.append(neighbor)
    if end not in previous:
        return set()
    result: set[tuple[int, int]] = set()
    cursor: tuple[str, int] | None = end
    while cursor is not None:
        if cursor[0] == "block":
            result.update(blocks[cursor[1]])
        cursor = previous[cursor]
    return result
