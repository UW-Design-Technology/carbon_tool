import os
import carbon_tool

from carbon_tool.datastructures import Building

def make_pies(filename, num_years):
    path = carbon_tool.TEMP

    filepath = os.path.join(path, filename)

    b = Building.from_obj(filepath)

    # embodied - - - -

    embodied, tot, tot_ft2 = make_emb_pie(b)

    # operational - - - -

    heat, cool, li = b.report_operational()
    tot_ = heat + cool + li

    cool = round(100*(cool / tot_), 1)
    heat = round(100*(heat / tot_), 1)
    li = round(100*(li / tot_), 1)

    s = ['cooling {}%'.format(cool)] * int(cool)
    b = ['heating {}%'.format(heat)] * int(heat)
    c = ['lighting {}%'.format(li)] * int(li)

    operational = s + b + c

    # operational vs embodied  - - - 

    tot_ *= num_years

    t = tot + tot_
    e = round(100*(tot / t), 1)
    o = round(100*(tot_ / t), 1)

    e = ['embodied {}%'.format(e)] * int(e)
    o = ['operational {}%'.format(o)] * int(o)

    emb_v_op = e + o
    return embodied, operational, emb_v_op  #, embft, opft

def make_emb_pie(building):
    slab = building.structure.slab_embodied
    beam = building.structure.beam_embodied
    col = building.structure.column_embodied
    conn = building.structure.connections_embodied
    core = building.structure.core_embodied
    win = building.envelope.window_embodied
    shd = building.envelope.shading_embodied
    wall = building.envelope.wall_embodied
    tot = sum([slab, beam, col, core, conn, win, shd, wall])
    # tot = sum([slab, beam, col, core, conn])

    slab = round(100*(slab / tot), 1)
    beam_col = round(100*((beam + col + conn) / tot), 1)
    core = round(100*(core / tot), 1)
    win = round(100*(win / tot), 1)
    shd = round(100*(shd / tot), 1)
    wall = round(100*(wall / tot), 1)

    s = ['{} {}%'.format('slab', slab)] * int(slab)
    b = ['{} {}%'.format('beams & columns', beam_col)] * int(beam_col)
    c = ['{} {}%'.format('core', core)] * int(core)
    wi = ['{} {}%'.format('windows', win)] * int(win)
    sh = ['{} {}%'.format('shading', shd)] * int(shd)
    wa = ['{} {}%'.format('walls', wall)] * int(wall)

    tot_ft2 = tot / building.floor_area

    return s + b + c + wi + sh + wa, tot, tot_ft2
    # return s + b + c, tot, tot_ft2

