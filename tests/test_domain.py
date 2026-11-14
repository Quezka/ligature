

def test_cardinalities_take_exact_numbers():
    from ligature.domain.model import Cardinality
    c = Cardinality.parse("(0, 2)")
    assert str(c) == "(0,2)" and c.many and c.upper == 2 and c.min == 0
    assert Cardinality.parse("1,1") == Cardinality(1, False)
    assert str(Cardinality.parse("(2,5)")) == "(2,5)"
    assert str(Cardinality.parse("(3,N)")) == "(3,N)"
    assert Cardinality.parse("(0,N)") == Cardinality(0, True)
    import pytest
    for bad in ("(3,2)", "(0,0)", "(a,b)", "(-1,N)"):
        with pytest.raises(ValueError):
            Cardinality.parse(bad)
