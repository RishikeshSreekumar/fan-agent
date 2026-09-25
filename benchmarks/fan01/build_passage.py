"""Build audited inner passage; this excludes test chambers and stationary wake hardware."""
from pathlib import Path
import gmsh,json,math
ROOT=Path(__file__).resolve().parent
gmsh.initialize();gmsh.option.setNumber('General.Terminal',0)
try:
 occ=gmsh.model.occ
 pts=[occ.addPoint(x,y,0) for x,y in [(-.05,0),(-.05,.3),(0,.25),(.196,.25),(.324,.275),(.324,0)]]
 center=occ.addPoint(0,.3,0)
 edges=[occ.addLine(pts[0],pts[1]),occ.addCircleArc(pts[1],center,pts[2]),occ.addLine(pts[2],pts[3]),occ.addLine(pts[3],pts[4]),occ.addLine(pts[4],pts[5]),occ.addLine(pts[5],pts[0])]
 section=occ.addPlaneSurface([occ.addCurveLoop(edges)])
 swept=occ.revolve([(2,section)],0,0,0,1,0,0,2*math.pi)
 occ.synchronize();volumes=gmsh.model.getEntities(3)
 if len(volumes)!=1:raise ValueError('Expected one passage volume.')
 passage=volumes[0];full_volume=occ.getMass(*passage)
 expected=math.pi*(.3**2*.05+(2/3)*.05**3-2*.3*math.pi*.05**2/4+.196*.25**2+.128*(.25**2+.25*.275+.275**2)/3)
 if not math.isclose(full_volume,expected,rel_tol=1e-8):raise ValueError('Passage volume check failed.')
 gmsh.write(str(ROOT/'passage-metres.brep'))
 rotor=occ.importShapes(str(ROOT/'rotor-metres.brep'));occ.synchronize()
 solids=[item for item in rotor if item[0]==3]
 if len(solids)!=1:raise ValueError('Expected one rotor solid.')
 rotor_volume=occ.getMass(*solids[0])
 fluid,_=occ.cut([passage],solids);occ.synchronize()
 fluid=[item for item in fluid if item[0]==3]
 fluid_volume=sum(occ.getMass(*item) for item in fluid)
 if len(fluid)!=1 or not math.isclose(fluid_volume,full_volume-rotor_volume,rel_tol=1e-5):raise ValueError('Fluid subtraction check failed.')
 gmsh.write(str(ROOT/'rotor-passage-fluid-metres.brep'))
 report={'status':'geometry_coupon_only_not_complete_validation_domain','units':'m','passage_volume_m3':full_volume,'analytical_passage_volume_m3':expected,'rotor_volume_m3':rotor_volume,'fluid_volume_m3':fluid_volume,'fluid_volumes':len(fluid),'surface_faces':len(gmsh.model.getBoundary(fluid,oriented=False)),'profile':{'nozzle_inlet_x':-.05,'nozzle_inlet_radius':.3,'nozzle_rounding_radius':.05,'straight_start_x':0,'straight_end_x':.196,'straight_radius':.25,'diffuser_end_x':.324,'diffuser_end_radius':.275},'simplifications':['Sealed nozzle/manufacturing openings and 3 mm assembly joints along the nominal inner passage, following the published simplification intent.'],'remaining':['Add inlet and outlet chambers.','Add appropriate stationary shaft/motor/strut obstruction.','Resolve LDA coordinate origin and pressure-ring locations before validation sampling.','Construct fluid volume mesh and qualify wall/tip-gap resolution.']}
 (ROOT/'passage-preparation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
finally:gmsh.finalize()
