from collections import namedtuple
from itertools import combinations
from search import astar_graph_search, astar_tree_search, Node, Problem
from sokoban import find_2D_iterator, Warehouse
from unittest import main, TestCase

# The characters representing empty, taboo and wall cells
CELL_CHARS = {'Empty':' ', 'Taboo':'X', 'Wall':'#'}
# The cost to move the worker before considering weights
COST = 1
# Directions for a given action
DIRECTIONS = {'Left':(-1,0), 'Right':(1,0), 'Up':(0,-1), 'Down':(0,1)}
# Indexes of the x- & y-coordinate in a 2D tuple
INDEXES = {'x':0, 'y':1}
# The steps that can be taken on a single axis
STEPS = {'Negative':-1, 'Positive':1}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def my_team():
    '''
    Return the list of the team members of this assignment submission as a list
    of triplet of the form (student_number, first_name, last_name)
    
    '''
    return [(10210776, 'Mitchell', 'Egan'), 
            (10396489, 'Jaydon', 'Gunzburg'), 
            (10603280, 'Rodo', 'Nguyen')]

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
    for _, direction in DIRECTIONS.items():
        # The next cell in that direction
        next_cell = (cell[INDEXES['x']] + direction[INDEXES['x']], 
                     cell[INDEXES['y']] + direction[INDEXES['y']])
        
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
    
    wall_neighbour_x = any((cell[INDEXES['x']] + step, cell[INDEXES['y']]) 
                           in warehouse.walls for _, step in STEPS.items())
    wall_neighbour_y = any((cell[INDEXES['x']], cell[INDEXES['y']] + step) 
                           in warehouse.walls for _, step in STEPS.items())
    
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
    for _, step in STEPS.items():
        # The next cell in that direction along the axis
        adjacent_cell[axis_index] = cell[axis_index] + step 
                            
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
        # as the ordering (shared_axis_index, non_shared_axis_index) is unknown
        cell = [0, 0]
        
        cell[shared_axis_index] = corner[shared_axis_index]
        cell[non_shared_axis_index] = non_shared_axis_value
        cell = tuple(cell)
                   
        # If cell isn't a wall, isn't a target and has at least one adjacent 
        # wall, add to set of taboo cells
        if (cell not in warehouse.walls 
            and cell not in warehouse.targets 
            and has_adjacent_wall(warehouse, cell, shared_axis_index)):
            taboo_cells_between.add(cell)
        # Else cell is a wall, target or doesn't have an adjacent wall and 
        # isn't taboo. Previously considered taboo cells are now invalid and no
        # more cells should be considered
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
            for shared_axis_index in [INDEXES['x'], INDEXES['y']]:
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
    
    row_strings = [str().join([CELL_CHARS['Wall'] if (x, y) in warehouse.walls 
                               else CELL_CHARS['Taboo'] if (x, y) in taboo_cells 
                               else CELL_CHARS['Empty']
                               for x in range(warehouse.ncols)]) 
                   for y in range(warehouse.nrows)]
    
    return "\n".join(row_strings)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def manhattan_distance(cell, other_cell):
    '''
    Determine the manhattan distance between two cells (|x_1 - x_2| + |y_1 - y_2|). 

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
    
    distance_x = abs(cell[INDEXES['x']] - other_cell[INDEXES['x']])
    distance_y = abs(cell[INDEXES['y']] - other_cell[INDEXES['y']])
    
    return distance_x + distance_y

class SokobanPuzzle(Problem):
    '''
    An instance of the class 'SokobanPuzzle' represents a Sokoban puzzle.
    
    State : namedtuple (worker: (x, y), boxes: ((x, y), ...))
        Tuple subclass to instantiate puzzle states.
        
    initial : State (worker: (x, y), boxes: ((x, y), ...))
        The initial state of the puzzle.
        
    goal : State (worker: (x, y), boxes: ((x, y), ...))
        The goal state of the puzzle, the worker position is irrelevant.
        
    taboo_cells : set {(x, y), ...}
        The set of taboo cell coordinates.
        
    walls : set {(x, y), ...}
        The set of wall cell coordinates.
        
    weights : tuple ((x, y), ...)
        A tuple of box weights.
    '''
    
    def __init__(self, warehouse):
        '''
        Construct subclass by calling the constructor of the base class with
        the initial & goal state, then store the box weights and the 
        coordinates of taboo cells & walls as attributes.

        Parameters
        ----------
        warehouse : Warehouse
            A Warehouse object with the worker inside the warehouse.

        Returns
        -------
        None.
        '''
        # Create tuple subclass to instantiate puzzle states
        self.State = namedtuple("State", ["worker", "boxes"])
        
        initial = self.State(warehouse.worker, tuple(warehouse.boxes))
        goal = self.State(None, tuple(warehouse.targets))
        
        # Call base class constructor with the initial and goal state
        super().__init__(initial, goal)
        
        # Get taboo cell coordinates from warehouse string
        taboo_cells_string = taboo_cells(warehouse)
        taboo_cells_lines = taboo_cells_string.split(sep = "\n")
        self.taboo_cells = set(find_2D_iterator(taboo_cells_lines, CELL_CHARS['Taboo']))
        
        self.walls = set(warehouse.walls)
        self.weights = tuple(warehouse.weights)
        
    def actions(self, state):
        '''
        Identify which actions can be performed in the provided state. For each
        possible direction, ensure the player isn't walking into a wall, then 
        if they are pushing a box - ensure the box isn't being pushed into a 
        wall, taboo cell or another box.

        Parameters
        ----------
        state : State (worker: (x, y), boxes: ((x, y), ...))
            The state of the puzzle.

        Returns
        -------
        actions_list : list ['action', ...]
            The list of possible actions as strings.
        '''
        
        actions_list = list()      
        x,y = state.worker
        
        # For each action string and its corresponding direction
        for action, direction in DIRECTIONS.items():
            x_next, y_next = x + direction[INDEXES['x']], y + direction[INDEXES['y']]
    
            # If trying to walk into wall, forbidden action - continue
            if (x_next, y_next) in self.walls:
                continue
            # If trying to push a box, check if push is valid
            if (x_next, y_next) in state.boxes:
                box_x, box_y = x_next, y_next
                box_x_next = box_x + direction[INDEXES['x']]
                box_y_next = box_y + direction[INDEXES['y']]
                
                # If trying to push box into a wall, taboo cell or another box, 
                # forbidden action - continue
                if any((box_x_next, box_y_next) in forbidden_pushes 
                       for forbidden_pushes in (self.walls, 
                                               self.taboo_cells, 
                                               state.boxes)):
                    continue

            actions_list.append(action)
        
        return actions_list
        
    def result(self, state, action):
        '''
        Determine the state which results from the provided action being 
        performed in the provided state. First identify the direction of the
        action, then update the worker coordinate, and if pushing a box update 
        the box coordinate accordingly.

        Parameters
        ----------
        state : State (worker: (x, y), boxes: ((x, y), ...))
            The state of the puzzle.
        action : string
            The action to perform. It is a precondition that this is one of the 
            actions returned by self.actions(state).

        Returns
        -------
        State (worker: (x, y), boxes: ((x, y), ...))
            The state of the puzzle after performing the action.
        '''
        
        x,y = state.worker
        direction = DIRECTIONS[action]
        
        # Get next worker position
        x_next, y_next = x + direction[INDEXES['x']], y + direction[INDEXES['y']]
        
        # A mutable form of the state's boxes
        boxes_next = list(state.boxes)
        
        # If trying to push a box, get next box position
        if (x_next, y_next) in state.boxes:
            box_x, box_y = x_next, y_next
            box_x_next = box_x + direction[INDEXES['x']]
            box_y_next = box_y + direction[INDEXES['y']]
           
            box_index = state.boxes.index((box_x, box_y))
            boxes_next[box_index] = (box_x_next, box_y_next)  
            
        # Return next state
        return self.State((x_next, y_next), tuple(boxes_next))
        
    def goal_test(self, state):
        '''
        Determine if the provided state is the goal state. Check if the set 
        (note that it is unordered) of state boxes is equal to the set of goal 
        boxes. The position of the worker is irrelevant.

        Parameters
        ----------
        state : State (worker: (x, y), boxes: ((x, y), ...))
            The state of the puzzle.

        Returns
        -------
        bool
            True if the state is the goal state, else False.
        '''
        
        return set(state.boxes) == set(self.goal.boxes)

    def path_cost(self, c, state1, action, state2):
        '''
        Determine the cost of the path taken after arriving at state2 from
        state1. The action is irrelevant. First determine if a box has been 
        moved. If not, add the base movement cost to the cost-upto state1 (c). 
        If a box has been moved, add the base movement-cost and the weight of 
        the moved box to to the cost-upto state1.

        Parameters
        ----------
        c : int
            The summative cost upto state1.
        state1 : State (worker: (x, y), boxes: ((x, y), ...))
            The first state of the puzzle.
        state2 : State (worker: (x, y), boxes: ((x, y), ...))
            The second state of the puzzle.

        Returns
        -------
        int
            The summative cost upto state2.

        '''
        
        # For each box (its position before & after) and its corresponding index
        for box_index, (box_before, box_after) in enumerate(zip(state1.boxes, state2.boxes)):
            # If the box has moved
            if box_before != box_after:
                return c + (COST + self.weights[box_index])
        
        
        return c + COST
        
    def h(self, node):
        '''
        Calulate the value of the heuristic for the state of a node. It is the 
        sum of the minimum manhattan distances (multiplied by the base cost 
        plus the box weight) between each box and the targets. It does not 
        consider if a target already has a box, or if multiple boxes are 
        assigned to the same target.

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
                # The minimum distance
                min(distances_to_target 
                    # For each of the distances
                    for distances_to_target in 
                        # The manhattan distance (multiplied by the base cost 
                        # plus the box weight) from the box to the target
                        (manhattan_distance(box, target) * (weight + COST)
                            # For each target               
                            for target in self.goal.boxes)) 
                # For each box and its corresponding weight
                for box, weight in zip(state.boxes, self.weights))

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
    
    # Copy the warehouse so that it can be updated without referencing the 
    # original state
    updated_warehouse = warehouse.copy(boxes = warehouse.boxes.copy(), 
                                       weights = warehouse.weights.copy())
    
    # For each action, check if action is possible
    for action in action_seq:
        x,y = updated_warehouse.worker
        direction = DIRECTIONS[action]
        x_next, y_next = x + direction[INDEXES['x']], y + direction[INDEXES['y']]
    
        # If trying to walk into wall, impossible action
        if (x_next, y_next) in updated_warehouse.walls:
            return 'Impossible'
        # If trying to push a box, check if push is possible
        if (x_next, y_next) in updated_warehouse.boxes:
            box_x, box_y = x_next, y_next
            box_x_next, box_y_next = box_x + direction[INDEXES['x']], box_y + direction[INDEXES['y']]
            
            # If trying to push box into a wall or another box, impossible action
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
    
    ### Choosing one of the 2: Graph / Tree
    solution_node = astar_graph_search(sokoban_puzzle)
    # solution_node = astar_tree_search(sokoban_puzzle)
    
    # If no solution is found or solution contains an impossible action, 
    # indicate impossible
    if (solution_node is None or 
        check_elem_action_seq(warehouse, solution_node.solution()) == 'Impossible'):
        return 'Impossible', None
    
    return solution_node.solution(), solution_node.path_cost
    
    
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

