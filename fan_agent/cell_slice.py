"""Exact horizontal intersection of tetrahedra, with piecewise-constant cell U."""
import math
from pathlib import Path
import re
from .analytics import plane_metrics


def tetra_polygon(points,height):
    hits=[]
    for i,a in enumerate(points):
        if a[2]==height: hits.append((a[0],a[1]))
        for b in points[i+1:]:
            if (a[2]<height<b[2]) or (b[2]<height<a[2]):
                t=(height-a[2])/(b[2]-a[2])
                hits.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))
    hits=list(dict.fromkeys(hits))
    if len(hits)<3:return [],0
    cx=sum(x for x,y in hits)/len(hits); cy=sum(y for x,y in hits)/len(hits)
    hits.sort(key=lambda p:math.atan2(p[1]-cy,p[0]-cx))
    a=hits[0]
    area=abs(math.fsum((b[0]-a[0])*(c[1]-a[1])-(c[0]-a[0])*(b[1]-a[1]) for b,c in zip(hits[1:],hits[2:])))/2
    return hits,area


def slice_case(root,time,height=1.2):
    root=Path(root); mesh=root/'constant/polyMesh'
    def body(path):
        text=re.sub(r'/\*.*?\*/|//[^\n]*','',path.read_text(),flags=re.S)
        return re.search(r'\n\s*\d+\s*\((.*)\)',text,re.S).group(1)
    points=[tuple(map(float,p.split())) for p in re.findall(r'\(([^()]*)\)',body(mesh/'points'))]
    faces=[list(map(int,p.split())) for p in re.findall(r'\d+\(([^()]*)\)',body(mesh/'faces'))]
    owners=list(map(int,body(mesh/'owner').split())); neighbours=list(map(int,body(mesh/'neighbour').split()))
    data=(root/str(time)/'U').read_text()
    match=re.search(r'internalField\s+nonuniform\s+List<vector>\s+(\d+)\s*\((.*?)\)\s*;',data,re.S)
    if not match:raise ValueError('Expected a nonuniform ASCII cell velocity field.')
    velocities=[tuple(map(float,p.split())) for p in re.findall(r'\(([^()]*)\)',match[2])]
    if len(velocities)!=int(match[1]) or not all(len(v)==3 and all(math.isfinite(x) for x in v) for v in velocities):
        raise ValueError('Invalid cell velocity field.')
    cells=[set() for _ in velocities]
    for index,face in enumerate(faces):
        cells[owners[index]].update(face)
        if index<len(neighbours):cells[neighbours[index]].update(face)
    samples=[]; polygons=[]
    for vertices,velocity in zip(cells,velocities):
        if len(vertices)!=4:raise ValueError('Exact slicer currently supports tetrahedral cells only.')
        polygon,area=tetra_polygon([points[v] for v in vertices],height)
        if area:
            samples.append({'area_m2':area,'velocity_ms':velocity})
            polygons.append((polygon,velocity))
    metrics=plane_metrics(samples)
    if not math.isclose(metrics['plane_area_m2'],16,rel_tol=1e-8):
        raise ValueError(f"Plane coverage failed: {metrics['plane_area_m2']} m2")
    metrics.update(sampling_method='Exact tetrahedral intersection / cell-constant stationary velocity',height_m=height)
    return metrics,polygons
