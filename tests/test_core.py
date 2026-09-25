import copy
import json
import math
import struct
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from fan_agent.domain import diagnose_log, preflight, validate_case
from fan_agent.geometry import inspect_stl
from fan_agent.reference import cmm_to_cfm, reference, shaft_power
from fan_agent.server import make_server
from fan_agent.store import Store
from fan_agent.analytics import plane_metrics, load_metrics


def valid_input():
    return {"name": "Test design", "rpm": 280, "diameter_mm": 1200,
            "room_x_m": 4, "room_y_m": 4, "room_z_m": 3,
            "rotor_height_m": 2.5, "sampling_height_m": 1.2, "direction": "cw"}


def tetrahedron():
    a,b,c,d=(0.,0.,0.),(100.,0.,0.),(0.,100.,0.),(0.,0.,100.)
    return [(a,c,b),(a,b,d),(a,d,c),(b,c,d)]


def binary_stl(triangles):
    return b"test".ljust(80,b" ")+struct.pack("<I",len(triangles))+b"".join(
        struct.pack("<12fH",0,0,0,*(coordinate for vertex in triangle for coordinate in vertex),0)
        for triangle in triangles)


def ascii_stl(triangles):
    facets=[]
    for triangle in triangles:
        facets.append("facet normal 0 0 1\n outer loop\n" +
                      "\n".join("vertex " + " ".join(map(str, vertex)) for vertex in triangle) +
                      "\nendloop\nendfacet")
    return ("solid test\n"+"\n".join(facets)+"\nendsolid test\n").encode()


class InputTests(unittest.TestCase):
    def test_units_and_rotation(self):
        value=validate_case(valid_input())
        self.assertAlmostEqual(value["angular_speed_rad_s"],29.32153143,places=6)
        self.assertAlmostEqual(value["tip_speed_ms"],17.59291886,places=6)

    def test_missing_input(self):
        raw=valid_input();del raw["room_x_m"]
        with self.assertRaises(ValueError):validate_case(raw)

    def test_invalid_and_nonfinite_numbers(self):
        for number in (-1,0,float("nan"),float("inf"),True,"not a speed"):
            with self.subTest(number=number):
                raw=valid_input();raw["rpm"]=number
                with self.assertRaises(ValueError):validate_case(raw)

    def test_conflicting_room_and_fan(self):
        raw=valid_input();raw["diameter_mm"]=5000
        with self.assertRaisesRegex(ValueError,"footprint"):validate_case(raw)

    def test_height_at_ceiling(self):
        raw=valid_input();raw["rotor_height_m"]=3
        with self.assertRaisesRegex(ValueError,"ceiling"):validate_case(raw)

    def test_sampling_above_rotor(self):
        raw=valid_input();raw["sampling_height_m"]=2.6
        with self.assertRaisesRegex(ValueError,"Sampling"):validate_case(raw)

    def test_unapproved_physics_cannot_be_injected(self):
        raw=valid_input();raw["solver"]="pimpleFoam"
        with self.assertRaisesRegex(ValueError,"Unsupported"):validate_case(raw)

    def test_all_basic_checks_cannot_unlock_unqualified_case(self):
        p=validate_case(valid_input())
        checks=preflight(p,{"surface_preflight_pass":True})
        self.assertFalse(checks["can_run"])
        self.assertEqual(checks["status"],"blocked")
        self.assertEqual(next(c for c in checks["checks"] if c["id"]=="recipe")["status"],"blocked")

    def test_reference_is_not_reconstructed_from_samples(self):
        ref=reference()
        self.assertEqual(ref["kind"],"company_reference")
        self.assertEqual(len(ref["samples"]),12)
        self.assertEqual(ref["samples"][-1]["position_mm"],920)
        self.assertEqual(ref["air_delivery_cmm"],232.65)
        self.assertAlmostEqual(cmm_to_cfm(1),35.31466672,places=6)
        self.assertAlmostEqual(shaft_power(.76,280),22.28436389,places=6)

    def test_failure_does_not_recommend_blade_change(self):
        for text in ("negative cell volume", "Courant max: 100 fatal error", "FOAM FATAL ERROR:", "End"):
            self.assertIsNone(diagnose_log(text)["design_change"])
        self.assertEqual(diagnose_log("End")["category"],"unclassified")


class AnalyticsTests(unittest.TestCase):
    def test_recirculation_is_reported_separately(self):
        result=plane_metrics([{"area_m2":2,"velocity_ms":[0,0,-1]},
                              {"area_m2":1,"velocity_ms":[0,0,2]}])
        self.assertEqual(result["downward_flow_cmm"],120)
        self.assertEqual(result["reverse_flow_cmm"],120)
        self.assertEqual(result["net_downward_flow_cmm"],0)
        self.assertAlmostEqual(result["mean_air_speed_ms"],4/3)
        self.assertAlmostEqual(result["downward_coverage_fraction"],2/3)

    def test_speed_magnitude_includes_horizontal_motion(self):
        result=plane_metrics([{"area_m2":1,"velocity_ms":[3,4,0]}])
        self.assertEqual(result["mean_air_speed_ms"],5)
        self.assertEqual(result["downward_flow_cmm"],0)

    def test_invalid_samples_cannot_produce_plausible_metrics(self):
        for samples in ([],[{"area_m2":0,"velocity_ms":[0,0,1]}],
                        [{"area_m2":1,"velocity_ms":[0,0,math.nan]}]):
            with self.assertRaises(ValueError):plane_metrics(samples)

    def test_torque_projection_and_power(self):
        result=load_metrics([5,3,-.76],[0,0,2],280)
        self.assertEqual(result["axis_torque_nm"],-.76)
        self.assertAlmostEqual(result["aerodynamic_shaft_power_w"],22.28436389,places=6)
        self.assertIsNone(result["electrical_input_power_w"])
        with self.assertRaises(ValueError):load_metrics([1,2,3],[0,0,0],280)