class TestTabooCells(TestCase):
    '''
    TestCase subclass for testing the taboo_cells function.
    '''
    
    def __init__(self, *args, **kwargs):
        '''
        Initialise the test class by constructing a warehouse which contains 
        all possible scenarios for classifying taboo cells and non-taboo cells.
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
        Assert that the answer returned from taboo_cells matches that which was
        manually determined.
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
    TestCase subclass for testing the methods in the SokobanPuzzle class.
    '''
    
    def __init__(self, *args, **kwargs):
        '''
        Initialise the test class by constructing warehouse_8a and 
        instantiating the SokobanPuzzle class with it.
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
        Assert that the answers returned from sokoban_puzzle.actions matches 
        those which were manually determined. There are multiple asserts for 
        each of the possible conditions.
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
        Assert that the answers returned from sokoban_puzzle.result matches 
        those which were manually determined. There are multiple asserts for 
        each of the possible conditions.
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
        Assert that the answers returned from sokoban_puzzle.goal_test matches 
        those which were manually determined. There are multiple asserts for 
        each of the possible conditions.
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
        Assert that the answers returned from sokoban_puzzle.path_cost matches 
        those which were manually determined. There are multiple asserts for 
        each of the possible conditions.
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
        Assert that the answers returned from sokoban_puzzle.h matches those 
        which were manually determined. There are multiple asserts for each of
        the possible conditions.
        '''
        
        # Initial state (No boxes on targets)
        state = self.sokoban_puzzle.initial
        node = Node(state)
        
        actual = self.sokoban_puzzle.h(node)
        expected = 404
        self.assertEqual(actual, expected)
        
        # One box on target
        worker = (3, 3)
        boxes = (self.sokoban_puzzle.goal.boxes[0], (5, 2))
        state = self.sokoban_puzzle.State(worker, boxes)
        node = Node(state)
        
        actual = self.sokoban_puzzle.h(node)
        expected = 400
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
    TestCase subclass for testing the check_elem_action_seq function.
    '''
    
    def __init__(self, *args, **kwargs):
        '''
        Initialise the test class by constructing warehouse_8a.
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
        Assert that the answers returned from check_elem_action_seq matches
        those which were manually determined. There are multiple asserts for 
        each of the possible conditions.
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
        
