package counter

import "testing"

func TestCounterStartsAtZeroAndIncrements(t *testing.T) {
	var subject Counter
	if subject.Value() != 0 {
		t.Fatalf("initial value = %d", subject.Value())
	}
	subject.Increment()
	if subject.Value() != 1 {
		t.Fatalf("value after increment = %d", subject.Value())
	}
}
