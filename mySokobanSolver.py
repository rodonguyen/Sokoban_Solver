from unittest import main, TestCase
from sokoban import find_2D_iterator, Warehouse
from collections import namedtuple
from itertools import combinations
from search import astar_graph_search, Node, Problem

# The cost to move the worker before considering weights
COST = 1
# Directions for a given action
DIRECTIONS = {'Left' :(-1,0), 'Right':(1,0) , 'Up':(0,-1), 'Down':(0,1)}
# The character representing an empty cell
EMPTY_CHAR = ' '
# The steps that can be taken on a single axis
STEPS = (-1, 1)
# The chatacter representing a taboo cell
TABOO_CHAR = 'X'
# The character representing a wall
WALL_CHAR = '#'
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
    The recursion terminates when a wall is reached. Each is cell is also 
    checked to confirm it is not already in the set of inside cells to prevent 
    unnecessary deep recursions.
    

    Parameters
    ----------
    warehouse : Warehouse
        A Warehouse object with the worker inside the warehouse.
    inside_cells : set {(x, y), ...}, optional
        A set of already identified inside cells. The default is None.
    cell : tuple (x, y), optional
        A cell to check if inside. The default is None.

    Returns
    -------
    inside_cells : set {(x, y), ...}
        The set of identified inside cells.

    '''
    # If called with no inside_cells parameter, initialise inside_cells
    if (inside_cells is None):
        inside_cells = set()
        
    # If called with no cell parameter, initialise cell as worker
    if (cell is None):
        cell = warehouse.worker
    
    # If the cell is a wall, terminate this recursive call and return inside cells
    if (cell in warehouse.walls):
        return inside_cells
    
    inside_cells.add(cell)
    
    # For each direction (left, right, up, down)
    for action, direction in DIRECTIONS.items():
        # The next cell in that direction
        next_cell = (cell[X_INDEX] + direction[X_INDEX], cell[Y_INDEX] + direction[Y_INDEX])
        
        # If not already considered an inside cell, recursively call function
        if next_cell not in inside_cells:
            inside_cells = get_inside_cells(warehouse, inside_cells, next_cell)
            
    return inside_cells

def is_corner(warehouse, cell):
    '''
    Identify if a cell is a corner by checking it has at least one adjacent
    wall on each axis. Call any() on generators for each axis to determine if 
    there's at least one adjacent wall per axis, then AND the results of both
    any() functions.
    

    Parameters
    ----------
    warehouse : Warehouse
        A Warehouse object with the worker inside the warehouse.
    cell : tuple (x, y)
        A cell to check if is corner.

    Returns
    -------
    bool
        True if a cell is a corner, else False.

    '''
    
    wall_neighbour_x = any((cell[X_INDEX] + x, cell[Y_INDEX]) in warehouse.walls for x in STEPS)
    wall_neighbour_y = any((cell[X_INDEX], cell[Y_INDEX] + y) in warehouse.walls for y in STEPS)
    
    return wall_neighbour_x and wall_neighbour_y

def get_corner_cells(warehouse, cells):
    '''
    Identifies all corner cells. Use set comprehension to create set of corners
    where each cell evaluates to true for is_corner().

    Parameters
    ----------
    warehouse : Warehouse
        A Warehouse object with the worker inside the warehouse.
    cells : Iterable ((x, y), ...)
        An iterable of cells to check for corner cells.

    Returns
    -------
    set {(x, y), ...}
        The set of identified corner cells.
    '''

    return {cell for cell in cells if is_corner(warehouse, cell)}

def has_adjacent_wall(warehouse, cell, axis_index):
    '''
    Identify if a cell has at least one adjacent wall along a single axis.

    Parameters
    ----------
    warehouse : Warehouse
        A Warehouse object with the worker inside the warehouse.
    cell : tuple (x, y)
        A cell to check for adjacent walls.
    axis_index : int
        The axis to check for adjacent walls on.

    Returns
    -------
    bool
        True if there is at least one adjacent wall, else False.
    '''
    
    # A mutable form of the cell
    adjacent_cell = list(cell)
    
    # For each direction (negative, positive)
    for direction in STEPS:
        # The next cell in that direction along the axis
        adjacent_cell[axis_index] = cell[axis_index] + direction 
                            
        if tuple(adjacent_cell) in warehouse.walls:
            return True
        
    return False

def get_taboo_cells_between(warehouse, corner, other_corner, shared_axis_index):
    '''
    Identify taboo cells on a shared axis between two corners. Check that each 
    cell isn't a wall, isn't a target and has at least one adjacent wall.
    Starting at the first cell next to the first corner in the 
    direction of the second corner, and finishing at the cell before the second
    corner. If any of the cells fail the criteria, none of the cells between
    are taboo.

    Parameters
    ----------
    warehouse : Warehouse
        A Warehouse object with the worker inside the warehouse.
    corner : tuple (x, y)
        The first corner to check for taboo cells between.
    other_corner : tuple (x, y)
        The first corner to check for taboo cells between.
    shared_axis_index : int
        The axis that both corners share.

    Returns
    -------
    taboo_cells_between : set {(x, y), ...}
        The set of identified taboo cells between the two corners.
    '''
    taboo_cells_between = set()
    
    # Flip axis index i.e. 1 - 0 = 1 & 1 - 1 = 0
    non_shared_axis_index = 1 - shared_axis_index
                    
    relative_distance = other_corner[non_shared_axis_index] - corner[non_shared_axis_index]
                  
    # +/- indication of the direction between corners
    step = relative_distance // abs(relative_distance)
    
    # For each value on the shared axis between the first corner and the second corner    
    for non_shared_axis_value in range(corner[non_shared_axis_index] + step, 
                                       other_corner[non_shared_axis_index], 
                                       step):
        # A mutable form of the cell. Its value cannot be declared explicitly
        # as the ordering (shared_axis_index, non_shared_axis_index) is unknown.
        cell = [0, 0]
        
        cell[shared_axis_index] = corner[shared_axis_index]
        cell[non_shared_axis_index] = non_shared_axis_value
        cell = tuple(cell)
                   
        # If cell isn't a wall and isn't a target, add to set of taboo cells
        if (cell not in warehouse.walls and cell not in warehouse.targets 
            and has_adjacent_wall(warehouse, cell, shared_axis_index)):
            taboo_cells_between.add(cell)
        # Else cell is a wall, target or doesn't have an adjacent wall and 
        # isn't taboo. Previously considered taboo cells are now invalid and no
        # more cells should be considered.
        else:
            taboo_cells_between.clear()
            break
        
    return taboo_cells_between
                    

def get_taboo_cells(warehouse, corner_cells):
    '''
    Identify taboo cells. Create unique pairs of corners and check if either is
    not a target. If a corner isn't a target, add it to the set of taboo cells.
    If both corners are taboo cells and share an axis, also identify the taboo
    cells between them.

    Parameters
    ----------
    warehouse : Warehouse
        A Warehouse object with the worker inside the warehouse.
    corner_cells : iterable ((x, y), ...)
        An iterable of corner cells to check for taboo cells.

    Returns
    -------
    taboo_cells : set {(x, y), ...}
        The set of identified taboo cells.
    '''
    
    taboo_cells = set()
    # Unique combinations of corner pairs
    corner_pairs = combinations(corner_cells, 2)
    
    # For each pair of corners
    for corner, other_corner in corner_pairs:
        # If inside corner isn't a target, add to set of taboo cells
        if corner not in warehouse.targets:
            taboo_cells.add(corner)
            
        # If other inside corner isn't a target, add to set of taboo cells
        if other_corner not in warehouse.targets:
            taboo_cells.add(other_corner)
        
        taboo_cells_between = set()
        
        # If both corners are taboo
        if corner in taboo_cells and other_corner in taboo_cells:
            for shared_axis_index in [X_INDEX, Y_INDEX]:
                # If corners share an axis, identify taboo cells between them
                if corner[shared_axis_index] == other_corner[shared_axis_index]:
                    taboo_cells_between = get_taboo_cells_between(warehouse, 
                                                                  corner, 
                                                                  other_corner, 
                                                                  shared_axis_index)
                    break
                else:
                    continue
        else:
            continue
        
        taboo_cells.update(taboo_cells_between)
    
    return taboo_cells

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
    taboo_cells = get_taboo_cells(warehouse, inside_corner_cells)
    
    row_strings = [str().join([WALL_CHAR if (x, y) in warehouse.walls 
                               else TABOO_CHAR if (x, y) in taboo_cells 
                               else EMPTY_CHAR
                               for x in range(warehouse.ncols)]) 
                   for y in range(warehouse.nrows)]
    
    return "\n".join(row_strings)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def manhattan_distance(cell, other_cell):
    '''
    Calculate the manhattan distance between two cells (|x_1 - x_2| + |y_1 - y_2|). 

    Parameters
    ----------
    cell : tuple (x, y)
        The first cell.
    other_cell : tuple (x, y)
        The second cell.

    Returns
    -------
    int
        The manhattan distance between the two cells.

    '''
    
    distance_x = abs(cell[X_INDEX] - other_cell[X_INDEX])
    distance_y = abs(cell[Y_INDEX] - other_cell[Y_INDEX])
    
    return distance_x + distance_y

class SokobanPuzzle(Problem):
    '''
    An instance of the class 'SokobanPuzzle' represents a Sokoban puzzle.
    An instance contains information about the walls, the targets, the boxes
    and the worker.
    
    '''
    
    def __init__(self, warehouse):
        '''
        

        Parameters
        ----------
        warehouse : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        '''
        self.State = namedtuple("State", ["worker", "boxes"])
        
        initial = self.State(warehouse.worker, tuple(warehouse.boxes))
        goal = self.State(None, tuple(warehouse.targets))
        
        super().__init__(initial, goal)
        
        taboo_cells_string = taboo_cells(warehouse)
        taboo_cells_lines = taboo_cells_string.split(sep = "\n")
        
        self.taboo_cells = set(find_2D_iterator(taboo_cells_lines, "X"))
        self.walls = set(warehouse.walls)
        self.weights = tuple(warehouse.weights)
        
    def actions(self, state):
        '''
        

        Parameters
        ----------
        state : TYPE
            DESCRIPTION.

        Returns
        -------
        actions_list : TYPE
            DESCRIPTION.

        '''
        """
        Return the list of actions that can be executed in the given state.

        """
        
        actions_list = list()      
        x,y = state.worker
        
        for action, direction in DIRECTIONS.items():
            x_next, y_next = x + direction[X_INDEX], y + direction[Y_INDEX]
    
            # If trying to walk into wall
            if (x_next, y_next) in self.walls:
                continue
            # If trying to push a box
            if (x_next, y_next) in state.boxes:
                box_x, box_y = x_next, y_next
                box_x_next, box_y_next = box_x + direction[X_INDEX], box_y + direction[Y_INDEX]
                
                # If trying to push box into a wall, taboo cell or another box
                if ((box_x_next, box_y_next) in self.walls or
                    (box_x_next, box_y_next) in self.taboo_cells or
                    (box_x_next, box_y_next) in state.boxes):
                    continue
                
            actions_list.append(action)
        
        return actions_list
        
    def result(self, state, action):
        '''
        

        Parameters
        ----------
        state : TYPE
            DESCRIPTION.
        action : TYPE
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        '''
        """Return the state that results from executing the given
        action in the given state. The action must be one of
        self.actions(state)."""
        
        x,y = state.worker
        direction = DIRECTIONS[action]
        
        x_next, y_next = x + direction[X_INDEX], y + direction[Y_INDEX]
        boxes_next = list(state.boxes)
        
        # If trying to push a box
        if (x_next, y_next) in state.boxes:
            box_x, box_y = x_next, y_next
            box_x_next, box_y_next = box_x + direction[X_INDEX], box_y + direction[Y_INDEX]
        
            # Update box position
            box_index = state.boxes.index((box_x, box_y))
            boxes_next[box_index] = (box_x_next, box_y_next)  
            
        # Return next state
        return self.State((x_next, y_next), tuple(boxes_next))
        
    def goal_test(self, state):
        '''
        

        Parameters
        ----------
        state : TYPE
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        '''
        """Return True if the state is a goal. The default method compares the
        state to self.goal, as specified in the constructor. Override this
        method if checking against a single self.goal is not enough."""
        
        return set(state.boxes) == set(self.goal.boxes)

    def path_cost(self, c, state1, action, state2):
        '''
        

        Parameters
        ----------
        c : TYPE
            DESCRIPTION.
        state1 : TYPE
            DESCRIPTION.
        action : TYPE
            DESCRIPTION.
        state2 : TYPE
            DESCRIPTION.

        Returns
        -------
        TYPE
            DESCRIPTION.

        '''
        """Return the cost of a solution path that arrives at state2 from
        state1 via action, assuming cost c to get up to state1. If the problem
        is such that the path doesn't matter, this function will only look at
        state2.  If the path does matter, it will consider c and maybe state1
        and action. The default method costs 1 for every step in the path."""
        
        # If a box is moved
        for box_index, (box_before, box_after) in enumerate(zip(state1.boxes, state2.boxes)):
            if box_before != box_after:
                return c + (COST + self.weights[box_index])
        
        # If only the worker moves but not any box
        return c + COST
        
    def h(self, node):
        '''
        Calulate the value of the heuristic for the state of a node. It is the 
        sum of the minimum manhattan distances between each box and the targets. 
        It does not consider if a target already has a box, or if multiple boxes 
        are assigned to the same target.

        Parameters
        ----------
        node : Node
            A node in a search tree.

        Returns
        -------
        int
            The value of the heuristic.

        '''
        
        state = node.state
        
        min_distances_to_targets = (
                # The minimum manhattan distance from the box to a target
                min(distances_to_target 
                    # For each of the manhattan distances from the box to targets
                    for distances_to_target in 
                        # The manhattan distance from the box to the target
                        (manhattan_distance(box, target)
                            # For each target               For each box
                            for target in self.goal.boxes)) for box in state.boxes)

        return sum(min_distances_to_targets)
    

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
               string returned by the method Warehouse.__str__()
    '''

    updated_warehouse = warehouse.copy(boxes = warehouse.boxes.copy(), 
                                       weights = warehouse.weights.copy())
    
    for action in action_seq:
        x,y = updated_warehouse.worker
        direction = DIRECTIONS[action]
        x_next, y_next = x + direction[X_INDEX], y + direction[Y_INDEX]
    
        # If trying to walk into wall
        if (x_next, y_next) in updated_warehouse.walls:
            return 'Impossible'
        # If trying to push a box
        if (x_next, y_next) in updated_warehouse.boxes:
            box_x, box_y = x_next, y_next
            box_x_next, box_y_next = box_x + direction[X_INDEX], box_y + direction[Y_INDEX]
            
            # If trying to push box into a wall or another box
            if ((box_x_next, box_y_next) in updated_warehouse.walls or
                (box_x_next, box_y_next) in updated_warehouse.boxes):
                return 'Impossible'
            
            # Update box position
            box_index = updated_warehouse.boxes.index((box_x, box_y))
            updated_warehouse.boxes[box_index] = (box_x_next, box_y_next)  
            
        # Update worker position
        updated_warehouse.worker = (x_next, y_next)
        
    return updated_warehouse.__str__()
    

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
    
    sokoban_puzzle = SokobanPuzzle(warehouse)
    
    solution_node = astar_graph_search(sokoban_puzzle)
    
    if (solution_node is None or 
        check_elem_action_seq(warehouse, solution_node.solution()) == 'Impossible'):
        return 'Impossible', None
    
    return solution_node.solution(), solution_node.path_cost
    
    
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class TestTabooCells(TestCase):
    '''
    
    '''
    def __init__(self, *args, **kwargs):
        '''
        

        Parameters
        ----------
        *args : TYPE
            DESCRIPTION.
        **kwargs : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        '''
        
        super().__init__(*args, **kwargs)
        
        self.warehouse = Warehouse()
        
        lines = ["###########",
                 "#   @   # #",
                 "#   ##  # #",
                 "#   #  *# #",
                 "#     # # #",
                 "#*  #   # #",
                 "###########"]

    
        self.warehouse.from_lines(lines)
    
    def test_taboo_cells(self):
        '''
        

        Returns
        -------
        None.

        '''
        
        actual = taboo_cells(self.warehouse)
        expected = ("###########\n"
                    "#XXXXXXX# #\n"
                    "#   ##  # #\n"
                    "#   #X  # #\n"
                    "#    X# # #\n"
                    "#  X#XXX# #\n"
                    "###########")
        
        self.assertEqual(actual, expected)
        