class TestSolveWeightedSokoban(TestCase):
    '''
    TestCase subclass for testing the solve_weighted_sokoban function.
    '''

    def __init__(self, *args, **kwargs):
        '''
        Initialise the test class by constructing warehouse_8a.
        '''
        
        super().__init__(*args, **kwargs)
        
        self.solvable_warehouse = Warehouse()
        self.impossible_warehouse = Warehouse()
        
        # Warehouse_09
        solvable_lines = ["3 87",
                          " ##### ",
                          " #.  ##",
                          " #@$$ #",
                          " ##   #",
                          "  ##  #",
                          "   ##.#",
                          "    ###"]
        
        # Warehouse_5n
        impossible_lines = ["  #### #### ",
                            " ##  ###  ##",
                            " #   # #   #",
                            " #  *. .*  #",
                            " ###$   $###",
                            "  #   @   # ",
                            " ###########"]
        
        self.solvable_warehouse.from_lines(solvable_lines)
        self.impossible_warehouse.from_lines(impossible_lines)
        
    def test_solve_weighted_sokoban(self):
        '''
        Assert that the answers returned from solve_weighted_sokoban matches
        those which were calculated by Fred's solver. There are multiple asserts 
        for each of the possible conditions.
        '''
        
        # Solvable, cost from spec
        _, actual = solve_weighted_sokoban(self.solvable_warehouse)
        expected = 396
        self.assertEqual(actual, expected)
        
        # Impossible, cost from spec
        _, actual = solve_weighted_sokoban(self.impossible_warehouse)
        expected = None
        
if __name__ == '__main__':
    main()