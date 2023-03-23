__author__ = ["Tomas Mendez Echenagucia"]
__copyright__ = "University of Washington 2023"
__license__ = "MIT License"
__email__ = "tmendeze@uw.edu"
__version__ = "0.1.0"

import carbon_tool

from carbon_tool.datastructures import structure
reload(structure)
from carbon_tool.datastructures.structure import Structure

from carbon_tool.datastructures import envelope
reload(envelope)
from carbon_tool.datastructures.envelope import Envelope


try:
    import rhinoscriptsyntax as rs
except:
    pass


class Building(object):

    def __init__(self):
        self.__name__                           = 'Studio2023Building'
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
        self.structure                          = None
        self.envelope                           = None
        self.glazing_type                       = None
        self.height                             = None

    @classmethod
    def from_gh(cls, 
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

        b.is_roof_adiabatic             = is_roof_adiabatic        
        b.is_floor_adiabatic            = is_floor_adiabatic            
        b.wwrs                          = wwrs
        b.shades                        = shades            
        b.automated_shades              = automated_shades              
        b.glazing_u                     = glazing_type                
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

        b.compute_surfaces()
        b.compute_height()

        b.structure = Structure.from_geometry(b)
        b.envelope = Envelope.from_geometry(b)
        return b

    def compute_surfaces(self):

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
            for srf in srfs:
                n = rs.VectorUnitize(rs.SurfaceNormal(srf, (0, 0)))
                # angle = rs.VectorAngle(n, [0, 1, 0])
                angle = rs.Angle2([[0,0,0], [0,1,0]], [[0,0,0], n])[0]
                if n[2] == 0:
                    if angle < 135 and angle > 45 and n[0] > 0:
                        self.zone_surfaces[zk]['east'].append(srf)
                    elif angle < 225 and angle > 135:
                        self.zone_surfaces[zk]['south'].append(srf)
                    elif angle < 135 and angle > 45 and n[0] < 0:
                        self.zone_surfaces[zk]['west'].append(srf)
                    else:
                        self.zone_surfaces[zk]['north'].append(srf)
                        
                    self.zone_surfaces[zk]['walls'].append(srf)
                elif n[2]< 0:
                    self.zone_surfaces[zk]['floor'] = srf
                else:
                    self.zone_surfaces[zk]['roof'] = srf

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

if __name__ == '__main__':
    for i in range(50): print('')
    #TODO: compute adiabatic WALLS automatically and exclude from env embodied
    #TODO: Glazing U values are hard coded and non-sensical
    #TODO: Shading embodied is missing, needs to include automated shading too