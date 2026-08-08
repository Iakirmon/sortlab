# builtin_timsort

## Jak działa

Opakowanie `a[:] = sorted(a)`, żeby wbudowany Timsort przechodził ten sam kontrakt
i te same pomiary co pozostałe algorytmy.

## Złożoność

- czas: O(n log n) (adaptacyjny)
- pamięć: zależna od implementacji CPython
- stabilny: tak

## Kiedy używać

Zawsze w produkcji Pythona — tu jest linią odniesienia na wykresach.

## Co pokazał pomiar

(uzupełnione po benchmarkach). Liczba porównań jest niemierzalna tooliem `Tracked`
(porównania dzieją się w C).
