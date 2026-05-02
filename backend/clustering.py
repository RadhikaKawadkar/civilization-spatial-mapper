"""
DBSCAN clustering built on top of the KD-Tree range search.

The KD-Tree's neighbors_within(lat, lon, eps) call IS the epsilon-neighborhood
query that DBSCAN requires — no external library needed.

Algorithm:
  For each unvisited point P:
    N = kdtree.neighbors_within(P.lat, P.lon, eps)
    if |N| < min_pts  → mark P as noise (-1)
    else              → expand cluster from P using N
"""

from models import Civilization, ClusterResult

NOISE = -1


def dbscan(
    civs: list[Civilization],
    kdtree,
    eps: float,
    min_pts: int,
) -> list[ClusterResult]:
    """
    Returns a ClusterResult for every civilization.
    cluster_id == -1 means noise / outlier.
    """
    n = len(civs)
    labels = [None] * n          # None = unvisited
    civ_index = {id(c): i for i, c in enumerate(civs)}

    cluster_id = 0

    for i, civ in enumerate(civs):
        if labels[i] is not None:
            continue  # already visited

        neighbors = kdtree.neighbors_within(civ.latitude, civ.longitude, eps)

        if len(neighbors) < min_pts:
            labels[i] = NOISE
            continue

        # Start a new cluster
        labels[i] = cluster_id
        seed_set = list(neighbors)

        j = 0
        while j < len(seed_set):
            q = seed_set[j]
            q_idx = civ_index.get(id(q))

            if q_idx is None:
                j += 1
                continue

            if labels[q_idx] == NOISE:
                labels[q_idx] = cluster_id  # border point

            if labels[q_idx] is not None:
                j += 1
                continue

            labels[q_idx] = cluster_id
            q_neighbors = kdtree.neighbors_within(q.latitude, q.longitude, eps)

            if len(q_neighbors) >= min_pts:
                # Expand: add new unvisited neighbors to seed set
                for nb in q_neighbors:
                    nb_idx = civ_index.get(id(nb))
                    if nb_idx is not None and labels[nb_idx] is None:
                        seed_set.append(nb)

            j += 1

        cluster_id += 1

    # Any still-None points are isolated — mark as noise
    results = []
    for i, civ in enumerate(civs):
        results.append(ClusterResult(civ, labels[i] if labels[i] is not None else NOISE))

    return results
