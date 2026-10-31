"""Pure geometry regression checks for the v3 PCB panel."""
import math
import unittest
from nova_nexus.chrome_v3 import routes

class TrackTests(unittest.TestCase):
    def test_track_segments_are_horizontal_or_45_degrees(self):
        for pts in routes(520,240):
            for (x1,y1),(x2,y2) in zip(pts,pts[1:]):
                dx=abs(x2-x1); dy=abs(y2-y1)
                self.assertTrue(dy==0 or dx==dy, (dx,dy))
    def test_traces_are_within_chassis(self):
        for pts in routes(520,240):
            self.assertTrue(all(15<x<505 and 15<y<225 for x,y in pts))
    def test_route_count(self):
        self.assertEqual(len(routes(520,240)), 12)
