## 2024-05-23 - In-place String Concatenation vs Join
**Learning:** In CPython, simple string concatenation `s += t` in a loop can be faster than `" ".join(...)` for simple cases, because CPython optimizes `+=` to happen in-place when the LHS variable has a reference count of 1.
**Action:** Always benchmark "obvious" string optimizations in Python before applying them. Don't assume `join` is always faster than `+=` for flat loops.
