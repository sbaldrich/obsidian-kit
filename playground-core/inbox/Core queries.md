Embedded core search for approaches C and D. Untested: syntax may need tweaks.

## C. Do `[/]` and `[-]` count as todo or done?

The six names below cover every task note. Note which block each task lands in.

All tasks:

```query
task:(Sketch OR Order OR Hire OR Test OR Pot OR Fix)
```

Uncompleted (`task-todo`):

```query
task-todo:(Sketch OR Order OR Hire OR Test OR Pot OR Fix)
```

Completed (`task-done`):

```query
task-done:(Sketch OR Order OR Hire OR Test OR Pot OR Fix)
```

## D. Regex on the checkbox text

In progress, across projects:

```query
/\[\/\] \[\[/
```

In progress, Orchard only:

```query
path:projects/orchard /\[\/\] \[\[/
```

Cancelled, across projects:

```query
/\[-\] \[\[/
```
