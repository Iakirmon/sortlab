# Selection sort

## Jak działa

Dla każdej pozycji i znajduje minimum w zakresie `[i, n)` i wstawia je na miejsce i
jedną zamianą. Przykład `[4, 2, 5, 1, 3]`: minimum `1` trafia na początek →
`[1, 2, 5, 4, 3]`, potem `2` już jest na miejscu, potem `3` zamienia się z `5`.

## Złożoność

- zawsze O(n²) porównań
- zapisy: O(n) — stąd kontrast z bubble/insertion
- pamięć O(1), stabilny: nie

## Kiedy używać

Gdy zapis jest drogi, a porównanie tanie — rzadki przypadek. Tu służy jako dowód,
że porównania i zapisy to osobne metryki.

## Co pokazał pomiar

Na random n=3200: **5.12M porównań** i tylko **6384 zapisów**, podczas gdy
`bubble_sort` zrobił ~5.18M zapisów.
