from collections import Counter
import unittest
from fan_agent.tetra import FACES, signed_volume, subdivide_boundary_tets


def external_faces(elements):
    counts = Counter(tuple(sorted(t[i] for i in f)) for t in elements.values() for f in FACES)
    return {f for f,count in counts.items() if count==1}, counts


class TetraTests(unittest.TestCase):
    def test_preserves_volume_and_boundary_and_adds_neighbours(self):
        nodes={1:(0,0,0),2:(1,0,0),3:(0,1,0),4:(0,0,1),5:(0,0,-1)}
        elements={1:[1,2,3,4],2:[1,3,2,5]}
        new_nodes,new_elements,count=subdivide_boundary_tets(nodes,elements)
        self.assertEqual(count,2)
        self.assertEqual(len(new_elements),8)
        self.assertEqual(external_faces(elements)[0],external_faces(new_elements)[0])
        self.assertAlmostEqual(sum(signed_volume(t,new_nodes) for t in new_elements.values()),1/3)
        faces=external_faces(new_elements)[1]
        for t in new_elements.values():
            self.assertGreater(signed_volume(t,new_nodes),0)
            self.assertLessEqual(sum(faces[tuple(sorted(t[i] for i in f))]==1 for f in FACES),1)
        self.assertEqual(len(nodes),5)

    def test_rejects_degenerate_volume(self):
        with self.assertRaises(ValueError):
            subdivide_boundary_tets({1:(0,0,0),2:(1,0,0),3:(0,1,0),4:(1,1,0)},{1:[1,2,3,4]})
