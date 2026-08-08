# Heap sort

## Jak działa

Buduje kopiec maksymalny, potem wielokrotnie zdejmuje maksimum na koniec tablicy
i naprawia kopiec. Całość in-place.

## Złożoność

- czas: O(n log n) zawsze
- pamięć: O(1), niestabilny

## Kiedy używać

Gdy potrzebny gwarantowany n log n bez dodatkowej pamięci merge sorta.

## Co pokazał pomiar

(uzupełnione po benchmarkach)
