"""

Complete the function marked with "INSERT YOUR CODE HERE"

If you don't know where to start, have a good look at the 
implementation of the sliding puzzle  (file sliding_puzzle.py)

- Define an heuristic for this problem (see hint in lecture slide).
- Compare the performance A* and BFS on this problem. 


Last modified 2022-04-1
by f.maire@qut.edu.au

"""

from  W05_search import Problem, breadth_first_graph_search, astar_graph_search, astar_tree_search

import random, time

class PancakePuzzle(Problem):
    '''
    Pancake puzzle, 
    Stack of n pancakes is represented by a permutation P of range(n).
    P[0] is the size of the pancake at the bottom
    P[n-1] is the size of the pancake at the top
    '''
    default_size = 4
    def __init__(self, initial=None, goal=None):
        # Problem.__init__(self, initial, goal)
        if goal is None:
            self.goal = range(PancakePuzzle.default_size,-1,-1)
        else:
            self.goal = goal
        if initial:
            self.initial = initial
        else:
            self.initial = range(len(self.goal))
            random.shuffle(self.initial)
        assert set(self.initial)==set(self.goal)
        self.initial = tuple(self.initial)
        self.goal = tuple(self.goal)

    def actions(self, state):
        """Return the actions that can be executed in the given
        state.
        """
        return list(range(len(state)))

    def result(self, state, action):
        """Return the state that results from executing the given
        action in the given state. The action must be one of
        self.actions(state).
        Applying action a to state s results in a sequence
        s[:a]+s[-1:a-1:-1]
        """
        assert action in self.actions(state)
        return tuple( list(state[:action])+list(reversed(state[action:])) )

    def print_solution(self, goal_node):
        """
            Shows solution represented by a specific goal node.
            For example, goal node could be obtained by calling 
                goal_node = breadth_first_tree_search(problem)
        """
        # path is list of nodes from initial state (root of the tree)
        # to the goal_node
        path = goal_node.path()
        # print the solution
        print ("Solution takes {0} steps from the initial state".format(len(path)-1))
        print (path[0].state)
        print ("to the goal state")
        print (path[-1].state)
        print ("\nBelow is the sequence of moves\n")
        for node in path:
            if node.action is not None:
                print ("flip at {0}".format(node.action))
            print (node.state)

    def goal_test(self, state):
        """Return True if the state is a goal. The default method compares the
        state to self.goal, as specified in the constructor. Override this
        method if checking against a single self.goal is not enough."""
        return state == self.goal

    def path_cost(self, c, state1, action, state2):
        """Return the cost of a solution path that arrives at state2 from
        state1 via action, assuming cost c to get up to state1. If the problem
        is such that the path doesn't matter, this function will only look at
        state2.  If the path does matter, it will consider c and maybe state1
        and action. The default method costs 1 for every step in the path."""
        return c + 1

    def h(self, n):
        '''
        Heuristic for goal state of the form range(k,-1,1) where k is a positive integer. 
        h(n) = 1 + the index of the largest pancake that is still out of place
        '''
        k = len(n.state)
        assert k == len(self.goal)
        misplaced = [x for i,x in enumerate(n.state) if x!=k-1-i]
        if misplaced:
            # some elements misplaced
            return 1+max(misplaced)
        else:
            return 0


#______________________________________________________________________________
#

if __name__ == "__main__":


##    pp = PancakePuzzle(initial=(0, 4, 1, 2, 6, 5, 3), goal=range(6,-1,-1))
##    print "Initial state : ", pp.initial
##    print "Goal state : ", pp.goal

    pp = PancakePuzzle(initial=(3, 1, 4, 6, 0, 2, 5), goal=range(6,-1,-1))
    t0 = time.time()
##    sol_ts = breadth_first_tree_search(pp) # tree search version
    sol_ts = breadth_first_graph_search(pp)  # graph search version
    t1 = time.time()
    print ('BFS Solver took {:.6f} seconds'.format(t1-t0))
    pp.print_solution(sol_ts)


    print('- '*40)
    pp = PancakePuzzle(initial=(3, 1, 4, 6, 0, 2, 5), goal=range(6,-1,-1))
    t0 = time.time()
    sol_ts = astar_graph_search(pp)  # graph search version
    t1 = time.time()
    print ('A* Solver took {:.6f} seconds'.format(t1-t0))
    pp.print_solution(sol_ts)

