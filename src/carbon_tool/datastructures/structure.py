from __future__ import print_function

__author__ = ["Tomas Mendez Echenagucia"]
__copyright__ = "University of Washington 2023"
__license__ = "MIT License"
__email__ = "tmendeze@uw.edu"
__version__ = "0.1.0"

from carbon_tool.functions import material_reader
try:
    reload(material_reader)
except:
    pass
from carbon_tool.functions.material_reader import read_materials
from carbon_tool.functions.material_reader import read_materials_city

from math import sqrt
from carbon_tool.functions import distance_point_point
from carbon_tool.functions import geometric_key
from carbon_tool.functions import midpoint_point_point
from carbon_tool.functions import area_polygon

TPL = """
################################################################################
Structure datastructure: {}
################################################################################

span:   {}
embodied: {}

"""

# TODO: Add gypsum to beams and columns

class Structure(object):
    def __init__(self):
        self.conc_thick = 2. / 12. # 2 inches in feet
        self.gypsum_thick = (2 * (5. / 8.)) / 12. # based on min 80 minutes fire rating
        self.gl_allowable = 2400 * 144. * .6 # GL24f in psi to psf .6 safety
        self.liveload = 80  # lbs / ft2 
        self.clt_density = 36  # lbs / ft3
        self.concrete_density = 149.8271  # lbs / ft3
        
        self.name               = 'carbon_tool Structure'
        self.city               = None
        self.area               = None
        self.composite          = None
        self.btype              = None
        self.num_floors_above   = None
        self.core               = None
        self.slab_embodied      = None
        self.beam_embodied      = None
        self.column_embodied    = None
        self.timber_thick       = None
        self.span_x             = None
        self.span_y             = None
        self.column_length      = None
        self.height             = None
        self.columns            = None
        self.n_columns          = None
        self.main_beams         = None
        self.second_beams       = None 
        self.main_span          = None
        self.second_span        = None 
        
    def __str__(self):
        return TPL.format(self.name)

    @classmethod
    def from_geometry(cls, building):
        structure = cls()
        structure.add_columns_beams(building)
        structure.area = building.floor_area

        structure.name               += '{}_'.format(building.name)
        structure.city               = building.city
        structure.composite          = building.composite_slab
        structure.btype              = building.building_type
        structure.num_floors_above   = building.num_floors_above

        structure.column_length = 0
        temp = []
        for a, b in structure.columns:
            d = distance_point_point(a, b)
            structure.column_length += d
            temp.append(d)

        structure.height = max(temp)
        structure.n_columns = len(structure.columns)

        if structure.span_x > structure.span_y:
            structure.main_beams = structure.beams_x
            structure.second_beams = structure.beams_y
            structure.main_span = structure.span_x
            structure.second_span = structure.span_y
        else:
            structure.main_beams = structure.beams_y
            structure.second_beams = structure.beams_x
            structure.main_span = structure.span_y
            structure.second_span = structure.span_x
        return structure

    def get_materials(self):
        self.clt_kgco2_yd3 = read_materials_city('CLT', self.city)
        self.glulam_kgco2_yd3 = read_materials_city('Glulam', self.city)
        self.conc_kgco2_yd3 = read_materials_city('Concrete', self.city)
        self.gyp_kgco2_yd3 = read_materials_city('GypsumX', self.city)
        self.steel_kgco2_yd3 = read_materials_city('Steel', self.city)
        self.rebar_kgco2_yd3 = read_materials_city('Rebar', self.city)

    def add_columns_beams(self, building):
        columns = building.columns
        beams_x = building.beams_x
        beams_y = building.beams_y
        cores    = building.cores

        cmap = []
        cols = []
        for col in columns:
            mpt = midpoint_point_point(col[0], col[1])
            gk = geometric_key(mpt)
            if gk not in cmap:
                cols.append(col)
                cmap.append(gk)

        cmap = []
        bx = []
        for b in beams_x:
            mpt = midpoint_point_point(b[0], b[1])
            gk = geometric_key(mpt)
            if gk not in cmap:
                bx.append(b)
                cmap.append(gk)

        cmap = []
        by = []
        for b in beams_y:
            mpt = midpoint_point_point(b[0], b[1])
            gk = geometric_key(mpt)
            if gk not in cmap:
                by.append(b)
                cmap.append(gk)

        columns = [[list(a), list(b)] for a, b in columns]
        bx = [[list(a), list(b)] for a, b in bx]
        by = [[list(a), list(b)] for a, b in by]

        cores_ = []
        for core in cores:
            cores_.append([list(p) for p in core])

        self.columns = columns
        self.beams_x = bx
        self.beams_y = by
        self.cores = cores_

        self.span_x = 0
        self.span_y = 0
        for a, b in bx:
            d = distance_point_point(a, b)
            if d > self.span_x:
                self.span_x = d

        for a, b in by:
            d = distance_point_point(a, b)
            if d > self.span_y:
                self.span_y = d  

    def compute_embodied(self):
        self.get_materials()
        self.compute_slab_embodied()
        self.compute_column_embodied()
        self.compute_beam_embodied()
        self.compute_core_embodied()
        
    def compute_slab_embodied(self):
        """These values are taken from Strobel (2016), using composite/non composite 
        values. Two inches of concrete are added for acoustics, and two more when 
        composite action is specified. Spans should be in feet, thicknesses in feet. 
        """
        span = self.second_span
        if self.composite:
            self.conc_thick *= 2.
            if span < 20:
                thick = 3.9 / 12.# feet
            elif span < 25:
                thick = 6.7 / 12.# feet
            elif span < 30:
                thick = 9.4 / 12.
            elif span < 35:
                thick = 12.2 / 12.
            else:
                raise(NameError('Span is too large for composite CLT slab'))
        else:
            if span < 20:
                thick = 6.7 / 12.# feet
            elif span < 25:
                thick = 8.6 / 12.# feet
            elif span < 30:
                thick = 10.4 / 12.
            else:
                raise(NameError('Span is too large for composite CLT slab'))
        
        # timber - - -
        self.timber_thick = thick
        timber =  ((self.area  * thick) / 27.) * self.clt_kgco2_yd3

        # conrete - - -
        concrete = ((self.area * self.conc_thick) / 27.) * self.conc_kgco2_yd3

        # gypsum - - - 
        if self.btype in ['Type 3', 'Type 4C', 'Type 5']:
            gypsum = 0
            self.gypsum_thick = 0.
        elif self.btype == 'Type 4B':
            gypsum = ((self.area * .8 * self.gypsum_thick) / 27.) * self.gyp_kgco2_yd3
            self.gypsum_thick *= .8
        elif self.btype == 'Type 4A':
            gypsum = ((self.area * 1. * self.gypsum_thick) / 27.) * self.gyp_kgco2_yd3
        else:
            raise(NameError('Bulinding type is wrong'))
        
        self.slab_embodied = timber + concrete + gypsum

        self.slab_strings = []
        s = '{0:20}{1:32}{2:22}{3:20}{4:20}'.format('Type', 'Material', 'Thickness (ft)', 'GWP/ft3', 'GWP/ft2')
        self.slab_strings.append(s)

        names = ['Top', 'Slab ', 'Fire protection', 'total']
        mat = ['Concrete', 'CLT', 'Gypsum', 'all']
        thick = [self.conc_thick, self.timber_thick, self.gypsum_thick]
        thick.append(sum(thick))
        emb = [self.conc_kgco2_yd3 / 27., self.clt_kgco2_yd3 / 27., self.gyp_kgco2_yd3 / 27]
        etot = sum([emb[0] * thick[0], emb[1] * thick[1], emb[2] * thick[2]])
        etot /= thick[-1]
        emb.append(etot)
        for i in range(4):
            string = '{0:20}{1:20}{2:20}{3:20}{4:20}'.format(names[i],
                                                             mat[i],
                                                             thick[i],
                                                             emb[i],
                                                             thick[i] * emb[i])
            self.slab_strings.append(string)
        
    def compute_column_embodied(self):
        
        trib = self.span_x * self.span_y
        concrete_dl = self.conc_thick * trib * self.concrete_density
        timber_dl = self.timber_thick * trib * self.clt_density 
        ll = trib * self.liveload  # live load in lbs / ft3
        load = (concrete_dl + timber_dl + ll) * self.num_floors_above

        self.col_area = load / self.gl_allowable
        self.col_side = sqrt(self.col_area)

        if self.col_side < 1:
            self.col_side = 1.

        if self.btype in ['Type 3', 'Type 5']:
            self.col_side += 1.8 / 12.
        elif self.btype in ['Type 4B', 'Type 4C']:
            self.col_side += 3.6 / 12.
        elif self.btype == 'Type 4A':
            self.col_side += 5.4 / 12.
        else:
            raise(NameError('Bulinding type is wrong'))

        self.col_area = self.col_side**2
        vol = (self.col_area * self.height) / 27.  # vol in cubic yards

        timber = vol * self.glulam_kgco2_yd3 * self.n_columns
        self.column_embodied = timber

        steel_vol = (self.col_side * 4 * (1. / 12.)) / 27. 
        self.connections_embodied = steel_vol * self.steel_kgco2_yd3 * self.n_columns
        self.col_string = 'Column dim. {} x {} ft'.format(round(self.col_side, 2), round(self.col_side, 2))

    def compute_beam_embodied(self):

        concrete_dl = self.conc_thick * self.concrete_density
        timber_dl = self.timber_thick * self.clt_density 
        dl = concrete_dl + timber_dl
        trib_l = self.second_span
        l = self.main_span
        w_load = trib_l * (dl + self.liveload)
        m_max = (w_load * l**2) / 8.
        fb = self.gl_allowable

        self.beam_width = self.col_side * .5
        if self.beam_width < 1:
            self.beam_width = 1.
        self.beam_height = sqrt((6 * m_max) / (fb * self.beam_width))

        tot_len_main = 0
        for a, b in self.main_beams:
            d = distance_point_point(a, b)
            tot_len_main += d

        tot_len_second = 0
        for a, b in self.second_beams:
            d = distance_point_point(a, b)
            tot_len_second += d

        vol = self.beam_width * self.beam_height * tot_len_main
        vol += self.beam_width * (self.beam_height / 2.) * tot_len_second
        vol /= 27.

        timber = vol * self.glulam_kgco2_yd3
        self.beam_embodied = timber
        self.beam_string = 'Beam dim. {} x {} ft'.format(round(self.beam_width, 2), round(self.beam_height, 2))

    def compute_core_embodied(self):
        tdist = 0
        for pts in self.cores:
            for i in range(len(pts) - 1):
                a, b = pts[i], pts[i + 1]
                tdist += distance_point_point(a, b)
        vol = tdist * self.height * 0.037037
        self.core_embodied = (vol * self.conc_kgco2_yd3) + (vol * .04 * self.rebar_kgco2_yd3)

if __name__ == "__main__":
    pass
