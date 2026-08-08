# sortlab — prompty dla Cursora

Instrukcja krok po kroku. Każdy etap to jeden nowy czat w Cursorze.

---

## Jak to prowadzić

**Nowy czat na każdy etap.** Nie ciągnij jednego wątku przez cały projekt — kontekst się
zapycha i Cursor zaczyna zapominać niezmienniki z reguł.

**Do każdego promptu dołącz spec przez `@`:**
`@docs/spec/2026-08-08-sortlab-design.md`

Reguły z `.cursor/rules/` wciągają się same (`00-project.mdc` ma `alwaysApply: true`).

**Po każdym etapie sam uruchom weryfikację** — nie wierz na słowo:

```
ruff check . ; if ($?) { mypy --strict src/ } ; if ($?) { pytest -q }
```

**Nie pozwól łączyć etapów.** Etapy 4–6 (runner → dopasowanie złożoności → raport) w jednym
przebiegu to gwarantowany bałagan — Cursor zacznie projektować format wyników pod wykresy,
zamiast pod pomiar.

**Gdy coś nie przechodzi:** nie proś o „napraw testy". Proś o diagnozę: *„który z tych dwóch
jest zepsuty — kod czy założenie testu? Uzasadnij, potem napraw właściwy."* Inaczej dostaniesz
osłabioną asercję i zielone CI, które nic nie znaczy.

---

## Etap 0 — szkielet, rejestr, pierwszy algorytm

```
Przeczytaj @docs/spec/2026-08-08-sortlab-design.md — realizujemy etap 0 z sekcji 10.

Zbuduj:
1. pyproject.toml — pakiet sortlab, layout src/, Python >=3.11, zależności produkcyjne
   i deweloperskie dokładnie te z reguł projektu, konfiguracja ruff (linia 100), mypy strict
   i pytest z pokryciem.
2. .gitignore (data/ musi być), LICENSE (MIT), .github/workflows/ci.yml zgodnie z sekcją 8.
3. src/sortlab/types.py — SortFn, AlgorithmSpec, Distribution, hierarchia wyjątków
   SortlabError zgodnie z sekcją 5.1.
4. src/sortlab/registry.py — register/discover/all_algorithms/get zgodnie z sekcją 5.2.
   Duplikat nazwy podnosi wyjątek. discover() przez pkgutil.iter_modules.
5. src/sortlab/algorithms/insertion_sort/ — jeden algorytm, zgodnie z kontraktem
   z .cursor/rules/10-algorithms.mdc, razem z README.md po polsku.
6. tests/test_registry.py i tests/test_correctness.py — parametryzowane po rejestrze,
   na razie z jednym wpisem.

TDD: najpierw testy, uruchom je, pokaż mi że są czerwone, dopiero potem implementacja.

Nie pisz jeszcze datasets, instrument, bench, report ani CLI.
```

**Ukończone, gdy:** `ruff`, `mypy --strict`, `pytest` zielone na jednym algorytmie.

---

## Etap 1 — generatory danych

```
Etap 1 z sekcji 10 specu: src/sortlab/datasets.py.

Zaimplementuj generate() dla wszystkich siedmiu rozkładów z tabeli w sekcji 5.4 oraz
load_csv_keys(). Wszystko deterministyczne przy tym samym seedzie.

Najpierw tests/test_datasets.py: długość równa n, determinizm przy tym samym seedzie,
różny wynik przy różnym seedzie, nearly_sorted ma faktycznie około 1% inwersji (sprawdź
licząc inwersje, nie na wiarę), few_unique ma dokładnie 10 różnych wartości, sawtooth
i zipf mają udokumentowany kształt.

Pokaż mi czerwone testy przed implementacją.
```

**Ukończone, gdy:** `test_datasets.py` zielony, w tym test liczący inwersje.

---

## Etap 2 — pozostałe algorytmy

```
Etap 2 z sekcji 10 specu: pozostałe dziewięć katalogów algorytmów, trzynaście wpisów
w rejestrze łącznie. Lista i nazwy w tabeli w sekcji 6.

Trzymaj się kontraktu z .cursor/rules/10-algorithms.mdc — szczególnie: żadnych importów
z warstwy pomiarowej, in-place i zwracanie None, operowanie tylko przez interfejs
MutableSequence.

Rozszerz tests/test_correctness.py o wszystkie rozkłady z datasets oraz przypadki brzegowe
(pusta lista, 1 element, 2 elementy, wszystkie równe, wartości ujemne). Dodaj
tests/test_contracts.py: zwraca None, sortuje in-place, stable=True weryfikowane na parach
(klucz, indeks pierwotny), in_place=True weryfikowane progiem tracemalloc.

Dodaj tests/test_properties.py z Hypothesis: wynik jest posortowaną permutacją wejścia
(Counter przed równy Counter po).

Zrób to po jednym algorytmie: test czerwony, implementacja, zielony, następny.
Po każdym pokaż mi wynik pytest.

Uwaga na counting_sort i radix_sort — comparison_based=False, wolno im kubełki.
Uwaga na builtin_timsort — a[:] = sorted(a), spełnia kontrakt in-place.
```

