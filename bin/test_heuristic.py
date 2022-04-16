from mySokobanSolver import manhattan_dist
from sokoban import Warehouse
from scipy.optimize import linear_sum_assignment
from numpy import array

if __name__ == "__main__":
    warehouse = Warehouse()
    warehouse.load_warehouse("./warehouses/warehouse_01_a.txt")
    
    cost_matrix = []
    
    for box, weight in zip(warehouse.boxes, warehouse.weights):    
        cost_row = []
        for target in warehouse.targets:
            cost = manhattan_dist(box, target) * (weight + 1)
            cost_row.append(cost)
            
        cost_matrix.append(cost_row)
        
    cost_matrix = array(cost_matrix)
        
    boxes, targets = linear_sum_assignment(cost_matrix)
    
    cost_matrix[boxes, targets].sum()
    
    print(boxes)
    print(targets)
    print(cost_matrix[boxes, targets].sum())