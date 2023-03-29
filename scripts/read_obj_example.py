# import rhinoscriptsyntax as rs
import carbon_tool
import os

from carbon_tool.datastructures import Building
from carbon_tool.functions import read_results_file

filepath = os.path.join(carbon_tool.TEMP, 'test_building_20230328205042.obj')

b = Building.from_obj(filepath)

print(b.structure.beam_embodied)

