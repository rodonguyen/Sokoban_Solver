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

from asyncio.windows_events import NULL
import search 
import sokoban
import time
from numpy import array
from scipy.optimize import linear_sum_assignment


# The index of the x-coordinate in a 2D tuple
X_INDEX = 0
# The index of the y-coordinate in a 2D tuple
Y_INDEX = 1
WORKER_INDEX = 0
BOX_INDEX = 1
POSSIBLE_MOVE = {'U':(0,-1), 'D':(0,1), 'L':(-1,0), 'R':(1,0) }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -


def my_team():
    '''
    Return the list of the team members of this assignment submission as a list
    of triplet of the form (student_number, first_name, last_name)
    
    '''
    return [(10210776, 'Mitchell', 'Egan'), (10396489, 'Jaydon', 'Gunzburg'), (10603280, 'Rodo', 'Nguyen')]

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def manhattan_dist(start_cell, end_cell):
    '''
    Finds the manhattan distance from start_cell to end_cell

    Parameters
    ----------
    start_cell : (x, y)
    end_cell : (x, y)

    Returns
    -------
    length
        Length of path from start to end
    '''
    return abs(end_cell[X_INDEX]-start_cell[X_INDEX]) \
         + abs(end_cell[Y_INDEX]-start_cell[Y_INDEX])


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

def get_taboo_cell_coordinates(taboo_cells_string):
    '''
    Return a list of tuple(taboo cells coordinates).
    These coordinates will be used in SokobanPuzzle.actions() 
    to avoid pushing box on them.
    '''
    x = 0
    y = 0
    taboo_cells_coordinates = tuple()

    for i in taboo_cells_string:
        if i == 'X':
            taboo_cells_coordinates += ((x,y),)  # Add 
            x += 1
        elif i == '\n':
            y += 1
            x = 0
        else: 
            x += 1

    return list(taboo_cells_coordinates)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
class SokobanPuzzle(search.Problem):
    '''
    An instance of the class 'SokobanPuzzle' represents a Sokoban puzzle.
    An instance contains information about the walls, the targets, the boxes
    and the worker.

    Your implementation should be fully compatible with the search functions of 
    the provided module 'search.py'. 
    
    '''
    def __init__(self, warehouse):
        self.warehouse = warehouse
        self.taboo_cells = get_taboo_cell_coordinates(taboo_cells(warehouse))
        self.initial = list((warehouse.worker,)) + warehouse.boxes

    def actions(self, state):
        '''
        Return the list of executable/legal actions of the agent 
        in the provided state.

        @params
            state <String> 
                String presentation of a Warehouse object
        @return
            legal_moves <List>
                a List of legal moves for agent
                e.g. ['U', 'D', 'R', 'L'], []
        ------------------------------------------------------------------------
        ALGORITHM DRAFT

        For each action in the sequence:
            1. If there is a wall in the direction of action, return 'Impossible'.
            2. If there is a box in the direction of action, move to case 1. Otherwise, move to case 2
        - CASE 1: agent push a box 
            3. If there is another box / wall / taboo cell after the box in the direction of action, return 'Impossible'.
            4. Move box and agent in the direction of action. (Remember to place an empty space in the agent's previous location. i.e. Make sure we don't duplicate box or agent)
        - CASE 2: agent does not push any box
            3. If there is NOT an empty space in the direction of action, return 'Impossible'
            4. Move Agent in the direction of action. (Remember to place an empty space in the agent's previous location. i.e. Make sure we don't duplicate agent)
        '''
        legal_moves = []
        # up    = ( 0 , -1,  'U')
        # down  = ( 0 ,  1,  'D')
        # left  = (-1 ,  0,  'L')
        # right = ( 1 ,  0,  'R')
        possible_moves = {'U':(0,-1), 'D':(0,1), 'L':(-1,0), 'R':(1,0) }
        x, y = state[WORKER_INDEX]

        for move in possible_moves.values():
            x_next, y_next = x + move[X_INDEX], y + move[Y_INDEX]
            
            # Wall
            if (x_next, y_next) in self.warehouse.walls: continue
            # Box
            elif (x_next, y_next) in state[BOX_INDEX:]:
                x_2_next, y_2_next = x + move[X_INDEX]*2, y + move[Y_INDEX]*2
                # Another box / wall / taboo cells after box
                if (x_2_next, y_2_next) in (list(state[BOX_INDEX]) + self.warehouse.walls + self.taboo_cells):
                    continue 
            # Empty space / Worker can move the box
            legal_moves += move
        return legal_moves

            #     # Empty space after box
            #     box_index = self.warehouse.boxes.index((x_next, y_next))
            #     self.warehouse.boxes[box_index] = (x_2_next, y_2_next)
            
            # # Empty space / Worker can move
            # self.warehouse.worker = (x_next, y_next)
    
    def result(self, state, action):
        """
        Return the state after executing 'action' from the given 'state'
        """
        # assert action in self.actions(state)

        possible_moves = {'U':(0,-1), 'D':(0,1), 'L':(-1,0), 'R':(1,0) }
        move = possible_moves[action]
        x, y = state[WORKER_INDEX]
        x_next, y_next = x + move[X_INDEX], y + move[Y_INDEX]
        
        # Move box if applicable
        if (x_next, y_next) in state[BOX_INDEX]:
            x_2_next, y_2_next = x + move[X_INDEX]*2, y + move[Y_INDEX]*2
            box_index = state.index((x_next, y_next))
            state[box_index] = (x_2_next, y_2_next)
        
        # Move worker
        state[WORKER_INDEX] = (x_next, y_next)

        return state

    def goal_test(self, state):
        '''
        Return True if the provided 'state' is a goal.
        '''
        return set(state[1:]) == set(self.warehouse.targets)


    def path_cost(self, cost, state1, action, state2): # can change the params
        '''
        Return the cost of a solution path that arrives at state2
        from state1 via action + 'cost' (from beginning to get to state 1). 

        If the problem is such that the path doesn't matter, 
        this function will only look at state2.  
        If the path does matter, it will consider c and maybe state1
        and action.
        '''
        
        #####################
        # CODE to be filled #
        #####################

        raise NotImplementedError

    def h(self, node):
        """
        Heuristic function for the Sokoban puzzle.......
        """
        # Will need to be refactored to suit the format of the state, assuming
        # here a tuple containing the player (0) & the list of boxes (1)
        cost_matrix = []
        boxes = node.state[1]
        
        for box, weight in zip(boxes, warehouse.weights):    
            cost_row = []
            for target in warehouse.targets:
                cost = manhattan_dist(box, target) * (weight + 1)
                cost_row.append(cost)
            cost_matrix.append(cost_row)
            
        cost_matrix = array(cost_matrix)
        boxes, targets = linear_sum_assignment(cost_matrix)
        return cost_matrix[boxes, targets].sum()


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
               string returned by the method  Warehouse.__str__() #important
    
    ----------------------------------------------------------
    ALGORITHM DRAFT

    For each action in the sequence:
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

    #####################
    # CODE to be filled #
    #####################
    state = NULL
    return state


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
    
    #####################
    # CODE to be filled #
    #####################

    raise NotImplementedError()


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

