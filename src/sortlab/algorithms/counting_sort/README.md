# Counting sort

## Jak działa

Liczy wystąpienia każdej wartości całkowitej, potem wypisuje je w kolejności.
Stabilna wersja wypełnia wynik od końca.

## Złożoność

- czas: O(n + k), gdzie k to zakres kluczy
- pamięć: O(n + k)
- stabilny: tak; comparison_based: nie

## Kiedy używać

Gdy klucze to małe liczby całkowite. Podstawa radixa.

## Co pokazał pomiar

(uzupełnione po benchmarkach) — oczekiwane zero porównań w trybie liczenia.