**Ukończone, gdy:** 13 wpisów w rejestrze, `test_correctness.py` i `test_contracts.py` zielone
dla wszystkich.

**Tu najczęściej coś idzie nie tak:** sprawdź, czy Cursor nie wsadził `sorted()` do środka
merge sorta „dla pewności" i czy warianty quicksorta faktycznie dzielą wspólne `_quicksort`
zamiast być trzy razy przekopiowane.

---

## Etap 3 — instrumentacja

```
Etap 3 z sekcji 10 specu: src/sortlab/instrument.py — Counters, Tracked, TrackedList
zgodnie z sekcją 5.3.

Wymagania krytyczne:
- Tracked owija wartość; każde __lt__/__le__/__gt__/__ge__/__eq__ inkrementuje comparisons.
- TrackedList owija listę; __setitem__ inkrementuje writes, __getitem__ inkrementuje reads.
- TrackedList przyjmuje opcjonalny on_write(snapshot) — ten sam hook zasili później animacje.
- Żaden algorytm nie może wymagać zmiany. Instrumentacja jest całkowicie przezroczysta.

Najpierw tests/test_instrument.py, i to jest najważniejszy plik testowy w projekcie:
- policz na piechotę liczbę porównań insertion sorta na [3, 1, 2] i zapisz tę liczbę jako
  wzorzec w teście; to samo dla selection sorta na [3, 1, 2]
- porównania są niezależne od maszyny: ten sam wynik przy każdym uruchomieniu
- count_run nie modyfikuje listy przekazanej przez wywołującego
- on_write dostaje dokładnie tyle wywołań, ile było zapisów
- counting_sort i radix_sort dają comparisons == 0 przy writes > 0

Ten ostatni punkt to teza projektu — jeśli nie wychodzi, coś jest fundamentalnie źle.
```

**Ukończone, gdy:** liczniki zgadzają się z wartościami policzonymi ręcznie, a sortowania
niekomparacyjne pokazują zero porównań.

---

## Etap 4 — runner benchmarków

```
Etap 4 z sekcji 10 specu: src/sortlab/bench.py oraz komenda bench w src/sortlab/cli.py.

Protokół pomiaru czasu z sekcji 5.5 realizuj co do punktu — świeża kopia danych na każde
powtórzenie, jeden przebieg rozgrzewkowy odrzucany, gc.disable() w try i gc.enable()
w finally, time.perf_counter(), raportowana mediana.

Świeża kopia jest krytyczna: algorytmy sortują in-place, więc bez tego drugie powtórzenie
mierzy sortowanie już posortowanej listy.

Bezpieczniki: n > spec.max_n daje status skipped_max_n bez uruchamiania; twardy timeout
na przebieg daje status timeout. Pominięte kombinacje MUSZĄ trafić do wyników jako pominięte,
nigdy nie wypadać po cichu.

Do metadanych raportu zapisz model CPU, liczbę rdzeni, wersję Pythona, system, wersję sortlab
i znacznik czasu UTC.

CLI: sortlab list oraz sortlab bench z opcjami z sekcji 5.10. Domyślne wartości muszą dać
sensowny kompletny wynik bez żadnych argumentów. --sizes obsługuje też zapis 500:16000:x2.

Testy: serializacja i deserializacja bez straty, skipped_max_n faktycznie nie uruchamia
funkcji (podstaw szpiega), timeout obsłużony, świeża kopia weryfikowana testem który
by upadł gdyby jej nie było.
```

**Ukończone, gdy:** samo `sortlab bench` daje kompletny JSON z pominięciami opisanymi jako
pominięcia.

---

## Etap 5 — dopasowanie złożoności

```
Etap 5 z sekcji 10 specu: src/sortlab/complexity.py — fit_power_law i classify
zgodnie z sekcją 5.7.

Najmniejsze kwadraty dla log(t) = a*log(n) + b. Minimum 4 punkty i R^2 >= 0.95, inaczej
classify zwraca "nierozstrzygnięte". Lepiej przyznać się do braku wyniku niż podać liczbę
bez podstaw.

Testy:
- na danych syntetycznych t = n^2 fit zwraca wykładnik 2.0 +/- 0.05 i R^2 > 0.999
- to samo dla t = n^1.5 i t = n
- przy 3 punktach albo niskim R^2 dostajemy "nierozstrzygnięte"
- test integracyjny na prawdziwych pomiarach: dla każdego zarejestrowanego algorytmu
  zmierzony wykładnik mieści się w tolerancji wokół expected_exponent

Ten ostatni test jest wart więcej niż wygląda — przypadkowe O(n^2) w merge sorcie objawi się
właśnie tutaj i nigdzie indziej.
```

**Ukończone, gdy:** bubble wychodzi 1.9–2.1, merge 1.0–1.25, radix około 1.0.

---

## Etap 6 — raport i wykresy

