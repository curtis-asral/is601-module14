from app.models.calculation import Calculation, Addition, Subtraction, Multiplication, Division

def test_addition():
    calc = Addition(inputs=[1,2,3])
    assert calc.get_result() == 6

def test_subtraction():
    calc = Subtraction(inputs=[5,2,1])
    assert calc.get_result() == 2

def test_multiplication():
    calc = Multiplication(inputs=[2,3,4])
    assert calc.get_result() == 24

def test_division():
    calc = Division(inputs=[8,2,2])
    assert calc.get_result() == 2

def test_factory():
    calc = Calculation.create("addition", 1, [1,2])
    assert isinstance(calc, Addition)
    calc = Calculation.create("subtraction", 1, [5,2])
    assert isinstance(calc, Subtraction)
    calc = Calculation.create("multiplication", 1, [2,3])
    assert isinstance(calc, Multiplication)
    calc = Calculation.create("division", 1, [8,2])
    assert isinstance(calc, Division)

def test_division_by_zero():
    calc = Division(inputs=[8,0])
    try:
        calc.get_result()
        assert False
    except ValueError:
        assert True
