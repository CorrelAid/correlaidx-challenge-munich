#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep  3 22:28:37 2020

@author: mitch
"""

# subset GADM data to Bavaria NUTS2 and NUTS3

# manually download the Shapefiles for Germany from https://www.gadm.org/
# extract the zip, and maybe adjust folders

import os
import geopandas as gpd
# needs pkg descartes installed for plotting


de_nuts2_full = gpd.read_file("gadm36_DEU_shp/gadm36_DEU_2.shp")
de_nuts2_bavaria = de_nuts2_full[de_nuts2_full["NAME_1"] == "Bayern"]

# de_nuts2_bavaria.plot()

os.makedirs("shp/bavaria_nuts2")
de_nuts2_bavaria.to_file("shp/bavaria_nuts2/bavaria_nuts2.shp")


# actually nuts2 in GADM is nuts2 in datenguidepy
# -> so no need for rest


# de_nuts3_full = gpd.read_file("gadm36_DEU_shp/gadm36_DEU_3.shp")
# de_nuts3_bavaria = de_nuts3_full[de_nuts3_full["NAME_1"] == "Bayern"]

# # de_nuts3_bavaria.plot()

# os.makedirs("shp/bavaria_nuts3")
# de_nuts3_bavaria.to_file("shp/bavaria_nuts3/bavaria_nuts3.shp")

