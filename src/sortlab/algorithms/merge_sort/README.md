# Merge sort

## Jak działa

Dzieli listę na połowy, sortuje je rekurencyjnie i scala dwa posortowane przebiegi
w jeden. Scalanie zachowuje kolejność równych elementów (stabilność).

## Złożoność

- czas: O(n log n) zawsze
- pamięć: O(n) dodatkowej — widać na wykresie RAM
- stabilny: tak

## Kiedy używać

Gdy potrzebna stabilność i przewidywalny czas; koszt to pamięć.

## Co pokazał pomiar

(uzupełnione po benchmarkach)
