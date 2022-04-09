'''

    Sokoban assignment


The functions and classes defined in this module will be called by a marker script. 
You should complete the functions and classes according to their specified interfaces.

No partial marks will be awarded for functions that do not meet the specifications
of the interfaces.

You are NOT allowed to change the defined interfaces.
In other words, you must fully adhere to the specifications of the 
functions, their arguments and returned values.
Changing the interfacce of a function will likely result in a fail 
for the test of your code. This is not negotiable! 

You have to make sure that your code works with the files provided 
(search.py and sokoban.py) as your code will be tested 
with the original copies of these files. 

Last modified by 2022-03-27  by f.maire@qut.edu.au
- clarifiy some comments, rename some functions
  (and hopefully didn't introduce any bug!)

'''

# You have to make sure that your code works with 
# the files provided (search.py and sokoban.py) as your code will be tested 
# with these files
import search 
import sokoban

# The index of the x-coordinate in a 2D tuple
X_INDEX = 0
# The index of the y-coordinate in a 2D tuple
Y_INDEX = 1

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


def my_team():
    '''
    Return the list of the team members of this assignment submission as a list
    of triplet of the form (student_number, first_name, last_name)
    
    '''
    return [(10210776, 'Mitchell', 'Egan'), (10396489, 'Jaydon', 'Gunzburg'), (10603280, 'Rodo', 'Nguyen')]

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def get_inside_cells(warehouse, inside_cells = None, cell = None):
    '''
    Recursively identify inside cells (the cells that are enclosed by walls in 
    the space of the worker) using the flood fill algorithm. Adapted from:
    https://en.wikipedia.org/wiki/Flood_fill#Stack-based_recursive_implementation_(four-way)

    Parameters
    ----------
    warehouse : Warehouse
        A Warehouse object with the worker inside the warehouse.
    inside_cells : List, optional
        A list of already identified inside cells (coordinate tuples). The default is [].
    cell : Tuple, optional
        A cell to check if inside. The default is None.

    Returns
    -------
    List
        A list of identified inside cells.
    '''
    
    # If called with no inside_cells parameter
    if (inside_cells is None):
        inside_cells = set()
        
    # If called with no cell parameter
    if (cell is None):
        cell = warehouse.worker
    
    # If the cell has already been classified as inside or the cell is a wall
    if (cell in inside_cells or cell in warehouse.walls):
        return inside_cells
    
    inside_cells.add(cell)
    
    # Recursively call get_inside_cells on cells to the north, south, west and 
    # east of current cell
    inside_cells = get_inside_cells(warehouse, inside_cells, (cell[X_INDEX], cell[Y_INDEX] + 1))
    inside_cells = get_inside_cells(warehouse, inside_cells, (cell[X_INDEX], cell[Y_INDEX] - 1))
    inside_cells = get_inside_cells(warehouse, inside_cells, (cell[X_INDEX] - 1, cell[Y_INDEX]))
    inside_cells = get_inside_cells(warehouse, inside_cells, (cell[X_INDEX] + 1, cell[Y_INDEX]))

    return inside_cells

def is_corner(warehouse, cell):
    '''
    Determine if a cell is a corner by checking it has at least one neighbouring 
    wall on each axis.
    
    Parameters
    ----------
    warehouse : Warehouse
        A Warehouse object with the worker inside the warehouse.
    cell : Tuple
        A cell to check.

    Returns
    -------
    Bool
        True if a cell is a corner, else False.

    '''
    wall_neighbour_x = (cell[X_INDEX] - 1, cell[Y_INDEX]) in warehouse.walls or (cell[X_INDEX] + 1, cell[Y_INDEX]) in warehouse.walls
    wall_neighbour_y = (cell[X_INDEX], cell[Y_INDEX] - 1) in warehouse.walls or (cell[X_INDEX], cell[Y_INDEX] + 1) in warehouse.walls
    
    return wall_neighbour_x and wall_neighbour_y

def get_corner_cells(warehouse, cells):
    '''
    Identify corner cells.

    Parameters
    ----------
    warehouse : Warehouse
        A Warehouse object with the worker inside the warehouse.
    cells : List
        A list of cells to check.

    Returns
    -------
    corner_cells : List
        A list of identified corner cells.

    '''
    
    corner_cells = set()
    
    for cell in cells:
        if is_corner(warehouse, cell):
            corner_cells.add(cell)
                
    return corner_cells

