# Shell sort

## Jak działa

Insertion sort na elementach odległych o `gap`, z malejącą sekwencją odstępów.
`shell_sort_shell` używa `n/2, n/4, …, 1`; `shell_sort_ciura` — sekwencji Ciury.

## Złożoność

Zależy od sekwencji odstępów (między ~n^1.25 a n^1.5 w praktyce). Pamięć O(1),
niestabilny.

## Kiedy używać

Czasem dla średnich n, gdy merge/heapsort są „za ciężkie”, a quicksort niepewny.

## Co pokazał pomiar

(uzupełnione po benchmarkach)