class GeometryTests(unittest.TestCase):
    def test_closed_binary_stl_and_unit_scaling(self):
        report=inspect_stl(binary_stl(tetrahedron()),"mm")
        self.assertTrue(report["surface_preflight_pass"])
        self.assertEqual(report["extent_m"],[.1,.1,.1])
        self.assertEqual(report["triangle_count"],4)

    def test_ascii_stl(self):
        report=inspect_stl(ascii_stl(tetrahedron()),"m")
        self.assertTrue(report["surface_preflight_pass"])
        self.assertEqual(report["extent_m"],[100.,100.,100.])

    def test_open_surface(self):
        report=inspect_stl(binary_stl(tetrahedron()[:1]),"mm")
        self.assertFalse(report["surface_preflight_pass"])
        self.assertEqual(report["boundary_edges"],3)

    def test_nonmanifold_surface(self):
        triangles=tetrahedron();triangles.append(triangles[0])
        report=inspect_stl(binary_stl(triangles),"mm")
        self.assertFalse(report["surface_preflight_pass"])
        self.assertEqual(report["nonmanifold_edges"],3)

    def test_degenerate(self):
        report=inspect_stl(binary_stl([((0,0,0),(0,0,0),(1,1,1))]),"mm")
        self.assertEqual(report["degenerate_triangles"],1)
        self.assertFalse(report["surface_preflight_pass"])

    def test_truncated_binary(self):
        with self.assertRaises(ValueError):inspect_stl(binary_stl(tetrahedron())[:-1],"mm")

    def test_nonfinite(self):
        with self.assertRaisesRegex(ValueError,"non-finite"):
            inspect_stl(binary_stl([((math.nan,0,0),(1,0,0),(0,1,0))]),"mm")

    def test_missing_units(self):
        with self.assertRaises(ValueError):inspect_stl(binary_stl(tetrahedron()),"")

    def test_arbitrary_text_not_geometry(self):
        with self.assertRaises(ValueError):inspect_stl(b"hello this is not an STL","m")


class PersistenceTests(unittest.TestCase):
    def test_cases_are_immutable_unique_and_do_not_have_results(self):
        with tempfile.TemporaryDirectory() as temp:
            store=Store(temp)
            geometry=store.upload(binary_stl(tetrahedron()),"mm")
            raw=valid_input();raw["geometry_id"]=geometry["id"]
            first=store.create(raw);raw["rpm"]=300;second=store.create(raw)
            self.assertNotEqual(first["id"],second["id"])
            self.assertEqual(store.read("cases",first["id"])["parameters"]["rpm"],280)
            self.assertIsNone(first["execution"]["results"])
            self.assertEqual(len(Store(temp).list_cases()),2)
            self.assertEqual(first["geometry"]["sha256"],geometry["sha256"])

    def test_geometry_identifier_cannot_escape_storage(self):
        with tempfile.TemporaryDirectory() as temp:
            raw=valid_input();raw["geometry_id"]="../../README.md"
            with self.assertRaises(ValueError):Store(temp).create(raw)


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.server=make_server(0,self.temp.name)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.base=f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.temp.cleanup()

    def request(self,path,data=None,headers=None):
        request=Request(self.base+path,data=data,headers=headers or {})
        return urlopen(request,timeout=5)

    def test_static_and_reference_api(self):
        with self.request("/") as response:
            self.assertIn(b"Fan-Agent",response.read())
            self.assertIn("frame-ancestors 'none'",response.headers["Content-Security-Policy"])
        with self.request("/api/reference") as response:
            self.assertEqual(json.load(response)["rpm"],280)

    def test_create_and_reload(self):
        with self.request("/api/cases",json.dumps(valid_input()).encode(),{"Content-Type":"application/json"}) as response:
            self.assertEqual(response.status,201);record=json.load(response)
        with self.request("/api/cases/"+record["id"]) as response:
            self.assertFalse(json.load(response)["preflight"]["can_run"])

    def test_cross_origin_write_rejected(self):
        with self.assertRaises(HTTPError) as error:
            self.request("/api/cases",b"{}",{"Origin":"https://external.example","Content-Type":"application/json"})
        self.assertEqual(error.exception.code,403)

    def test_no_solver_endpoint(self):
        with self.assertRaises(HTTPError) as error:
            self.request("/api/run",b"{}",{"Content-Type":"application/json"})
        self.assertEqual(error.exception.code,404)

    def test_bad_json_rejected(self):
        with self.assertRaises(HTTPError) as error:
            self.request("/api/cases",b"{",{"Content-Type":"application/json"})
        self.assertEqual(error.exception.code,400)

    def test_stl_upload(self):
        with self.request("/api/geometry?units=mm",binary_stl(tetrahedron()),{"Content-Type":"application/octet-stream"}) as response:
            self.assertTrue(json.load(response)["surface_preflight_pass"])


if __name__ == "__main__":
    unittest.main()
