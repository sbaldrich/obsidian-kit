---
category: "[[Techniques]]"
created: 2026-05-16
start: 2026-05-16
tags:
  - review/DSA
  - sample
---

## Overview

A technique for processing subarrays or substrings using two pointers that define a window. The window expands by moving the right pointer and shrinks by moving the left pointer, avoiding nested loops.

## Flashcards

Q: When should you use Sliding Window instead of brute force?
A: When you need to find a contiguous subarray/substring optimizing some constraint — O(n) vs O(n²).

Q: What are the two variants of Sliding Window?
A: **Fixed size** (window size k stays constant) and **Variable size** (window expands/shrinks based on a condition).

## Problems

![[Coding Tasks.base]]
