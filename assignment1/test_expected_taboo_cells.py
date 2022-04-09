from os import listdir
from mySokobanSolver import taboo_cells
from sokoban import Warehouse
from time import perf_counter_ns

def compare_taboo_cells(warehouse_file):
    '''
    Compare the computed taboo_cells answer with the expected answer, record
    execution time, and provide feedback to the console.

    Parameters
    ----------
    warehouse_file : str
        Warehouse file path.

    Returns
    -------
    bool
        True if answers match, else False.
    int
        Execution time in nanoseconds.

    '''
    warehouse = Warehouse()
    
    # Try load warehouse
    try:
        warehouse.load_warehouse("./warehouses/" + warehouse_file)
    # If exception raised
    except Exception as e:
        print("\033[1;31m" + warehouse_file, "failed!\033[0;0m Could not load",
              "file -> " + repr(e) + ".")
        return (False, None)
    
    # Get and time answer
    start_time = perf_counter_ns()
    answer = taboo_cells(warehouse)
    execution_time = perf_counter_ns() - start_time
    
    # Open expected answer file
    with open('./expected_taboo_cells/' + warehouse_file, 'r') as file:
        expected_answer = file.read()

    # Characters forbidden from being in the taboo_cells output
    illegal_chars = ['$', '.', '@', '!', '*']

    # If the expected file contains any forbidden characters
    if any(illegal_char in expected_answer for illegal_char in illegal_chars):
        print("\033[1;31m" + warehouse_file, "failed!\033[0;0m The expected",
              "answer file contains illegal characters, it most likely hasn't",
              "been configured yet.")
        return (False, None)

    # If the generated answer matches the expected answer
    if answer == expected_answer:
        print(warehouse_file, "passed!")
        return (True, execution_time)
    
    # Generated and expected answer do not match
    print("\033[1;31m" + warehouse_file, "failed!\n\033[0;0mExpected:\n" + 
          expected_answer + "\nActual:\n" + answer)
    return (False, None)

if __name__ == "__main__":
    warehouse_file_list = listdir("./warehouses")
    
    total_count = len(warehouse_file_list)
    pass_count = 0
    total_execution_time = 0
    
    for warehouse_file in warehouse_file_list:
        result = compare_taboo_cells(warehouse_file)
        
        if result[0]:
            pass_count += 1
            total_execution_time += result[1]
            
    print("\n" + str(pass_count) + "/" + str(total_count), "tests passed. Average execution time:", round(total_execution_time/pass_count/1000, 2), "μs.")