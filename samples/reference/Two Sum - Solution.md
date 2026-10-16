---
category: "[[Coding Tasks]]"
created: 2026-05-16
parents:
  - "[[Two Sum]]"
tags:
- solution
- sample
---

# Key invariant / idea:
Use a hash map to store each number's index as we iterate. For each element, check if `target - num` is already in the map.

## Optimal Complexity:
Time: O(n), Space: O(n)

## Gotchas:
- Can't use the same index twice — the map check prevents this since we only add `num` after the check.

## Sample Code

```python
def twoSum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
```