def get_taboo_cells(warehouse, inside_corner_cells):
    '''
    Identify taboo cells (inside non-target corners AND 
    all non-target cells between inside non-target taboo corners).

    Parameters
    ----------
    warehouse : Warehouse
        A Warehouse object with the worker inside the warehouse.
    inside_corner_cells : List
        A list of inside corners to check.

    Returns
    -------
    List
        A list of identified taboo cells.

    '''
    
    taboo_cells_set = set()
    
    # For each inside corner cell where i is its index
    for i, inside_corner_cell in enumerate(inside_corner_cells):
        # If inside corner cell is a target (thus not taboo)
        if inside_corner_cell in warehouse.targets:
            continue
        
        taboo_cells_set.add(inside_corner_cell)
        
        # Starting from the index after the inside corner cell, for each other 
        # inside corner cell
        for other_inside_corner_cell in inside_corner_cells[i + 1:]:
            # If other inside corner cell is a target (thus not taboo)
            if other_inside_corner_cell in warehouse.targets:
                continue
            
            taboo_cells_set.add(other_inside_corner_cell)
            
            # Bool representing that a wall is shared between corners in the 
            # negative non-shared-direction (i.e. walls on left for both 
            # corners if shared x-coordinate, or walls on top if shared y-
            # coordinate
            negative_wall_shared = False
            # Bool representing that a wall is shared between corners in the 
            # positive non-shared-direction (i.e. walls on right for both 
            # corners if shared x-coordinate, or walls on bottom if shared y-
            # coordinate
            positive_wall_shared = False
            
            # If inside corners share x-coordinate
            if inside_corner_cell[X_INDEX] == other_inside_corner_cell[X_INDEX]:
                # If corners share wall on left
                if ((inside_corner_cell[X_INDEX] - 1, inside_corner_cell[Y_INDEX]) in warehouse.walls and
                    (other_inside_corner_cell[X_INDEX] - 1, other_inside_corner_cell[Y_INDEX]) in warehouse.walls):
                    negative_wall_shared = True
                    
                # If corners share wall on right
                if ((inside_corner_cell[X_INDEX] + 1, inside_corner_cell[Y_INDEX]) in warehouse.walls and
                    (other_inside_corner_cell[X_INDEX] + 1, other_inside_corner_cell[Y_INDEX]) in warehouse.walls):
                    positive_wall_shared = True
                    
                # If corners don't share a wall in the shared-direction (i.e. 
                # top corner: ‾|, bottom corner: |_)
                if not negative_wall_shared and not positive_wall_shared:
                    continue
                
                # Axis to traverse along wall between corners (y-axis)
                traversal_axis = Y_INDEX
            # Else if inside corners share y-coordinate
            elif inside_corner_cell[Y_INDEX] == other_inside_corner_cell[Y_INDEX]:
                # If corners share wall on top
                if ((inside_corner_cell[X_INDEX], inside_corner_cell[Y_INDEX] - 1) in warehouse.walls and
                    (other_inside_corner_cell[X_INDEX], other_inside_corner_cell[Y_INDEX] - 1) in warehouse.walls):
                    negative_wall_shared = True
                    
                # If corners share wall on bottom
                if ((inside_corner_cell[X_INDEX], inside_corner_cell[Y_INDEX] + 1) in warehouse.walls and
                    (other_inside_corner_cell[X_INDEX], other_inside_corner_cell[Y_INDEX] + 1) in warehouse.walls):
                    positive_wall_shared = True
                 
                # If corners don't share a wall in the shared-direction (i.e. 
                # left corner: |‾, right corner: _|)
                if not negative_wall_shared and not positive_wall_shared:
                    continue
                
                # Axis to traverse along wall between corners (x-axis)
                traversal_axis = X_INDEX
            # Else inside corners are not aligned (thus no taboo cells between them)
            else:
                continue
            
            distance = other_inside_corner_cell[traversal_axis] - inside_corner_cell[traversal_axis]
            
            # If there are no cells between corners
            if abs(distance) == 1:
                continue
            
            # Positive/negative indication of the direction to traverse
            step = distance // abs(distance)
            
            traversed_cells = []
            
            # For each traversal-axis value between corners
            for traversal_axis_value in range(inside_corner_cell[traversal_axis] + step, other_inside_corner_cell[traversal_axis], step):
                if traversal_axis == X_INDEX:
                    if ((traversal_axis_value, inside_corner_cell[Y_INDEX]) in warehouse.targets or
                        (traversal_axis_value, inside_corner_cell[Y_INDEX]) in warehouse.walls):
                        traversed_cells.clear()
                        break
                    
                    if negative_wall_shared:
                        # If negative shared wall is broken
                        if (traversal_axis_value, inside_corner_cell[Y_INDEX] - 1) not in warehouse.walls:
                            negative_wall_shared = False
                            
                    if positive_wall_shared:
                        # If positive shared wall is broken
                        if (traversal_axis_value, inside_corner_cell[Y_INDEX] + 1) not in warehouse.walls:
                            positive_wall_shared = False
                            
                    # If corners still share at least one wall
                    if negative_wall_shared or positive_wall_shared:
                        traversed_cells.append((traversal_axis_value, inside_corner_cell[Y_INDEX]))
                    # Else corners no longer share a wall
                    else:
                        traversed_cells.clear()
                        break
                elif traversal_axis == Y_INDEX:
                    if ((inside_corner_cell[X_INDEX], traversal_axis_value) in warehouse.targets or
                        (inside_corner_cell[X_INDEX], traversal_axis_value) in warehouse.walls):
                        traversed_cells.clear()
                        break
                    
                    # If negative shared wall is broken
                    if negative_wall_shared:
                        if (inside_corner_cell[X_INDEX] - 1, traversal_axis_value) not in warehouse.walls:
                            negative_wall_shared = False
                          
                    # If positive shared wall is broken
                    if positive_wall_shared:
                        if (inside_corner_cell[X_INDEX] + 1, traversal_axis_value) not in warehouse.walls:
                            positive_wall_shared = False

                    # If corners still share at least one wall
                    if negative_wall_shared or positive_wall_shared:
                        traversed_cells.append((inside_corner_cell[X_INDEX], traversal_axis_value))
                    # Else corners no longer share a wall
                    else:
                        traversed_cells.clear()
                        break
                    
            taboo_cells_set.update(traversed_cells)
            
    return taboo_cells_set

