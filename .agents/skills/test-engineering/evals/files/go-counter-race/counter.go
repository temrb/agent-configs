package counter

import "runtime"

type Counter struct {
	value int
}

func (c *Counter) Increment() {
	current := c.value
	runtime.Gosched()
	c.value = current + 1
}

func (c *Counter) Value() int {
	return c.value
}
