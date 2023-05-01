__author__ = ["Tomas Mendez Echenagucia"]
__copyright__ = "University of Washington 2023"
__license__ = "MIT License"
__email__ = "tmendeze@uw.edu"
__version__ = "0.1.0"

import os
import carbon_tool
import pickle
from datetime import datetime

from carbon_tool.datastructures import structure
reload(structure)
from carbon_tool.datastructures.structure import Structure

from carbon_tool.datastructures import envelope
reload(envelope)
from carbon_tool.datastructures.envelope import Envelope

from carbon_tool.functions import geometry
reload(geometry)

from carbon_tool.functions.geometry import geometric_key
from carbon_tool.functions.geometry import area_polygon
from carbon_tool.functions.geometry import rhino_surface_points

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
        self.volume                             = None
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
        self.context_buildings                  = None
        self.balconies                          = None
        self.context_building_faces             = {}
        self.balcony_faces                      = {}

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
                cores,
                context_buildings,
                balconies):

        b = cls()

        if not znames or znames == ['']:
            znames = ['zone_{}'.format(i) for i in range(len(breps))]
        elif len(znames) != len(breps):
            znames_ = ['zone_{}'.format(i) for i in range(len(znames), len(breps))]
            znames.extend(znames_)

        b.znames = znames

        volume = 0
        for i, zname in enumerate(znames):
            b.zone_breps[zname] = breps[i]
            volume += rs.SurfaceVolume(breps[i])[0]

        weather_dict = {'Seattle': carbon_tool.SEATTLE,
                        'Los Angeles': carbon_tool.LOS_ANGELES,
                        'Milwaukee': carbon_tool.MILWAUKEE,
                        'San Antonio': carbon_tool.SAN_ANTONIO,
                        'New York': carbon_tool.NEW_YORK,
                        'Atlanta': carbon_tool.ATLANTA,
                        'Minneapolis': carbon_tool.MINNEAPOLIS,
                        'Phoenix': carbon_tool.PHOENIX,
                        'San Francisco': carbon_tool.SAN_FRANCISCO,
                        'Miami': carbon_tool.MIAMI,
                        }

        glazing_dict = {'double': .4, 'triple': .2}  #### Btu/h-ft2-F


        if not out_path:
            out_path = carbon_tool.TEMP

        b.name                          = name
        b.volume                        = volume
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
        b.context_buildings             = context_buildings
        b.balconies                     = balconies

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
                    if rs.IsSurfaceTrimmed(srf):
                        pts = rhino_surface_points(srf)
                        # if len(pts) == 4:
                        #     pts = rs.SurfacePoints(srf)
                        #     pts = [pts[0], pts[1], pts[3], pts[2]]
                    else:
                        pts = rs.SurfacePoints(srf)
                        pts = [pts[0], pts[1], pts[3], pts[2]]
                    angle = rs.Angle2([[0,0,0], [0,1,0]], [[0,0,0], n])[0]
                    if n[2] == 0:
                        if angle < 135 and angle > 45 and n[0] > 0:
                            self.zone_surfaces[zk]['east'].append(srf)
                            self.zone_faces[zk]['east'].append(pts)
                        elif angle < 225 and angle > 135:
                            self.zone_surfaces[zk]['south'].append(srf)
                            self.zone_faces[zk]['south'].append(pts)
                        elif angle < 135 and angle > 45 and n[0] < 0:
                            self.zone_surfaces[zk]['west'].append(srf)
                            self.zone_faces[zk]['west'].append(pts)
                        else:
                            self.zone_surfaces[zk]['north'].append(srf)
                            self.zone_faces[zk]['north'].append(pts)
                            
                        self.zone_surfaces[zk]['walls'].append(srf)
                        self.zone_faces[zk]['walls'].append(pts)
                    elif n[2]< 0:
                        self.zone_surfaces[zk]['floor'] = srf
                        self.zone_faces[zk]['floor'] = pts
                    else:
                        self.zone_surfaces[zk]['roof'] = srf
                        self.zone_faces[zk]['roof'] = pts

        for i, srf in enumerate(self.balconies):
            pts = rs.SurfacePoints(srf)
            pts = [pts[0], pts[1], pts[3], pts[2]]
            self.balcony_faces[i] = pts

        for i, srf in enumerate(self.context_buildings):
            pts = rs.SurfacePoints(srf)
            pts = [pts[0], pts[1], pts[3], pts[2]]
            self.context_building_faces[i] = pts

    def compute_height(self):
        zk = list(self.zone_surfaces.keys())[0]
        roof = rhino_surface_points(self.zone_surfaces[zk]['roof'])
        floor = rhino_surface_points(self.zone_surfaces[zk]['floor'])
        self.height = roof[0][2] - floor[0][2]

    @property
    def floor_area(self):
        fa = 0
        for zk in self.zone_surfaces:
            fa += rs.SurfaceArea(self.zone_surfaces[zk]['floor'])[0]
            # pts = self.zone_faces[zk]['floor']
            # pts.append(pts[0])
            # pl = rs.AddPolyline(pts)
            # # print(pl)
            # # print(rs.IsCurve(pl))
            # srf = rs.AddPlanarSrf(pl)
            # if len(srf) > 1:
            #     srf = srf[0]

            # # print(srf)
            # # print(type(srf))
            # # print(rs.IsSurface(srf))
            # area = rs.SurfaceArea(srf)[0]
            # fa += area
            # fa += area_polygon(pts)
        print(fa)
        return fa

    def zone_areas(self):
        string = ''
        tot = 0
        for zk in self.znames:
            # pts = self.zone_faces[zk]['floor']
            # pts.append(pts[0])
            # pl = rs.AddPolyline(pts)
            # srf = rs.AddPlanarSrf(pl)
            # if len(srf) > 1:
            #     print(len(srf))
            #     srf = srf[0]
                
            # area = rs.SurfaceArea(srf)[0]
            area = rs.SurfaceArea(self.zone_surfaces[zk]['floor'])[0]
            # area = area_polygon(pts)
            tot += area
            string += '{:>12} = {:9.4f}\n'.format(zk, area)
        string += '{:>12} = {:9.4f}\n'.format('total', tot)
        return string
    
    @property
    def balcony_area(self):
        ba = 0
        for k in self.balcony_faces:
            pts = self.balcony_faces[k]
            ba += area_polygon(pts)
        return ba

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

    def report_operational(self):
        tot_heat = 0
        tot_cool = 0
        tot_light = 0
        for key in self.results:
            for zone in self.results[key]:
                tot_heat += self.results[key][zone]['heating'] 
                tot_cool += self.results[key][zone]['cooling']
                tot_light += self.results[key][zone]['lighting']

        tot_heat  /= 3.6e+6  # J to kwh
        tot_cool  /= 3.6e+6  # J to kwh
        tot_light /= 3.6e+6  # J to kwh

        tot_heat /= 3  # COP
        tot_cool /= 3  # COP

        return tot_heat, tot_cool, tot_light

    def write_csvs(self):
        self.write_hourly_operational()
        self.write_daily_operational()
        self.write_monthly_operational()
        self.write_embodied_csv()

    def write_embodied_csv(self):
        slab = self.structure.slab_embodied
        beam = self.structure.beam_embodied
        col = self.structure.column_embodied
        conn = self.structure.connections_embodied
        core = self.structure.core_embodied
        win = self.envelope.window_embodied
        shd = self.envelope.shading_embodied
        wall = self.envelope.wall_embodied
        tot = sum([slab, beam, col, core, conn, win, shd, wall])

        slab = round(100*(slab / tot), 1)
        beam_col = round(100*((beam + col + conn) / tot), 1)
        core = round(100*(core / tot), 1)
        win = round(100*(win / tot), 1)
        shd = round(100*(shd / tot), 1)
        wall = round(100*(wall / tot), 1)
        tot_ft2 = tot / self.floor_area
        fh = open(os.path.join(self.out_path, self.name, 'embodied_results.csv'), 'w')


        fh.write('{}, {}, (%)\n'.format('slab', slab))
        fh.write('{}, {}, (%)\n'.format('beams & columns', beam_col))
        fh.write('{}, {}, (%)\n'.format('core', core))
        fh.write('{}, {}, (%)\n'.format('windows', win))
        fh.write('{}, {}, (%)\n'.format('shading', shd))
        fh.write('{}, {}, (%)\n'.format('walls', wall))
        fh.write('{}, {},  (kg CO2e)\n'.format('total', tot))
        fh.write('{}, {},  (kg CO2e / ft2)\n'.format('total /ft2', tot_ft2))
        fh.close()

    def write_monthly_operational(self):

        results = {}
        for key in self.results:
            _, h, d, m = key.split('_')
            # tkey = '0_0_{}_{}'.format(d, m)
            tkey = datetime(2023, int(m), 1, 0)
            if tkey not in results:
                results[tkey] = {}
            for zone in self.znames:
                if zone not in results[tkey]:
                    results[tkey][zone] = {'heating': 0, 'cooling':0, 'lighting': 0}

                results[tkey][zone]['heating'] += self.results[key][zone]['heating']
                results[tkey][zone]['cooling'] += self.results[key][zone]['cooling']
                results[tkey][zone]['lighting'] += self.results[key][zone]['lighting']

        fh = open(os.path.join(self.out_path, self.name, 'operational_monthly_results.csv'), 'w')


        fh.write('time,')
        for zone in self.znames:
            fh.write('{0} heating (KWh),{0} cooling (KWh),{0} lighting (KWh),'.format(zone))
        fh.write('TOTAL heating (KWh),TOTAL cooling (KWh),TOTAL lighting (KWh)\n'.format(zone))
        # fh.write('\n')

        times = sorted(list(results.keys()))

        for time in times:
            fh.write('{},'.format(time))
            tot_heat = 0
            tot_cool = 0
            tot_light = 0
            for zone in self.znames:
                heat = results[time][zone]['heating']
                cool = results[time][zone]['cooling']
                light = results[time][zone]['lighting']
                
                heat  /= 3.6e+6  # J to kwh
                cool  /= 3.6e+6  # J to kwh
                light /= 3.6e+6  # J to kwh
                heat /= 3  # COP
                cool /= 3  # COP

                tot_heat += heat
                tot_cool += cool
                tot_light += light

                fh.write('{},{},{},'.format(heat, cool, light))

            fh.write('{},{},{}\n'.format(tot_heat, tot_cool, tot_light))
            # fh.write('\n')
        fh.close()

    def write_daily_operational(self):

        results = {}
        for key in self.results:
            _, h, d, m = key.split('_')
            # tkey = '0_0_{}_{}'.format(d, m)
            tkey = datetime(2023, int(m), int(d), 0)
            if tkey not in results:
                results[tkey] = {}
            for zone in self.znames:
                if zone not in results[tkey]:
                    results[tkey][zone] = {'heating': 0, 'cooling':0, 'lighting': 0}

                results[tkey][zone]['heating'] += self.results[key][zone]['heating']
                results[tkey][zone]['cooling'] += self.results[key][zone]['cooling']
                results[tkey][zone]['lighting'] += self.results[key][zone]['lighting']

        fh = open(os.path.join(self.out_path, self.name, 'operational_daily_results.csv'), 'w')


        fh.write('time,')
        for zone in self.znames:
            fh.write('{0} heating (KWh),{0} cooling (KWh),{0} lighting (KWh),'.format(zone))
        fh.write('TOTAL heating (KWh),TOTAL cooling (KWh),TOTAL lighting (KWh)\n'.format(zone))
        # fh.write('\n')

        times = sorted(list(results.keys()))

        for time in times:
            fh.write('{},'.format(time))
            tot_heat = 0
            tot_cool = 0
            tot_light = 0
            for zone in self.znames:
                heat = results[time][zone]['heating']
                cool = results[time][zone]['cooling']
                light = results[time][zone]['lighting']
                
                heat  /= 3.6e+6  # J to kwh
                cool  /= 3.6e+6  # J to kwh
                light /= 3.6e+6  # J to kwh
                heat /= 3  # COP
                cool /= 3  # COP

                tot_heat += heat
                tot_cool += cool
                tot_light += light

                fh.write('{},{},{},'.format(heat, cool, light))
            fh.write('{},{},{}\n'.format(tot_heat, tot_cool, tot_light))
            # fh.write('\n')
        fh.close()

    def write_hourly_operational(self):

        fh = open(os.path.join(self.out_path, self.name, 'operational_hourly_results.csv'), 'w')
        times = []
        data = {}
        for key in self.results:
            _, h, d, m = key.split('_')
            time = datetime(2023, int(m), int(d), int(h))
            times.append(time)
            data[time] = {}
            for zone in self.znames:
                heat = self.results[key][zone]['heating'] 
                cool = self.results[key][zone]['cooling']
                light = self.results[key][zone]['lighting']

                heat  /= 3.6e+6  # J to kwh
                cool  /= 3.6e+6  # J to kwh
                light /= 3.6e+6  # J to kwh
                heat /= 3  # COP
                cool /= 3  # COP

                data[time][zone] = {'heat': heat,
                                    'cool': cool,
                                    'light': light,
                                    }

        fh.write('time,')
        for zone in self.znames:
            fh.write('{0} heating (KWh),{0} cooling (KWh),{0} lighting (KWh),'.format(zone))
        fh.write('TOTAL heating (KWh),TOTAL cooling (KWh),TOTAL lighting (KWh)\n'.format(zone))
        # fh.write('\n')


        times = sorted(times)
        for time in times:
            fh.write('{},'.format(time))
            tot_heat = 0
            tot_cool = 0
            tot_light = 0
            for zone in self.znames:
                heat = data[time][zone]['heat']
                cool = data[time][zone]['cool']
                light = data[time][zone]['light']

                tot_heat += heat
                tot_cool += cool
                tot_light += light

                fh.write('{},{},{},'.format(heat, cool, light))
            fh.write('{},{},{}\n'.format(tot_heat, tot_cool, tot_light))
            # fh.write('\n')
        fh.close()

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

    def surface_to_volume(self):
        area = 0
        for zk in self.zone_faces:
            for wall in self.zone_faces[zk]['walls']:
                area += area_polygon(wall)
        return area / self.volume

if __name__ == '__main__':
    for i in range(50): print('')
    
    import os

    filepath = os.path.join(carbon_tool.TEMP, 'test_building_20230328163220.obj')
    b = Building.from_obj(filepath)
