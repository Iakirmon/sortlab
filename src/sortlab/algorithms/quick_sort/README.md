# Quick sort

## Jak działa

Wybiera pivot, partycjonuje listę na elementy mniejsze i większe, sortuje
rekurencyjnie. Trzy warianty różnią się tylko wyborem pivota: ostatni element,
losowy, mediana z trzech.

## Złożoność

- średni: O(n log n)
- najgorszy: O(n²) — szczególnie `quick_sort_last` na posortowanych danych
- pamięć: O(log n) stosu, in-place względem bufora danych; niestabilny

## Kiedy używać

Domyślny wybór „na szybko”, ale pivot ma znaczenie — ten projekt właśnie to mierzy.

## Co pokazał pomiar

`quick_sort_last` na wejściu `sorted` vs `random`: **9.5× wolniej przy n=200**,
**99× przy n=3200**. Ten sam kod, inny rozkład.