```
Etap 6 z sekcji 10 specu: src/sortlab/report.py — sześć wykresów z sekcji 5.8
plus tabele markdown i komenda sortlab report.

Wspólny styl dla wszystkich wykresów. Na każdym linia odniesienia builtin_timsort.
Każdy wykres podpisany modelem CPU i wersją Pythona z metadanych raportu.

Tabele markdown wstrzykiwane do README między znacznikami
<!-- sortlab:tables:start --> i <!-- sortlab:tables:end -->. README pisany ręcznie,
podmieniane tylko liczby — nigdy nie nadpisuj całego README.

Wykresy o pominiętych pomiarach: pominięcia muszą być widoczne, np. adnotacją
"skipped: n > max_n", nie milczącą luką.

Testy dymne: plik PNG powstał i jest niepusty, wstrzyknięcie tabel jest idempotentne
(dwa uruchomienia dają ten sam plik), tekst poza znacznikami zostaje nietknięty.

Potem uruchom pełny benchmark, wygeneruj wykresy i pokaż mi listę plików z rozmiarami.
```

**Ukończone, gdy:** PNG w `docs/charts/`, tabele w README, powtórne uruchomienie nic nie psuje.

---

## Etap 7 — profilowanie CPU i pamięci

```
Etap 7 z sekcji 10 specu: src/sortlab/profile.py zgodnie z sekcją 5.6, plus wykres pamięci
w report.py i flaga --profile w sortlab bench.

Wątek próbkujący psutil co 50 ms, plus tracemalloc. Profilujemy tylko przebiegi dłuższe
niż 0.5 s — na krótszych to wyłącznie szum.

Wątek próbkujący musi być demonem i musi się zamknąć nawet gdy mierzony kod rzuci wyjątek.
Napisz test, który to sprawdza.

Wykres pamięci ma jedno zadanie: pokazać, że merge_sort alokuje pamięć proporcjonalną do n,
a heap_sort i quick_sort nie. Jeśli tego nie widać — albo pomiar jest zły, albo któryś
algorytm kłamie w metadanych in_place. Rozstrzygnij które.
```

**Ukończone, gdy:** wykres pokazuje różnicę merge vs heap, a wątek próbkujący nie zostaje
po wyjątku.

---

## Etap 8 — animacje

```
Etap 8 z sekcji 10 specu: src/sortlab/animate.py plus komenda sortlab animate.

Klatki zbierane przez hook on_write z TrackedList — zero zmian w algorytmach. Przy dużej
liczbie zapisów bierz co k-tą klatkę, tak żeby trafić w max_frames.
matplotlib.animation.FuncAnimation + PillowWriter.

Wygeneruj cztery GIF-y do docs/animations/: bubble_sort, insertion_sort, quick_sort_median3,
merge_sort. n=60, rozkład random, każdy poniżej 2 MB.

Jeśli któryś przekracza 2 MB — zmniejsz max_frames albo fps, nie rozdzielczość poniżej
czytelności. Pokaż mi rozmiary plików.
```

**Ukończone, gdy:** cztery GIF-y poniżej 2 MB każdy.

---

## Etap 9 — README

```
Etap 9 z sekcji 10 specu: główne README.md po angielsku, dokładnie w kolejności sekcji
z sekcji 9 specu.

Zacznij od jednego zdania i tabeli zmierzonych wykładników — nie od instalacji. Ktoś daje
temu projektowi 20 sekund i musi w tym czasie zobaczyć najmocniejszy wynik.

Sekcję "Findings" napisz na podstawie PRAWDZIWYCH liczb z benchmarks/results/ — wypisz mi
najpierw, co konkretnie widzisz w danych, jako listę obserwacji z liczbami. Nie pisz
ogólników w stylu "quicksort is faster". Interesuje mnie: przy jakim n insertion sort
przestaje bić quicksorta na prawie posortowanych danych, ile razy dokładnie zwalnia
quick_sort_last na już posortowanym wejściu, ile razy builtin_timsort jest przed najlepszą
naszą implementacją.

Sekcja "Measurement methodology" ma zawierać uczciwe ograniczenia: szum CPU, próbkowanie
tylko powyżej 0.5 s, wyniki z jednej maszyny, niemierzalność porównań w builtin_timsort.

Nie wstawiaj emoji, nie wstawiaj odznak shields.io poza CI i licencją, nie pisz
"blazingly fast".
```

**Ukończone, gdy:** README otwiera się tabelą wykładników, a sekcja Findings zawiera konkretne
liczby, nie ogólniki.

---

## Prompt kontrolny — po całości

```
Przejrzyj repo pod kątem niezmienników z .cursor/rules/00-project.mdc. Dla każdego z sześciu
niezmienników podaj konkretny dowód, że jest spełniony, albo wskaż miejsce, gdzie jest
złamany.

Szczególnie sprawdź, czy żaden plik w src/sortlab/algorithms/ nie importuje z warstwy
pomiarowej — pokaż wynik grepa, nie deklarację.

Potem wypisz wszystko, co jest w repo, a nie ma uzasadnienia w specu. Zakładam, że coś takiego
jest — usuńmy to.
```

Ten ostatni prompt warto puścić także po etapach 4 i 6. Agenci mają skłonność do dokładania
warstw abstrakcji „na przyszłość", a to jest dokładnie ten rodzaj kodu, który sprawia, że repo
portfolio wygląda na przekombinowane.
