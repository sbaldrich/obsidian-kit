[[Project Based To Do| >> To Project Tasks]]

# `= date(today)`
> [!swan] Focus
> **This week:** [[Quarterly Review]] · [[Weekly Review]] · [[Top Priorities]]
>
> **Jump to:** [[Projects]] · [[Tasks]] · [[Notes]] · [[Meetings]] · [[Finance]] · [[Health]]

## Today's Events

```base
filters:
  and:
    - category.contains("Events")
    - start == today()
views:
  - type: table
    name: Table
    order:
      - file.name

      - type
    columnSize:
      file.name: 469

```

## Upcoming Important People Dates

![[Home - Upcoming People Dates.base]]

## Recent Notes

![[Home - Created This Week.base]]