class TestSokobanPuzzle(TestCase):
    '''
    
    '''
    def __init__(self, *args, **kwargs):
        '''
        

        Parameters
        ----------
        *args : TYPE
            DESCRIPTION.
        **kwargs : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        '''
        
        super().__init__(*args, **kwargs)
        
        self.warehouse = Warehouse()
        
        # Warehouse_8a
        lines = ["1 99",
                 "    ######    ",
                 " ###      ### ",
                 " #  $ $      #",
                 " # .   @    .#",
                 " ############ "]
        
        self.warehouse.from_lines(lines)
        self.sokoban_puzzle = SokobanPuzzle(self.warehouse)
        
    def test_actions(self):
        '''
        

        Returns
        -------
        None.

        '''
        
        # Initial state (wall on down side of worker)
        state = self.sokoban_puzzle.initial
        
        actual = self.sokoban_puzzle.actions(state)
        expected = ['Left', 'Right', 'Up']
        self.assertEqual(actual, expected)
        
        # Box next to wall on down side of worker
        worker = (5, 2)
        boxes = ((3, 2), (5, 3))
        state = self.sokoban_puzzle.State(worker, boxes)
        
        actual = self.sokoban_puzzle.actions(state)
        expected = ['Left', 'Right', 'Up']
        self.assertEqual(actual, expected)
        
        # Box next to taboo cell on up side, wall on down side of worker
        worker = (5, 3)
        boxes = ((3, 2), (5, 2))
        state = self.sokoban_puzzle.State(worker, boxes)
        
        actual = self.sokoban_puzzle.actions(state)
        expected = ['Left', 'Right']
        self.assertEqual(actual, expected)
        
        # Two boxes together on left side of worker
        worker = (5, 2)
        boxes = ((3, 2), (4, 2))
        state = self.sokoban_puzzle.State(worker, boxes)
        
        actual = self.sokoban_puzzle.actions(state)
        expected = ['Right', 'Up', 'Down']
        self.assertEqual(actual, expected)
        
    def test_result(self):
        '''
        

        Returns
        -------
        None.

        '''
        
        # Moving up fron initial state (nothing on up side of worker) 
        state = self.sokoban_puzzle.initial
        action = 'Up'
        
        actual = self.sokoban_puzzle.result(state, action)
        expected = self.sokoban_puzzle.State((6, 2), state.boxes)
        self.assertEqual(actual, expected)
        
        # Moving up with box on up side of player
        worker = (5, 3)
        boxes = ((3, 2), (5, 2))
        state = self.sokoban_puzzle.State(worker, boxes)
        action = 'Up'
        
        actual = self.sokoban_puzzle.result(state, action)
        expected = self.sokoban_puzzle.State((5, 2), ((3, 2), (5, 1)))
        self.assertEqual(actual, expected)    
        
    def test_goal_test(self):
        '''
        

        Returns
        -------
        None.

        '''
        
        # Initial state (No boxes on targets)
        state = self.sokoban_puzzle.initial
        
        actual = self.sokoban_puzzle.goal_test(state)
        expected = False
        self.assertEqual(actual, expected)
        
        # One box on target
        worker = (3, 3)
        boxes = (self.sokoban_puzzle.goal.boxes[0], (5, 1))
        state = self.sokoban_puzzle.State(worker, boxes)
        
        actual = self.sokoban_puzzle.goal_test(state)
        expected = False
        self.assertEqual(actual, expected)
        
        # Both boxes on target
        worker = (3, 3)
        boxes = self.sokoban_puzzle.goal.boxes
        state = self.sokoban_puzzle.State(worker, boxes)
        
        actual = self.sokoban_puzzle.goal_test(state)
        expected = True
        self.assertEqual(actual, expected)
        
    def test_path_cost(self):
        '''
        

        Returns
        -------
        None.

        '''
        
        # Moving up from initial state (no box pushed)
        c = 0
        state1 = self.sokoban_puzzle.initial
        action = 'Up'
        state2 = self.sokoban_puzzle.State((7, 2), state1.boxes)
        
        actual = self.sokoban_puzzle.path_cost(c, state1, action, state2)
        expected = 1
        self.assertEqual(actual, expected)
        
        # Moving up and pushing a box
        c = 0
        worker1 = (6, 3)
        boxes1 = self.sokoban_puzzle.initial.boxes
        state1 = self.sokoban_puzzle.State(worker1, boxes1)
        action = 'Up'
        worker2 = (7, 2)
        boxes2 = ((3, 2), (5, 1))
        state2 = self.sokoban_puzzle.State(worker2, boxes2)
        
        actual = self.sokoban_puzzle.path_cost(c, state1, action, state2)
        expected = 100
        self.assertEqual(actual, expected)
        
    def test_h(self):
        '''
        

        Returns
        -------
        None.

        '''
        
        # Initial state (No boxes on targets)
        state = self.sokoban_puzzle.initial
        node = Node(state)
        
        actual = self.sokoban_puzzle.h(node)
        expected = 6
        self.assertEqual(actual, expected)
        
        # One box on target
        worker = (3, 3)
        boxes = (self.sokoban_puzzle.goal.boxes[0], (5, 2))
        state = self.sokoban_puzzle.State(worker, boxes)
        node = Node(state)
        
        actual = self.sokoban_puzzle.h(node)
        expected = 4
        self.assertEqual(actual, expected)
        
        # Both boxes on target
        worker = (3, 3)
        boxes = self.sokoban_puzzle.goal.boxes
        state = self.sokoban_puzzle.State(worker, boxes)
        node = Node(state)
        
        actual = self.sokoban_puzzle.h(node)
        expected = 0
        self.assertEqual(actual, expected)
        
