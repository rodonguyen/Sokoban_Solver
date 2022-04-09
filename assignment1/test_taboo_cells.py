import unittest
from os import listdir
from mySokobanSolver import taboo_cells
from sokoban import Warehouse
from sys import stdout

FORBIDDEN_CHARS = ['$', '.', '@', '!', '*']
RESET = "\033[0;0m"
YELLOW = "\033[1;33m"

class TestTabooCells(unittest.TestCase):
    pass

def test_generator(answer, expected_answer):
    def test(self):
        self.assertEqual(answer, expected_answer)
        
    return test

if __name__ == "__main__":
    warehouse_file_list = listdir("./warehouses")
    
    for warehouse_file in warehouse_file_list:
        test_name = "test_{}".format(warehouse_file.replace(".txt", ""))
        warehouse = Warehouse()
        
        # Try load warehouse
        try:
            warehouse.load_warehouse("./warehouses/" + warehouse_file)
        except Exception as e:
            print("{}Could not run {}. {}Warehouse file could not be loaded -> {}.".format(YELLOW, test_name, RESET, repr(e)))
            stdout.flush()
            continue
        
        # Get answer from function
        answer = taboo_cells(warehouse)
        
        # Open expected answer file
        with open('./expected_taboo_cells/' + warehouse_file, 'r') as file:
            expected_answer = file.read()
            
        # If the expected answer contains any forbidden characters
        if any(forbidden_char in expected_answer for forbidden_char in FORBIDDEN_CHARS):
            print("{}Could not run {}. {}Expected answer is likely not configured.".format(YELLOW, test_name, RESET))
            stdout.flush()
            continue
        
        test_name = "test_{}".format(warehouse_file.replace(".txt", ""))
        test = test_generator(answer, expected_answer)
        setattr(TestTabooCells, test_name, test)
        
    unittest.main()