def taboo_cells(warehouse):
    '''  
    Identify the taboo cells of a warehouse. A "taboo cell" is by definition
    a cell inside a warehouse such that whenever a box get pushed on such 
    a cell then the puzzle becomes unsolvable. 
    
    Cells outside the warehouse are not taboo. It is a fail to tag an 
    outside cell as taboo.
    
    When determining the taboo cells, you must ignore all the existing boxes, 
    only consider the walls and the target  cells.  
    Use only the following rules to determine the taboo cells;
     Rule 1: if a cell is a corner and not a target, then it is a taboo cell.
     Rule 2: all the cells between two corners along a wall are taboo if none of 
             these cells is a target.
    
    @param warehouse: 
        a Warehouse object with the worker inside the warehouse

    @return
       A string representing the warehouse with only the wall cells marked with 
       a '#' and the taboo cells marked with a 'X'.  
       The returned string should NOT have marks for the worker, the targets,
       and the boxes.  
    '''
    
    inside_cells = get_inside_cells(warehouse)
    inside_corner_cells = get_corner_cells(warehouse, inside_cells)
    taboo_cells_set = get_taboo_cells(warehouse, list(inside_corner_cells))
    
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
                
    
    return taboo_cells_string

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


class SokobanPuzzle(search.Problem):
    '''
    An instance of the class 'SokobanPuzzle' represents a Sokoban puzzle.
    An instance contains information about the walls, the targets, the boxes
    and the worker.

    Your implementation should be fully compatible with the search functions of 
    the provided module 'search.py'. 
    
    '''
    
    #
    #         "INSERT YOUR CODE HERE"
    #
    #     Revisit the sliding puzzle and the pancake puzzle for inspiration!
    #
    #     Note that you will need to add several functions to 
    #     complete this class. For example, a 'result' method is needed
    #     to satisfy the interface of 'search.Problem'.
    #
    #     You are allowed (and encouraged) to use auxiliary functions and classes

    
    def __init__(self, warehouse):
        raise NotImplementedError()

    def actions(self, state):
        """
        Return the list of actions that can be executed in the given state.
        
        """
        raise NotImplementedError

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def check_elem_action_seq(warehouse, action_seq):
    '''
    
    Determine if the sequence of actions listed in 'action_seq' is legal or not.
    
    Important notes:
      - a legal sequence of actions does not necessarily solve the puzzle.
      - an action is legal even if it pushes a box onto a taboo cell.
        
    @param warehouse: a valid Warehouse object

    @param action_seq: a sequence of legal actions.
           For example, ['Left', 'Down', Down','Right', 'Up', 'Down']
           
    @return
        The string 'Impossible', if one of the action was not valid.
           For example, if the agent tries to push two boxes at the same time,
                        or push a box into a wall.
        Otherwise, if all actions were successful, return                 
               A string representing the state of the puzzle after applying
               the sequence of actions.  This must be the same string as the
               string returned by the method  Warehouse.__str__()
    '''
    
    '''
    ALGORITHM DRAFT

    For each action:
        1. If there is a wall in the direction of action, return 'Impossible'.
        2. If there is a box in the direction of action, move to case 1. Otherwise, move to case 2
    - CASE 1: agent push a box 
        3. If there is NOT an empty space after the box (i.e., not another box or wall) in the direction of action, return 'Impossible'.
        4. Move box and agent in the direction of action. (Remember to place an empty space in the agent's previous location. i.e. Make sure we don't duplicate box or agent)
    - CASE 2: agent does not push any box
        3. If there is NOT an empty space in the direction of action, return 'Impossible'
        4. Move Agent in the direction of action. (Remember to place an empty space in the agent's previous location. i.e. Make sure we don't duplicate agent)

    After finsishing action-seq, return the warehouse state as a 'string'

    '''
    ##         "INSERT YOUR CODE HERE"
    
    raise NotImplementedError()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def solve_weighted_sokoban(warehouse):
    '''
    This function analyses the given warehouse.
    It returns the two items. The first item is an action sequence solution. 
    The second item is the total cost of this action sequence.
    
    @param 
     warehouse: a valid Warehouse object

    @return
    
        If puzzle cannot be solved 
            return 'Impossible', None
        
        If a solution was found, 
            return S, C 
            where S is a list of actions that solves
            the given puzzle coded with 'Left', 'Right', 'Up', 'Down'
            For example, ['Left', 'Down', Down','Right', 'Up', 'Down']
            If the puzzle is already in a goal state, simply return []
            C is the total cost of the action sequence C

    '''
    
    raise NotImplementedError()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

