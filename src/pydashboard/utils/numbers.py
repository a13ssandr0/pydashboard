def safe_float_cast(str_number):
    try:
        number = float(str_number)
    except ValueError:
        number = float('nan')
    return number
