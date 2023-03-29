__author__ = ["Tomas Mendez Echenagucia"]
__copyright__ = "University of Washington 2023"
__license__ = "MIT License"
__email__ = "tmendeze@uw.edu"
__version__ = "0.1.0"

import os
import carbon_tool
import pickle

from carbon_tool.datastructures import structure
# reload(structure)
from carbon_tool.datastructures.structure import Structure

from carbon_tool.datastructures import envelope
# reload(envelope)
from carbon_tool.datastructures.envelope import Envelope

from carbon_tool.functions import geometric_key

try:
    import rhinoscriptsyntax as rs
except:
    pass


class Building(object):

    def __init__(self):
        self.__name__                           = 'Studio2023Building'
        self.name                               = None
        self.zone_breps                         = {}
        self.znames                             = []
        self.is_roof_adiabatic                  = False
        self.is_floor_adiabatic                 = False
        self.wwrs                               = {}
        self.shades                             = {'horizontal':{}, 'vertical': {}}
        self.automated_shades                   = {}
        self.glazing_u                          = None
        self.shgc                               = {}
        self.custom_shades                      = {}
        self.cladding                           = None
        self.exterior_insulation_material       = None
        self.exterior_insulation_thickness      = None
        self.interior_insulation_material       = None
        self.exterior_wall_framing              = None
        self.interior_finish                    = None
        self.weather_file                       = None
        self.out_path                           = None
        self.run_model                          = False
        self.city                               = None
        self.building_type                      = None
        self.num_floors_above                   = None
        self.composite_slab                     = None
        self.columns                            = None
        self.beams_x                            = None
        self.beams_y                            = None
        self.cores                              = None
        self.zone_surfaces                      = {}
        self.zone_faces                         = {}
        self.structure                          = None
        self.envelope                           = None
        self.glazing_type                       = None
        self.height                             = None

    @classmethod
    def from_gh(cls,
                name,
                breps,
                znames,
                is_roof_adiabatic,
                is_floor_adiabatic,
                wwrs,
                shades,
                automated_shades,
                glazing_type,
                shgc,
                custom_shades,
                cladding,
                exterior_insulation_material,
                exterior_insulation_thickness,
                interior_insulation_material,
                exterior_wall_framing,
                interior_finish,
                city,
                out_path,
                run_model,
                building_type,
                num_floors_above,
                composite_slab,
                columns,
                beams_x,
                beams_y,
                cores):

        b = cls()
        b.znames = znames

        for i, zname in enumerate(znames):
            b.zone_breps[zname] = breps[i]

        weather_dict = {'Seattle': carbon_tool.SEATTLE,
                        'Los Angeles': carbon_tool.LOS_ANGELES,
                        'Milwaukee': carbon_tool.MILWAUKEE,
                        'San Antonio': carbon_tool.SAN_ANTONIO,
                        'New York': carbon_tool.NEW_YORK,
                        'Atlanta': carbon_tool.ATLANTA,
                        }

        glazing_dict = {'double': .35, 'triple': .45}  #### This must be chanced to good numbers


        if not out_path:
            out_path = carbon_tool.TEMP

        b.name                          = name
        b.is_roof_adiabatic             = is_roof_adiabatic        
        b.is_floor_adiabatic            = is_floor_adiabatic            
        b.wwrs                          = wwrs
        b.shades                        = shades            
        b.automated_shades              = automated_shades              
        b.glazing_type                  = glazing_type                
        b.shgc                          = shgc                
        b.custom_shades                 = custom_shades                
        b.cladding                      = cladding                
        b.exterior_insulation_material  = exterior_insulation_material                
        b.exterior_insulation_thickness = exterior_insulation_thickness                
        b.interior_insulation_material  = interior_insulation_material                    
        b.exterior_wall_framing         = exterior_wall_framing                
        b.interior_finish               = interior_finish                
        b.weather_file                  = weather_dict[city]                
        b.city                          = city
        b.out_path                      = out_path                
        b.run_model                     = run_model                
        b.building_type                 = building_type                       
        b.num_floors_above              = num_floors_above                    
        b.composite_slab                = composite_slab                          
        b.columns                       = columns                             
        b.beams_x                       = beams_x                                 
        b.beams_y                       = beams_y                                 
        b.cores                         = cores                                
        b.glazing_u                     = glazing_dict[glazing_type]
        b.results                       = None

        b.compute_surfaces()
        b.compute_height()

        b.structure = Structure.from_geometry(b)
        b.envelope = Envelope.from_geometry(b)
        return b

    def compute_surfaces(self):
        
        cpt_dict = {}
        for zk in self.zone_breps:
            brep = self.zone_breps[zk]
            srfs = rs.ExplodePolysurfaces(brep, delete_input=False)
            for srf in srfs:
                cpt = rs.SurfaceAreaCentroid(srf)[0]
                gk = geometric_key(cpt)
                if gk in cpt_dict:
                    cpt_dict[gk] = False
                else:
                    cpt_dict[gk] = True

        for zk in self.zone_breps:
            brep = self.zone_breps[zk]
            srfs = rs.ExplodePolysurfaces(brep, delete_input=False)
            self.zone_surfaces[zk] = {'north': [],
                                      'east': [],
                                      'south': [],
                                      'west': [],
                                      'walls': [],
                                      'roof': None,
                                      'floor': None}

            self.zone_faces[zk]    = {'north': [],
                                      'east': [],
                                      'south': [],
                                      'west': [],
                                      'walls': [],
                                      'roof': None,
                                      'floor': None}

            for srf in srfs:
                cpt = rs.SurfaceAreaCentroid(srf)[0]
                gk = geometric_key(cpt)
                if cpt_dict[gk]:
                    n = rs.VectorUnitize(rs.SurfaceNormal(srf, (0, 0)))
                    # angle = rs.VectorAngle(n, [0, 1, 0])
                    angle = rs.Angle2([[0,0,0], [0,1,0]], [[0,0,0], n])[0]
                    if n[2] == 0:
                        if angle < 135 and angle > 45 and n[0] > 0:
                            self.zone_surfaces[zk]['east'].append(srf)
                            self.zone_faces[zk]['east'].append(rs.SurfacePoints(srf))
                        elif angle < 225 and angle > 135:
                            self.zone_surfaces[zk]['south'].append(srf)
                            self.zone_faces[zk]['south'].append(rs.SurfacePoints(srf))
                        elif angle < 135 and angle > 45 and n[0] < 0:
                            self.zone_surfaces[zk]['west'].append(srf)
                            self.zone_faces[zk]['west'].append(rs.SurfacePoints(srf))
                        else:
                            self.zone_surfaces[zk]['north'].append(srf)
                            self.zone_faces[zk]['north'].append(rs.SurfacePoints(srf))
                            
                        self.zone_surfaces[zk]['walls'].append(srf)
                        self.zone_faces[zk]['walls'].append(rs.SurfacePoints(srf))
                    elif n[2]< 0:
                        self.zone_surfaces[zk]['floor'] = srf
                        self.zone_faces[zk]['floor'] = rs.SurfacePoints(srf)
                    else:
                        self.zone_surfaces[zk]['roof'] = srf
                        self.zone_faces[zk]['roof'] = rs.SurfacePoints(srf)

    def compute_height(self):
        zk = list(self.zone_surfaces.keys())[0]
        roof = rs.SurfacePoints(self.zone_surfaces[zk]['roof'])
        floor = rs.SurfacePoints(self.zone_surfaces[zk]['floor'])
        self.height = roof[0][2] - floor[0][2]

    @property
    def floor_area(self):
        fa = 0
        for zk in self.zone_surfaces:
            fa += rs.SurfaceArea(self.zone_surfaces[zk]['floor'])[0]
        return fa

    def compute_structure_embodied(self):
        self.structure.compute_embodied()

    def compute_envelope_embodied(self):
        self.envelope.compute_embodied()

    def draw_structure(self):
        c_th = self.structure.conc_thick 
        t_th = self.structure.timber_thick
        tot_thick = c_th + t_th
        srfs = [self.zone_surfaces[zk]['roof'] for zk in self.zone_surfaces]
        slabs = []
        for srf in srfs:
            line = rs.AddLine([0,0,0], [0,0,tot_thick])
            srf = rs.ExtrudeSurface(srf, line)
            slabs.append(srf)

        side = self.structure.col_side

        sh = self.structure.timber_thick + self.structure.conc_thick

        columns = []
        for sp, ep in self.structure.columns:
            sp_ = rs.VectorAdd(sp, [-side/2., -side/2.,0])
            b = rs.VectorAdd(sp_, [1,0,0])
            c = rs.VectorAdd(sp_, [0,1,0])
            ep_ = ep[0], ep[1], ep[2] - sh

            plane = rs.PlaneFromPoints(sp_, b, c)
            sec = rs.AddRectangle(plane, side, side)
            col = rs.AddLine(sp, ep_)
            columns.append(rs.ExtrudeCurve(sec, col))

        bw = self.structure.beam_width
        bh = self.structure.beam_height


        beams = []
        for sp, ep in self.structure.main_beams:
            x = rs.VectorCreate(ep, sp)
            z = [0,0,1]
            y = rs.VectorCrossProduct(x, z)
            y_ = rs.VectorScale(rs.VectorUnitize(y), bw / -2.)
            
            sp_ = rs.VectorAdd(sp, y_)
            sp_ = rs.VectorAdd(sp_, [0,0,-bh -sh])    
            b = rs.VectorAdd(sp_, y)
            c = rs.VectorAdd(sp_, z)
            plane = rs.PlaneFromPoints(sp_, b, c)
            sec = rs.AddRectangle(plane, bw, bh)
            beam = rs.AddLine(sp, ep)
            beams.append(rs.ExtrudeCurve(sec, beam))

        bh_ = bh *.5
        for sp, ep in self.structure.second_beams:
            x = rs.VectorCreate(ep, sp)
            z = [0,0,1]
            y = rs.VectorCrossProduct(x, z)
            y_ = rs.VectorScale(rs.VectorUnitize(y), bw / -2.)
            
            sp_ = rs.VectorAdd(sp, y_)
            sp_ = rs.VectorAdd(sp_, [0,0,-bh_ -sh])    
            b = rs.VectorAdd(sp_, y)
            c = rs.VectorAdd(sp_, z)
            plane = rs.PlaneFromPoints(sp_, b, c)
            sec = rs.AddRectangle(plane, bw, bh_)
            beam = rs.AddLine(sp, ep)
            beams.append(rs.ExtrudeCurve(sec, beam))
        cores = []
        for core in self.structure.cores:
            sp = core[0]
            ep = (core[0][0], core[0][1], core[0][2]+ self.height)
            core = rs.ExtrudeCurveStraight(rs.AddPolyline(core), sp, ep)
            cores.append(core)

        return slabs, columns, beams, cores

    def to_obj(self, output=True, path=None, name=None):

        """ Exports the Building object to an .obj file through Pickle.

        Parameters
        ----------
        output : bool
            Print terminal output.

        Returns
        -------
        None

        """

        if not path:
            path = self.out_path
        if not name:
            name = self.name
        filename = os.path.join(path, name + '.obj')

        with open(filename, 'wb') as f:
            pickle.dump(self, f, protocol=2)

        if output:
            print('***** Building saved to: {0} *****\n'.format(filename))

    @staticmethod
    def from_obj(filepath, output=True):

        """ Imports a Building object from an .obj file through Pickle.

        Parameters
        ----------
        filepath : str
            Path to load the Building .obj from.
        output : bool
            Print terminal output.

        Returns
        -------
        obj
            Imported Building object.

        """
        with open(filepath, 'rb') as f:
            building = pickle.load(f)
        if output:
            print('***** Building loaded from: {0} *****'.format(filepath))

        return building


if __name__ == '__main__':
    for i in range(50): print('')
    #TODO: Glazing U values are hard coded and non-sensical
    #TODO: Think of something better for the core embodied, it is too much
    #TODO: Test results reading with weird zone names, honeybee adds a weird thing to the zone name
    #TODO: Sanity chekcs, plot results, hourly, etc.
    #TODO: Test reproducibility, should I save all surfaces (pts) lines, etc?
    #TODO: On a related note, pickle is not working well, should I switch to json and use meshes?
    #TODO: what oher geometry needs to be saved in non GUID form?

    #TODO: (low) Wood cladding is giving negative GWP. Why?
    #TODO: (low) Display structural elements needs a check / update
    import os

    filepath = os.path.join(carbon_tool.TEMP, 'test_building_20230328163220.obj')
    b = Building.from_obj(filepath)
