import unittest
from os import listdir
from mySokobanSolver import taboo_cells
from sokoban import Warehouse
from sys import stdout

FORBIDDEN_CHARS = ['$', '.', '@', '!', '*']

warehouse_file_list = listdir("./warehouses")

class TestTabooCells(unittest.TestCase):
    def test_taboo_cells(self):
        for warehouse_file in warehouse_file_list:
            warehouse = Warehouse()
            
            # Try load warehouse
            try:
                warehouse.load_warehouse("./warehouses/" + warehouse_file)
            except Exception as e:
                print("Could not run test_taboo_cells subtest for {}. Warehouse file could not be loaded -> {}.".format(warehouse_file.replace(".txt", ""), repr(e)))
                stdout.flush()
                continue
            
            # Get answer from function
            answer = taboo_cells(warehouse)
            
            # Open expected answer file
            with open('./taboo_cells_expected/' + warehouse_file, 'r') as file:
                expected_answer = file.read()
                
            forbidden_char = ''
            # If the expected answer contains any forbidden characters
            if any(forbidden_char in expected_answer for forbidden_char in FORBIDDEN_CHARS):
                print(forbidden_char)
                print("Could not run test_taboo_cells subtest for {}. Expected answer is likely not configured.".format(warehouse_file.replace(".txt", "")))
                stdout.flush()
                continue
            
            with self.subTest():
                self.assertEqual(answer, expected_answer)
                
if __name__ == "__main__":
    unittest.main()