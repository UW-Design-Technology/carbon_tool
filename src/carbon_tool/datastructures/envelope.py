from __future__ import print_function

__author__ = ["Tomas Mendez Echenagucia"]
__copyright__ = "University of Washington 2023"
__license__ = "MIT License"
__email__ = "tmendeze@uw.edu"
__version__ = "0.1.0"

from ast import literal_eval

from carbon_tool.functions import material_reader
try:
    reload(material_reader)
except:
    pass

try:
    import rhinoscriptsyntax as rs
except:
    pass


from carbon_tool.functions import read_materials
from carbon_tool.functions import read_materials_city


TPL = """
################################################################################
Envelope datastructure: {}
################################################################################

window-to-wall ratio:   {}
window: {}
wall: {}
embodied: {}

"""



class Envelope(object):
    
    def __init__(self):
        self.orient_areas           = {'n':{}, 's':{}, 'e':{}, 'w':{}}
        self.opaque_areas           = {'n':{}, 's':{}, 'e':{}, 'w':{}}
        self.window_areas           = {'n':{}, 's':{}, 'e':{}, 'w':{}}
        self.city                   = None
        self.external_insulation    = None
        self.insulation_thickness   = None
        self.facade_cladding        = None
        self.glazing_system         = None
        self.height                 = None
        self.shade_depth_h          = {'n':{}, 's':{}, 'e':{}, 'w':{}} 
        self.shade_depth_v1         = {'n':{}, 's':{}, 'e':{}, 'w':{}} 
        self.shade_depth_v2         = {'n':{}, 's':{}, 'e':{}, 'w':{}} 
        self.wwr                    = {'n':{}, 's':{}, 'e':{}, 'w':{}} 
        self.wall_embodied          = None
        self.window_embodied        = None
        self.shading_embodied       = None
        self.int_finish             = None
        self.ewall_framing          = None
        self.interior_insul_mat     = None
        self.int_ins_thickness      = None
        self.shading                = None
        self.automated_shading      = None
        self.custom_shading         = None

    @classmethod
    def from_geometry(cls, building):
        env = cls()
        for zk in building.zone_surfaces:
            for ok in ['north', 'east', 'south', 'west']:
                if building.zone_surfaces[zk][ok]:
                    areas = [rs.SurfaceArea(srf)[0] for srf in building.zone_surfaces[zk][ok]]
                    env.orient_areas[ok[0]][zk] = sum(areas)
                    env.opaque_areas[ok[0]][zk] = env.orient_areas[ok[0]][zk] * (1 - building.wwrs[ok])
                    env.window_areas[ok[0]][zk] = env.orient_areas[ok[0]][zk] * building.wwrs[ok]

        interior_insulation_dict = {'2x4 Wood Studs': 4,
                                    '2x6 Wood Studs':6,
                                    '2x8 Wood Studs':8,
                                    '2x10 Wood Studs':10,
                                    '2x12 Wood Studs':12}

        env.external_insulation     = building.exterior_insulation_material
        env.insulation_thickness    = building.exterior_insulation_thickness
        env.facade_cladding         = building.cladding
        env.glazing_system          = building.glazing_type
        env.height                  = building.height
        env.shading                 = building.shades          
        env.automated_shading       = building.automated_shades
        env.custom_shading          = building.custom_shades
        env.wwr                     = building.wwrs
        env.city                    = building.city 
        env.int_finish              = building.interior_finish
        env.ewall_framing           = building.exterior_wall_framing
        env.interior_insul_mat      = building.interior_insulation_material
        env.int_ins_thickness       = interior_insulation_dict[building.exterior_wall_framing]
        env.height                  = building.height

        return env

    def compute_embodied(self):
        tot_opaque = 0.  # this should be in feet?
        tot_win = 0.     # this should be in feet?
        orient_win_areas = {}
        orient_areas = {}
        sides = {}
        for okey in self.opaque_areas:
            opaque_orient = 0
            win_orient = 0
            orient_areas[okey] = 0
            for zkey in self.opaque_areas[okey]:
                orient_areas[okey] += self.orient_areas[okey][zkey]
                opaque_orient += self.opaque_areas[okey][zkey]
                win_orient += self.window_areas[okey][zkey]
            sides[okey] = (opaque_orient + win_orient) / self.height
            tot_opaque += opaque_orient
            tot_win += win_orient
            orient_win_areas[okey] = win_orient

        # external insulation - - -
        ins_mat = self.external_insulation
        if ins_mat == 'None':
            ins_thick = 0.
            ins_emb_ = 0
        else:
            
            ins_thick = float(self.insulation_thickness) / 12. # currently in inches
            ins_emb_ = float(read_materials_city(ins_mat, self.city)) / 27.  # currently (kgCO2/yd3)
        ins_emb = tot_opaque * ins_thick * ins_emb_ 

        # facade cladding - - -
        fac_mat = self.facade_cladding
        fac_thick = float(read_materials(fac_mat)['thickness_in']) / 12. # currently (kgCO2/yd3)
        fac_emb_ = float(read_materials_city(fac_mat, self.city)) / 27. # currently (kgCO2/yd3)
        fac_emb = tot_opaque * fac_thick * fac_emb_ 

        # interior framing - - -
        fram_mat = self.ewall_framing
        fram_thick = float(read_materials(fram_mat)['thickness_in']) / 12. # currently (kgCO2/yd3)
        fram_emb_ = float(read_materials_city(fram_mat, self.city)) / 27. # currently (kgCO2/yd3)
        fram_emb = tot_opaque * fram_thick * fram_emb_ 

        # interior insulation - - -
        int_ins_mat = self.interior_insul_mat
        int_ins_thick = self.int_ins_thickness / 12.
        if int_ins_mat != 'None':
            int_ins_emb_ = float(read_materials_city(int_ins_mat, self.city)) / 27. # currently (kgCO2/yd3)
            int_ins_emb = tot_opaque * int_ins_thick * int_ins_emb_ 
        else:
            int_ins_emb = 0.
            int_ins_emb_ = 0.

        # interior finish - - -
        int_mat = self.int_finish
        if int_mat == 'None':
            int_thick = 0.
            int_emb_ = 0
        else:
            int_thick = float(read_materials(int_mat)['thickness_in']) / 12# currently (kgCO2/yd3)
            int_emb_ = float(read_materials_city(int_mat, self.city)) / 27 # currently (kgCO2/yd3)
        int_emb = tot_opaque * int_thick * int_emb_ 

        win_sys = self.glazing_system
        if win_sys == 'double':
            glass_mat = 'Glass Double'
        elif win_sys == 'single':
            glass_mat = 'Glass Single'
        else:
            glass_mat = 'Glass Triple'
        # win_emb_ = float(read_glazing(win_sys)['embodied_carbon_imperial']) # currently (KgCO2/ft2)
        glass_thick = float(read_materials(glass_mat)['thickness_in']) / 12# currently (kgCO2/yd3)
        win_emb_ = float(read_materials_city(glass_mat, self.city)) / 27. # currently (kgCO2/yd3)
        win_emb = tot_win * win_emb_ * glass_thick

        self.wall_embodied =  ins_emb + fac_emb + int_emb + fram_emb + int_ins_emb
        self.window_embodied = win_emb


        # shading embodied - - - - - - -
        alum_emb = float(read_materials_city('Aluminum', self.city)) / 27. # currently (kgCO2/yd3)
        total_shading_area = 0

        for srf in self.custom_shading:
            total_shading_area += rs.SurfaceArea(srf)[0]

        for okey in self.automated_shading:
            if self.automated_shading[okey]:
                total_shading_area += orient_win_areas[okey[0]]

        shade_area = 0
        for ok in self.shading:
            print(ok)
            dh = self.shading[ok]['horizontal']['depth']
            nh = self.shading[ok]['horizontal']['num'] 
            if nh > 0:
                nh += 1
            dv = self.shading[ok]['vertical']['depth']
            nv = self.shading[ok]['vertical']['num']
            if nv > 0:
                nv += 1
            print(nh, nv)
            side = sides[ok[0]]
            if side:
                numsec = round(side / 10., 0)
                wwr = self.wwr[ok]
                # area = orient_win_areas[okey[0]]
                w_height = self.height * wwr
                w_width = (side * wwr) / numsec
                # print(ok, numsec, side, w_width)
                horizontal_area = w_width * dh * nh * numsec
                vertical_area =  w_height * dv * nv * numsec
                shade_area += horizontal_area + vertical_area
            print(shade_area)
        print('')
        total_shading_area += shade_area


        # if self.total_shade_len:
        #     shd_area = self.total_shade_len * self.shade_depth_h['s']
        # else:
        #     shd_area = 0
        #     for okey in sides:
        #         side = sides[okey]
        #         if side:
        #             numsec = round(side / 10., 0)
        #             # print(okey, side, numsec)
        #             secside = side / float(numsec)
        #             secarea = secside * self.height
        #             wwr = self.wwr[okey]
        #             vertical = self.height - 2
        #             horizontal = (secarea * wwr) / vertical
        #             shd_area += horizontal * self.shade_depth_h[okey] * numsec
        #             shd_area += vertical * self.shade_depth_v1[okey] * numsec
        #             shd_area += vertical * self.shade_depth_v2[okey] * numsec


        self.shading_embodied = total_shading_area * 0.00492126 * alum_emb # 1.5 mm aluminimum

        self.env_strings = []
        s = '{0:20}{1:32}{2:22}{3:20}{4:20}'.format('Type', 'Material', 'Thickness (ft)', 'GWP/ft3', 'GWP/ft2')
        self.env_strings.append(s)
        
        names = ['cladding', 'ext.insulation', 'framing', 'int.insulation', 'interior', 'window']
        mat = [fac_mat, ins_mat, fram_mat, int_ins_mat, int_mat, glass_mat]
        thick = [fac_thick, ins_thick, fram_thick, int_ins_thick, int_thick, glass_thick]
        emb = [fac_emb_, ins_emb_, fram_emb_, int_ins_emb_, int_emb_, win_emb_]

        for i in range(6):
            string = '{0:20}{1:20}{2:20}{3:20}{4:20}'.format(names[i],
                                                             mat[i],
                                                             thick[i],
                                                             emb[i],
                                                             thick[i] * emb[i])
            self.env_strings.append(string)


if __name__ == "__main__":
    pass