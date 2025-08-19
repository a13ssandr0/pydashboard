::: tablemodule


## Sorting
Rows can be sorted by a single column name, or by a list of column names, in each case you can
choose whether to reverse the sorting order.

- Single column
```yaml
sort: column name
```
- Single column, reverse
```yaml
sort: [column name, True]
```
- Multiple columns
```yaml
sort:
    - column 1
    - column 2
    - column 3
    #...
```
- Multiple columns, reverse
```yaml
sort:
    - [column 1, false]
    - [column 2, true]
    - [column 3, true]
    - column 4         # equals to [column 4, false]
    #...
```