class TestCheckElemActionSeq(TestCase):
    '''
    
    '''
    def __init__(self, *args, **kwargs):
        '''
        

        Parameters
        ----------
        *args : TYPE
            DESCRIPTION.
        **kwargs : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        '''
        
        super().__init__(*args, **kwargs)
        
        self.warehouse = Warehouse()
        
        # Warehouse_8a
        lines = ["1 99",
                 "    ######    ",
                 " ###      ### ",
                 " #  $ $      #",
                 " # .   @    .#",
                 " ############ "]
        
        self.warehouse.from_lines(lines)
        
    def test_check_elem_action_seq(self):
        '''
        

        Returns
        -------
        None.

        '''
        
        # Walk
        action_seq = ['Up']
        
        actual = check_elem_action_seq(self.warehouse, action_seq)
        expected = ("   ######    \n"
                    "###      ### \n"
                    "#  $ $@     #\n"
                    "# .        .#\n"
                    "############ ")
        self.assertEqual(actual, expected)
        
        # Push box
        action_seq = ['Up', 'Left']
        
        actual = check_elem_action_seq(self.warehouse, action_seq)
        expected = ("   ######    \n"
                    "###      ### \n"
                    "#  $$@      #\n"
                    "# .        .#\n"
                    "############ ")
        self.assertEqual(actual, expected)
        
        # Walk into wall
        action_seq = ['Down']
        
        actual = check_elem_action_seq(self.warehouse, action_seq)
        expected = 'Impossible'
        self.assertEqual(actual, expected)
        
        # Push box into wall
        action_seq = ['Left', 'Up', 'Up']
        
        actual = check_elem_action_seq(self.warehouse, action_seq)
        expected = 'Impossible'
        self.assertEqual(actual, expected)
        
        # Push box into another box
        action_seq = ['Up', 'Left', 'Left']
        
        actual = check_elem_action_seq(self.warehouse, action_seq)
        expected = 'Impossible'
        self.assertEqual(actual, expected)
        
if __name__ == '__main__':
    main()