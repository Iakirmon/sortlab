# Bubble sort

## Jak działa

Wielokrotnie przechodzi po liście i zamienia sąsiednie elementy, gdy są w złej
kolejności. Po i-tym przebiegu i największych wartości jest na końcu. Wariant
`bubble_sort_early_exit` kończy pracę, gdy przebieg nie wykona żadnej zamiany.

Przykład `[4, 2, 5, 1, 3]`: pierwszy przebieg daje `[2, 4, 1, 3, 5]`, kolejne
przesuwają mniejsze wartości w lewo, aż lista jest posortowana.

## Złożoność

- najlepszy: O(n) z early exit na posortowanych danych; O(n²) bez early exit
- średni / najgorszy: O(n²)
- pamięć: O(1), stabilny: tak

## Kiedy używać

Prawie nigdy w produkcji — to punkt odniesienia „jak wolno może być poprawnie”.

## Co pokazał pomiar

(uzupełnione po benchmarkach)
