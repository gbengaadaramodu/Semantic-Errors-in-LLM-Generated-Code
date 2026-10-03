def sort_numbers(numbers: str) -> str:
    num_list = numbers.split()
    num_list.sort(key=lambda x: int(x.replace('zero', '0').replace('one', '1').replace('two', '2').replace('three', '3').replace('four', '4').replace('five', '5').replace('six', '6').replace('seven', '7').replace('eight', '8').replace('nine', '9')))
    return ' '.join(num_list)