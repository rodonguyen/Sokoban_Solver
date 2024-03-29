
import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '..')
sys.path.insert(0, '../')
sys.path.insert(0, '/..')
sys.path.insert(0, '../CAB320_assignments')
sys.path.append('../sokoban.py')
import sokoban
import mySokobanSolver



def do_2():
    warehouse = sokoban.Warehouse()
    w = "warehouses/warehouse_39.txt"               # Change warehouse here
    warehouse.load_warehouse(w)
    sokobanPuzzle = mySokobanSolver.SokobanPuzzle(warehouse)

    rows = str(warehouse).split('\n')
    for column, row in enumerate(rows):
        if row.find('.') != -1:
            print(column,row.find('.'))
            break


    print(str(warehouse).index('@'))

    print(warehouse.ncols)

    # print(str(warehouse))
    # print(sokobanPuzzle.goal_test(sokobanPuzzle.initial))

    print(sokobanPuzzle.initial)


def do_1():
    warehouse = sokoban.Warehouse()
    w = "../warehouses/warehouse_39.txt"               # Change warehouse here
    warehouse.load_warehouse(w)


    #------------------ Code from taboo_cells() -----------------------
    inside_cells = mySokobanSolver.get_inside_cells(warehouse)
    inside_corner_cells = mySokobanSolver.get_corner_cells(warehouse, inside_cells)
    taboo_cells_set = mySokobanSolver.get_taboo_cells(warehouse, list(inside_corner_cells))

    taboo_cells_string = ""
    for y in range(warehouse.nrows):
        if y != 0:
            taboo_cells_string += "\n"
        
        for x in range(warehouse.ncols):
            if (x, y) in warehouse.walls:
                taboo_cells_string += '#'
            elif (x, y) in taboo_cells_set:
                taboo_cells_string += 'X'
            else:
                taboo_cells_string += ' '
    #----------------------------------------------------------------------

    # Record and display results
    file = open('bin/expected_taboo_cells_'+w[11:], 'w')    # Edit the output location here
    file.write(taboo_cells_string)

    file.write('\n\nOriginal warehouse text file:')
    warehouse_txt = open(w, 'r')
    for line in warehouse_txt:
        file.write(line)
    file.close()

    print()
    print('Testing on:', w) 
    print('Inside cells:', inside_cells)
    print('Corners:', inside_corner_cells)
    print('Taboo cells:', taboo_cells_set)





do_2()

















