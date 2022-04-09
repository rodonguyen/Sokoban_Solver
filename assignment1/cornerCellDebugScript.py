# -*- coding: utf-8 -*-
"""
Created on Wed Apr  6 08:36:09 2022

@author: gunzy
"""

import sokoban

warehouse = sokoban.Warehouse()
warehouse.load_warehouse("./warehouses/warehouse_25.txt")

import mySokobanSolver
corners = mySokobanSolver.get_corner_cells(warehouse)
cornerPairs = mySokobanSolver.get_corner_pairs(warehouse, corners)