if __name__ == "__main__":

    warehouse = sokoban.Warehouse()
    w = "warehouses/warehouse_39.txt"               # Change warehouse here
    warehouse.load_warehouse(w)
    sokobanPuzzle = SokobanPuzzle(warehouse)

    # Test output format of warehouse attributes
    print(warehouse.boxes)
    print(warehouse.worker)
    print(sokobanPuzzle.initial)
    print(sokobanPuzzle.warehouse.targets)
    print(warehouse.boxes + warehouse.walls)

    # Test get_taboo_cell_coordinates()
    print(warehouse)
    taboo_cells_str = taboo_cells(warehouse)
    print(taboo_cells_str)
    coords = get_taboo_cell_coordinates(taboo_cells_str)
    print(coords)
    print(warehouse.walls + coords)
    print((3,7) in coords)

    
    # t0 = time.time()
    # solution = search.astar_graph_search(sokobanPuzzle)
    # t1 = time.time()
    # sokobanPuzzle.print_solution(solution)
    # print ("Solver took ",t1-t0, ' seconds')









































"""
+ + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + 
                             CODE CEMETARY
+ + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + + 

class SokobanPuzzle(search.Problem):
    '''
    An instance of the class 'SokobanPuzzle' represents a Sokoban puzzle.
    An instance contains information about the walls, the targets, the boxes
    and the worker.

    Your implementation should be fully compatible with the search functions of 
    the provided module 'search.py'. 
    
    '''
    def __init__(self, warehouse):
        self.warehouse = warehouse
        self.taboo_cells = get_taboo_cell_coordinates(taboo_cells(warehouse))
        self.initial = list((warehouse.worker,)) + warehouse.boxes

    def actions(self, state):
        '''
        Return the list of executable/legal actions of the agent 
        in the provided state.

        @params
            state <String> 
                String presentation of a Warehouse object
        @return
            legal_moves <List>
                a List of legal moves for agent
                e.g. ['U', 'D', 'R', 'L'], []
        ------------------------------------------------------------------------
        ALGORITHM DRAFT

        For each action in the sequence:
            1. If there is a wall in the direction of action, return 'Impossible'.
            2. If there is a box in the direction of action, move to case 1. Otherwise, move to case 2
        - CASE 1: agent push a box 
            3. If there is NOT an empty space after the box (i.e., not another box or wall) in the direction of action, return 'Impossible'.
            4. Move box and agent in the direction of action. (Remember to place an empty space in the agent's previous location. i.e. Make sure we don't duplicate box or agent)
        - CASE 2: agent does not push any box
            3. If there is NOT an empty space in the direction of action, return 'Impossible'
            4. Move Agent in the direction of action. (Remember to place an empty space in the agent's previous location. i.e. Make sure we don't duplicate agent)
        '''

        agent_position = self.find(state, 'agent')
        if agent_position == -1:
            raise Exception('Agent is not found in state! Your warehouse look like this:\b {0}'.format(state))

        legal_moves = []
        up    = ( 0 , -1,  'U')
        down  = ( 0 ,  1,  'D')
        left  = (-1 ,  0,  'L')
        right = ( 1 ,  0,  'R')
        possible_moves = [up, down, left, right]

    
        for move in possible_moves:
            print(self.identify(state, agent_position[X_INDEX] + move[X_INDEX], 
                                    agent_position[Y_INDEX] + move[Y_INDEX]))

            # Empty space
            if self.identify(state, agent_position[X_INDEX] + move[X_INDEX], 
                                    agent_position[Y_INDEX] + move[Y_INDEX]) in [' ', '.']:
                legal_moves.append(move[2])
                continue

            # Wall
            if self.identify(state, agent_position[X_INDEX] + move[X_INDEX], 
                                    agent_position[Y_INDEX] + move[Y_INDEX]) == '#':
                continue

            # Box
            if self.identify(state, agent_position[X_INDEX] + move[X_INDEX], 
                                    agent_position[Y_INDEX] + move[Y_INDEX]) in ['*', '$']:
                # Box and Wall
                if self.identify(state, agent_position[X_INDEX] + move[X_INDEX] * 2, 
                                        agent_position[Y_INDEX] + move[Y_INDEX] * 2) in ['*', '$', '#']:
                    continue
                # Empty space
                elif self.identify(state, agent_position[X_INDEX] + move[X_INDEX] * 2, 
                                        agent_position[Y_INDEX] + move[Y_INDEX] * 2) in [' ', '.']:
                    legal_moves.append(move[2])
        return legal_moves


--------------------------------------
        Possible path_cost value (Rodo):
            cost + len(actions)*box_weight 
            (there may be many phases where part of 'action' 
            is pushing different boxes with different weights)


--------------------------------------

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
               string returned by the method  Warehouse.__str__() #important
    
    ----------------------------------------------------------
    ALGORITHM DRAFT

    For each action in the sequence:
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
    state = str(warehouse)
    
    for step in action_seq:
        legal_actions = SokobanPuzzle.actions(state)
        if step in legal_actions:
            next_state = SokobanPuzzle.result(state, step)
            state = next_state
        else: 
            return 'Impossible'

    # Update 'warehouse' Object        
    warehouse = warehouse.from_string(state)
    return state

--------------------------------------
    def find(self, state, object):
        '''
        Find the object and return its coordinates e.g. (2,4)
        @params
            state <String> 
                String presentation of a Warehouse object
            object <String>
                The object you want to locate

        @return
            location <tuple>
                The location of the object in (x,y)
                Or return -1 if not found

        '''

        # Replace object with possible symbols
        if object == 'agent':
            objects = ['@', '!'] 
        else:
            raise Exception('Invalid object. Input object = {0}'.format(object))
                

        lines = state.split('\n')
        for o in objects:
            for y, line in enumerate(lines):
                if line.find(o) != -1:
                    return(line.find(o), y)  # Found and return position
        
        return -1  # Can not found object in state / str(warehouse)

    def identify(self, state, x, y):
        '''
        Return the object at the provided coordinates 'x' and 'y' in 'state'. Return -1 if the coordinates if outside of the warehouse state.
        @params
            state <String> 
                String presentation of a Warehouse object
            x <Integer>
                x coordinate
            y <Integer>
                y coordinate
            
        @return
            object <String>
                The object found at (x,y)
                Or return -1 if coordinates is outside of the warehouse state.

        '''
        lines = state.split('\n')
        try:
            object = lines[y][x]
        except:
            object = -1
        return object

    def replace(self, state, x, y, new_object):
        '''
        Return the state with new_object at the provided coordinates 'x' and 'y' in 'state'. Return -1 if the coordinates if outside of the warehouse state.
        @params
            state <String> 
                String presentation of a Warehouse object
            x <Integer>
                x coordinate
            y <Integer>
                y coordinate
            new_object <String>
                a symbol of the object in warehouse you want to replace (x,y)
            
        @return
            next_state <String>
                A new state of the warehouse object with (x,y) char 
                replaced by new_object
        '''

        lines = state.split('\n')
        temp_list = list(lines[y])
        temp_list[x] = new_object 
        lines[y] = ''.join(temp_list)
        # lines[y][x] = new_object
        next_state = '\n'.join(lines)

        return next_state


--------------------------------------







--------------------------------------



"""