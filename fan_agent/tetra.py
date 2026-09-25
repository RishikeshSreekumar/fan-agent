"""Boundary-preserving tetrahedron subdivision for finite-volume connectivity."""
from collections import Counter
import math

FACES = ((0,1,2),(0,1,3),(0,2,3),(1,2,3))


def signed_volume(tet, nodes):
    a,b,c,d = [nodes[n] for n in tet]
    u,v,w = [[p[j]-a[j] for j in range(3)] for p in (b,c,d)]
    return (u[0]*(v[1]*w[2]-v[2]*w[1])-u[1]*(v[0]*w[2]-v[2]*w[0])+u[2]*(v[0]*w[1]-v[1]*w[0]))/6


def subdivide_boundary_tets(nodes, elements):
    """Return new node and element maps without modifying the inputs."""
    counts = Counter(tuple(sorted(t[i] for i in f)) for t in elements.values() for f in FACES)
    if any(count > 2 for count in counts.values()):
        raise ValueError('Nonmanifold input tetrahedra.')
    result_nodes, result_elements = dict(nodes), {}
    next_node, next_element = max(nodes)+1, max(elements)+1
    split_count = 0
    for tag,tet in elements.items():
        volume = abs(signed_volume(tet,nodes))
        if not math.isfinite(volume) or volume <= 0:
            raise ValueError('Invalid input tetrahedron volume.')
        if sum(counts[tuple(sorted(tet[i] for i in f))]==1 for f in FACES) < 2:
            result_elements[tag] = list(tet)
            continue
        result_nodes[next_node] = [sum(nodes[n][j] for n in tet)/4 for j in range(3)]
        child_volume = 0
        for f in FACES:
            child = [tet[i] for i in f]+[next_node]
            if signed_volume(child,result_nodes) < 0:
                child[0],child[1] = child[1],child[0]
            child_volume += signed_volume(child,result_nodes)
            result_elements[next_element] = child
            next_element += 1
        if not math.isclose(child_volume,volume,rel_tol=1e-10,abs_tol=1e-16):
            raise ValueError('Subdivision failed volume conservation.')
        split_count += 1
        next_node += 1
    return result_nodes,result_elements,split_count
