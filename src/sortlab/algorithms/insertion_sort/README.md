# Insertion sort

## Jak działa

Buduje posortowany prefiks listy. Dla każdego kolejnego elementu przesuwa większe
elementy w prawo, aż znajdzie miejsce wstawienia. Na wejściu `[4, 2, 5, 1, 3]`:
najpierw wstawia `2` → `[2, 4, 5, 1, 3]`, potem `5` zostaje, potem `1` wędruje na
początek → `[1, 2, 4, 5, 3]`, na końcu `3` ląduje między `2` a `4`.

## Złożoność

- najlepszy: O(n) — już posortowane dane (same porównania, bez przesunięć)
- średni / najgorszy: O(n²)
- pamięć: O(1) dodatkowej
- stabilny: tak

## Kiedy używać

W produkcji rzadko — zwykle tylko dla bardzo małych n albo jako baza Timsorta /
introsorta. Warto pamiętać przy prawie posortowanych danych: wtedy bije wiele
„szybszych” algorytmów.

## Co pokazał pomiar

Na `nearly_sorted`, w całym zakresie n=200…3200, insertion był **~9–15% czasu**
`quick_sort_median3` (np. n=3200: 0.144 ms vs 1.59 ms).
