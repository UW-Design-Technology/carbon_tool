__author__ = ["Tomas Mendez Echenagucia"]
__copyright__ = "University of Washington 2023"
__license__ = "MIT License"
__email__ = "tmendeze@uw.edu"
__version__ = "0.1.0"


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

    @classmethod
    def from_gh(self, 
                breps,
                znames,
                is_roof_adiabatic,
                is_floor_adiabatic,
                wwrs,
                shades,
                automated_shades,
                glazing_u,
                shgc,
                custom_shades,
                cladding,
                exterior_insulation_material,
                exterior_insulation_thickness,
                interior_insulation_material,
                exterior_wall_framing,
                interior_finish,
                weather_file,
                out_path,
                run_model):

        b = Building()
        b.znames = znames

        for i, zname in enumerate(znames):
            b.zone_breps[zname] = breps[i]

        b.is_roof_adiabatic             = is_roof_adiabatic        
        b.is_floor_adiabatic            = is_floor_adiabatic            
        b.wwrs                          = wwrs
        b.shades                        = shades            
        b.automated_shades              = automated_shades              
        b.glazing_u                     = glazing_u                
        b.shgc                          = shgc                
        b.custom_shades                 = custom_shades                
        b.cladding                      = cladding                
        b.exterior_insulation_material  = exterior_insulation_material                
        b.exterior_insulation_thickness = exterior_insulation_thickness                
        b.interior_insulation_material  = interior_insulation_material                    
        b.exterior_wall_framing         = exterior_wall_framing                
        b.interior_finish               = interior_finish                
        b.weather_file                  = weather_file                
        b.out_path                      = out_path                
        b.run_model                     = run_model                
        
        return b


if __name__ == '__main__':
    for i in range(50): print('')