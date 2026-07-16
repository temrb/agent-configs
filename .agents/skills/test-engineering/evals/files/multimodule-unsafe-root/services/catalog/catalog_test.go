package catalog

import "testing"

func TestAvailable(t *testing.T) {
	if !Available() {
		t.Fatal("catalog should be available")
	}
}
