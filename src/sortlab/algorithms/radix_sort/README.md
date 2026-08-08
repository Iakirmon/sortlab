# Radix sort (LSD, baza 10)

## Jak działa

Sortuje liczby całkowite cyfra po cyfrze od najmniej znaczącej, używając stabilnego
counting sorta na cyfrach. Ujemne są osobno sortowane po wartości bezwzględnej
i odwracane.

## Złożoność

- czas: O(n · k), k = liczba cyfr
- pamięć: O(n)
- stabilny: tak; comparison_based: nie — przełamuje Ω(n log n)

## Kiedy używać

Przy całkowitych kluczach o ograniczonej liczbie cyfr.

## Co pokazał pomiar

Zmierzony wykładnik na random ≈ **1.08**; w trybie liczenia **0 porównań** przy
dodatnich zapisach — dokładnie teza projektu.
