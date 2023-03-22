"""
********************************************************************************
carbon_tool
********************************************************************************

.. currentmodule:: carbon_tool


.. toctree::
    :maxdepth: 1


"""

from __future__ import print_function

import os


__author__ = ["Tomas Mendez Echenagucia"]
__copyright__ = "University of Washington 2023"
__license__ = "MIT License"
__email__ = "tmendeze@uw.edu"
__version__ = "0.1.0"


HERE = os.path.dirname(__file__)

HOME = os.path.abspath(os.path.join(HERE, "../../"))
DATA = os.path.abspath(os.path.join(HOME, "data"))
DOCS = os.path.abspath(os.path.join(HOME, "docs"))
TEMP = os.path.abspath(os.path.join(HOME, "temp"))

# Weather files - - -
root = os.path.join(HERE, '../../')
SEATTLE = os.path.abspath(os.path.join(root, 'data', 'weather_files', 'USA_WA_Seattle-Tacoma.Intl.AP.727930_TMY3.epw'))
ATLANTA = os.path.abspath(os.path.join(root, 'data', 'weather_files', 'USA_GA_Atlanta-Hartsfield-Jackson.Intl.AP.722190_TMY3.epw'))
MILWAUKEE = os.path.abspath(os.path.join(root, 'data', 'weather_files', 'USA_WI_Milwaukee-Mitchell.Intl.AP.726400_TMY3.epw'))
SAN_ANTONIO = os.path.abspath(os.path.join(root, 'data', 'weather_files', 'USA_TX_San.Antonio.Intl.AP.722530_TMY3.epw'))
NEW_YORK = os.path.abspath(os.path.join(root, 'data', 'weather_files', 'USA_NY_New.York-Central.Park.725033_TMY3.epw'))
LOS_ANGELES = os.path.abspath(os.path.join(root, 'data', 'weather_files', 'USA_CA_Los.Angeles.Intl.AP.722950_TMY3.epw'))


__all__ = ["HOME", "DATA", "DOCS", "TEMP"]
