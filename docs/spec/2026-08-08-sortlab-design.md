# sortlab — projekt techniczny

**Data:** 2026-08-08
**Status:** zatwierdzony do realizacji
**Budżet:** weekend (2–3 dni robocze)

---

## 1. Cel

`sortlab` to laboratorium pomiarowe algorytmów sortowania w Pythonie. Projekt portfolio: ma
nauczyć czegoś realnego i dobrze wyglądać na GitHubie.

Środek ciężkości leży **nie w algorytmach, a w stanowisku pomiarowym**. Implementacje sortowań są
celowo naiwne i czytelne — mają być do czytania. Prawdziwa inżynieria jest w warstwie, która je
mierzy: generatorach danych, instrumentacji, runnerze, profilerze, dopasowaniu złożoności
i generatorze raportów.

Teza projektu, którą README musi udowodnić pomiarami, a nie cytatem:

> Złożoność obliczeniową algorytmu można odczytać z pomiarów czasu, bez zaglądania do kodu.

## 2. Nie-cele

Świadomie poza zakresem — każdy z tych punktów to osobny projekt:

- aplikacja webowa lub interaktywna wizualizacja w przeglądarce,
- sortowanie zewnętrzne (dane większe niż RAM), równoległe lub rozproszone,
- rozszerzenia w C / Cython / próby pobicia `sorted()` wydajnością,
- interaktywny podgląd na żywo w terminalu,
- publikacja na PyPI (repo ma być instalowalne lokalnie, ale nie publikujemy),
- benchmarki bibliotek zewnętrznych (numpy, pandas) — mierzymy tylko własne implementacje
  i wbudowany `sorted()` jako linię odniesienia.

## 3. Decyzje projektowe

| Decyzja | Uzasadnienie |
|---|---|
| Dane wejściowe: liczby całkowite jako baza + jeden realny CSV | Liczby dają czysty, powtarzalny pomiar; CSV pokazuje, że to działa na prawdziwych danych |
| Realny CSV **generowany skryptem z ustalonym seedem** | Repo zostaje małe, wyniki odtwarzalne u każdego, brak zależności od martwego linku |
| Raport: PNG commitowane do repo + tabele w README | Widoczne od razu na stronie projektu, bez uruchamiania czegokolwiek |
| Animacje: GIF generowane skryptem, commitowane | Efekt wizualny w README bez GitHub Pages i bez JS |
| README po angielsku, spec i README algorytmów po polsku | README to zasięg; spec to dokument roboczy |
| Wszystkie algorytmy sortują **in-place i zwracają `None`** | Jeden kontrakt dla całego rejestru — bez tego testy współdzielone się rozjeżdżają |
| Warianty algorytmu = **osobne wpisy w rejestrze** | Bez tego nie da się postawić na jednym wykresie naiwnego pivota obok mediany z trzech, a to główna puenta quicksorta |
| `sorted()` też jest zarejestrowanym algorytmem | Linia odniesienia musi przechodzić te same testy i pomiary co reszta, inaczej porównanie jest nieuczciwe |
| Wygenerowany CSV **nie jest commitowany** | 8 MB danych w repo portfolio to szum; skrypt z ustalonym seedem odtwarza plik identycznie |
| Metryki liczone: **porównania i zapisy**, nie „przestawienia" | Zamiana `a[i], a[j] = a[j], a[i]` to dwa zapisy; „liczba swapów" nie jest uczciwie mierzalna z zewnątrz |
| Python 3.11+ | `Self`, lepsze komunikaty błędów, dostępne wszędzie |

## 4. Architektura

Dwie warstwy, rozdzielone celowo i sztywno.

```
                    ┌─────────────────────────────┐
                    │   cli.py  (bench|report|…)  │
                    └──────────────┬──────────────┘
                                   │
      ┌────────────┬───────────────┼───────────────┬────────────┐
      ▼            ▼               ▼               ▼            ▼
  datasets.py  instrument.py    bench.py      complexity.py  report.py
      │            │               │               ▲            ▲
      │            └──────┬────────┘               │            │
      │                   │                  wyniki JSON ───────┘
      │                   ▼
      │             profile.py                animate.py
      │                                            │
      └────────────────► registry.py ◄─────────────┘
                              │
                              ▼
                   algorithms/*/algorithm.py
```

Zależności idą wyłącznie w jedną stronę: algorytmy nie wiedzą nic o warstwie pomiarowej.
To warunek konieczny — algorytm, który wie, że jest mierzony, przestaje być uczciwym obiektem
pomiaru.

### 4.1 Struktura katalogów

```
sortlab/
├── README.md
├── LICENSE                          (MIT)
├── pyproject.toml                   pakiet + ruff + mypy + pytest
├── .github/workflows/ci.yml
├── src/sortlab/
│   ├── __init__.py
│   ├── types.py                     SortFn, AlgorithmSpec, Distribution
│   ├── registry.py                  @register + autodiscovery
│   ├── instrument.py                Counters, Tracked, TrackedList
│   ├── datasets.py                  7 rozkładów + generator CSV
│   ├── bench.py                     runner + serializacja wyników
│   ├── profile.py                   próbkowanie CPU/RAM
│   ├── complexity.py                regresja log-log
│   ├── report.py                    wykresy PNG + tabele markdown
│   ├── animate.py                   GIF
│   ├── cli.py                       argparse + rich
│   └── algorithms/
│       ├── __init__.py
│       ├── bubble_sort/{__init__.py, algorithm.py, README.md}
│       ├── insertion_sort/…
│       ├── selection_sort/…
│       ├── shell_sort/…
│       ├── merge_sort/…
│       ├── quick_sort/…             3 warianty pivota
│       ├── heap_sort/…
│       ├── counting_sort/…
│       ├── radix_sort/…
│       └── builtin_timsort/…        linia odniesienia: a[:] = sorted(a)
├── tests/
│   ├── conftest.py
│   ├── test_registry.py
│   ├── test_correctness.py          parametryzowany po rejestrze
│   ├── test_contracts.py            stabilność, in-place
│   ├── test_properties.py           Hypothesis
│   ├── test_instrument.py
│   ├── test_datasets.py
│   └── test_complexity.py
├── benchmarks/results/*.json        surowe wyniki, commitowane
├── scripts/make_dataset.py
└── docs/
    ├── spec/2026-08-08-sortlab-design.md
    ├── charts/*.png
    └── animations/*.gif
```

## 5. Kontrakty modułów

### 5.1 `types.py`

```python
SortFn = Callable[[MutableSequence[Any]], None]  # sortuje in-place, zwraca None


@dataclass(frozen=True, slots=True)
class AlgorithmSpec:
    name: str  # unikalny, snake_case, = nazwa katalogu
    func: SortFn
    complexity: str  # notacja teoretyczna, np. "O(n^2)"
    expected_exponent: float  # oczekiwany wykładnik w regresji log-log
    stable: bool
    in_place: bool
    comparison_based: bool
    max_n: int  # bezpiecznik runnera
    notes: str = ""
```

`expected_exponent` istnieje po to, żeby test złożoności mógł porównać pomiar z teorią. Dla
O(n log n) przyjmujemy 1.15 z szeroką tolerancją — log rośnie na tyle wolno, że regresja
potęgowa daje wykładnik między 1.0 a 1.25 zależnie od zakresu n.

### 5.2 `registry.py`

```python
def register(**metadata) -> Callable[[SortFn], SortFn]   # dekorator
def discover() -> None                                   # importuje algorithms/*/
def all_algorithms() -> tuple[AlgorithmSpec, ...]        # posortowane po nazwie
def get(name: str) -> AlgorithmSpec
```

`discover()` skanuje `algorithms/` przez `pkgutil.iter_modules` i importuje każdy podpakiet,
co uruchamia dekoratory. Wywoływane raz, z `__init__.py` pakietu. Rejestracja duplikatu nazwy
podnosi wyjątek.

Warunek akceptacji: dodanie algorytmu = jeden nowy katalog i jeden dekorator. Zero edycji
w istniejących plikach.

### 5.3 `instrument.py` — sedno

Instrumentacja musi być całkowicie przezroczysta dla algorytmu. Algorytm pisze zwykłe
`if a[j] > a[j + 1]: a[j], a[j + 1] = a[j + 1], a[j]` i nie wie, że cokolwiek jest liczone.

Osiągamy to na dwóch poziomach:

```python
@dataclass(slots=True)
class Counters:
    comparisons: int = 0
    writes: int = 0
    reads: int = 0


class Tracked:
    """Owija wartość. Każde porównanie inkrementuje licznik."""

    __slots__ = ("value", "_c")
    # __lt__, __le__, __gt__, __ge__, __eq__  →  self._c.comparisons += 1


class TrackedList(MutableSequence[Any]):
    """Owija listę. Zapisy i odczyty inkrementują liczniki.
    Opcjonalny on_write(snapshot) zasila animacje."""
```

**Dwa tryby pomiaru, nigdy w jednym przebiegu:**

- *tryb czasu* — surowe `int`, bez żadnego owijania. Instrumentacja zniekształca czas
  kilkukrotnie, więc mieszanie trybów unieważniłoby oba wyniki.
- *tryb liczenia* — `TrackedList` z elementami `Tracked`. Czasu w tym trybie nie raportujemy.

Zysk z trybu liczenia: **metryka niezależna od maszyny**. Czas zależy od tego, co robi
w tle laptop; liczba porównań dla danego wejścia jest identyczna na każdym komputerze i to ona
jest dowodem w README.

Efekt uboczny wart odnotowania: `counting_sort` i `radix_sort` wykażą **zero porównań** przy
dodatnich zapisach. To nie błąd pomiaru, to puenta — pokazuje, dlaczego nie obowiązuje ich
dolne ograniczenie Ω(n log n).

`on_write` to hook, który zasila też animacje — ten sam mechanizm obsługuje liczenie
i zbieranie klatek. Bez tego każdy algorytm potrzebowałby drugiego, generatorowego wariantu.

### 5.4 `datasets.py`

```python
Distribution = Literal["random", "sorted", "reversed", "nearly_sorted",
                       "few_unique", "sawtooth", "zipf"]

def generate(distribution: Distribution, n: int, *, seed: int = 42) -> list[int]
def load_csv_keys(path: Path, column: str) -> list[str]
```

| Rozkład | Definicja | Co ujawnia |
|---|---|---|
| `random` | permutacja losowa | przypadek średni, punkt odniesienia |
| `sorted` | 0..n-1 | quicksort z naiwnym pivotem degeneruje do n² |
| `reversed` | n-1..0 | najgorszy przypadek dla bubble i insertion |
| `nearly_sorted` | posortowane + 1% losowych zamian | insertion sort **wygrywa** z quicksortem |
| `few_unique` | 10 różnych wartości | zachowanie na duplikatach; problem flagi holenderskiej |
| `sawtooth` | powtarzany ciąg rosnący | shell sort i merge korzystają z lokalnych serii |
| `zipf` | rozkład potęgowy | najbliżej realnych danych |

Wszystkie generatory deterministyczne przy tym samym `seed`. Test sprawdza determinizm.

`scripts/make_dataset.py` generuje realny CSV: 200 000 wierszy z polami
`id, surname, city, registered_at, amount`, seed ustalony, ~8 MB. Sortowanie po `surname`
z powtórzeniami — dzięki temu widać różnicę między sortowaniem stabilnym a niestabilnym
na prawdziwym pliku.

Plik **nie jest commitowany** — `data/` wchodzi do `.gitignore`. Skrypt z ustalonym seedem
odtwarza go bajt w bajt, więc commitowanie 8 MB byłoby wyłącznie szumem w repo portfolio.
README podaje jedną komendę, która go generuje.

### 5.5 `bench.py`

```python
@dataclass(frozen=True, slots=True)
class TimingResult:
    median_s: float; min_s: float; repeats: int

@dataclass(frozen=True, slots=True)
class RunResult:
    algorithm: str; distribution: str; n: int
    timing: TimingResult | None
    counters: Counters | None
    resources: ResourceSample | None
    status: Literal["ok", "skipped_max_n", "timeout"]

def time_run(spec, data, *, repeats=5, warmup=1, timeout_s=30.0) -> TimingResult
def count_run(spec, data) -> Counters
def run_matrix(algorithms, distributions, sizes, *, profile=False) -> BenchmarkReport
def save(report, path) -> None
```

Protokół pomiaru czasu — każdy punkt ma znaczenie:

1. świeża kopia danych dla każdego powtórzenia (algorytm sortuje in-place; drugie powtórzenie
   na już posortowanej liście mierzyłoby coś zupełnie innego),
2. jeden przebieg rozgrzewkowy, odrzucany,
3. `gc.disable()` na czas pomiaru, `gc.enable()` w `finally`,
4. `time.perf_counter()`,
5. raportowana **mediana** z `repeats`; `min` zapisany dodatkowo jako wartość najmniej
   zaszumiona.

Bezpieczniki, bez których projekt się nie uruchomi:

- `n > spec.max_n` → status `skipped_max_n`, bez uruchamiania. Bubble sort na milionie
  elementów to godziny.
- twardy timeout na pojedynczy przebieg → status `timeout`, przebieg porzucony, runner leci dalej.
- pominięte kombinacje **trafiają do raportu jako pominięte**. Puste miejsce na wykresie musi
  być opisane, nie zamiecione.

### 5.6 `profile.py`

```python
@dataclass(frozen=True, slots=True)
class ResourceSample:
    peak_rss_bytes: int
    tracemalloc_peak_bytes: int
    cpu_percent_samples: list[float]
    sample_interval_s: float

def profiled(min_duration_s: float = 0.5) -> ContextManager[ResourceSample]
```

Wątek próbkujący `psutil.Process().cpu_percent()` i RSS co 50 ms, plus `tracemalloc` dla
alokacji samego Pythona. Profilujemy **tylko przebiegi dłuższe niż 0.5 s** — na krótszych
próbkowanie daje wyłącznie szum. README mówi o tym wprost, zamiast udawać czyste dane.

Wykres RAM ma jedno konkretne zadanie: pokazać, że `merge_sort` alokuje pamięć proporcjonalną
do n, a `heap_sort` i `quick_sort` nie. To dowód na kolumnę `in_place` w tabeli.

### 5.7 `complexity.py`

Element flagowy projektu.

```python
@dataclass(frozen=True, slots=True)
class FitResult:
    exponent: float; intercept: float; r_squared: float; points: int

def fit_power_law(ns: Sequence[int], times: Sequence[float]) -> FitResult
def classify(fit: FitResult) -> str    # "≈O(n)", "≈O(n log n)", "≈O(n²)"
```

Metoda: najmniejsze kwadraty dla `log(t) = a·log(n) + b`; `a` to zmierzony wykładnik.
Wymagane minimum 4 punkty pomiarowe i `r_squared >= 0.95`, inaczej `classify` zwraca
`"nierozstrzygnięte"` — lepiej przyznać się do braku wyniku niż podać liczbę bez podstaw.

Wynik w README:

| Algorytm | Teoria | Zmierzony wykładnik | R² | Klasyfikacja |
|---|---|---|---|---|
| bubble_sort | O(n²) | 1.98 | 0.999 | ≈O(n²) |
| quick_sort | O(n log n) | 1.06 | 0.997 | ≈O(n log n) |
| radix_sort | O(n·k) | 1.01 | 0.998 | ≈O(n) |

Test `test_complexity.py` weryfikuje, że dla każdego algorytmu zmierzony wykładnik mieści się
w tolerancji wokół `expected_exponent`. To test, który realnie może złapać błąd
w implementacji — przypadkowe O(n²) w merge sorcie objawi się właśnie tutaj.

### 5.8 `report.py`

```python
def chart_time_vs_n(report, distribution, out: Path) -> None        # log-log
def chart_distribution_comparison(report, n, out: Path) -> None     # słupki
def chart_operation_counts(report, out: Path) -> None               # porównania vs zapisy
def chart_memory(report, out: Path) -> None
def chart_complexity_fit(report, out: Path) -> None                 # pomiary + dopasowana prosta
def heatmap_algorithm_x_distribution(report, n, out: Path) -> None
def markdown_tables(report) -> str
def write_all(report, charts_dir, readme_path) -> None
```

Sześć wykresów PNG do `docs/charts/`, jeden wspólny styl, zawsze `sorted()` jako linia
odniesienia. Tabele markdown wstrzykiwane do README między znacznikami
`<!-- sortlab:tables:start -->` i `<!-- sortlab:tables:end -->` — README zostaje pisane ręcznie,
podmieniane są tylko liczby.

Każdy wykres podpisany modelem CPU i wersją Pythona z metadanych raportu. Wykres bez tych
danych jest nieuczciwy.

### 5.9 `animate.py`

```python
def animate(algorithm: str, out: Path, *, n: int = 60,
            distribution: Distribution = "random", max_frames: int = 300,
            fps: int = 30) -> None
```

Klatki zbierane przez hook `on_write` z `TrackedList` — bez żadnych zmian w algorytmach.
Przy dużej liczbie zapisów co k-ta klatka, tak by trafić w `max_frames`. Render:
`matplotlib.animation.FuncAnimation` + `PillowWriter`.

Cel: 4 GIF-y do README (bubble, insertion, quick, merge), każdy poniżej 2 MB.

Ryzyko: dobranie rozmiaru i liczby klatek zajmuje więcej prób, niż się wydaje. Dlatego ten
etap jest ostatni i wypada bez szkody dla reszty projektu.

### 5.10 `cli.py`

```
sortlab list                                              tabela rejestru (rich)
sortlab bench  [--algorithms …] [--distributions …] [--sizes …] [--profile] [-o …]
sortlab report [--results …] [--charts-dir …] [--readme …]
sortlab animate --algorithm quick_sort [--n 60]
sortlab dataset --rows 200000 -o data/records.csv
```

`argparse` + `rich` do tabel. `--sizes` przyjmuje listę lub `500:16000:x2` (skala
geometryczna). Domyślne wartości muszą dawać sensowny wynik bez żadnych argumentów —
`sortlab bench` samo w sobie ma zadziałać i dać kompletny zestaw.

## 6. Algorytmy

**Dziesięć katalogów, trzynaście wpisów w rejestrze.** Warianty rejestrują się jako osobne
algorytmy pod własnymi nazwami — inaczej nie da się postawić naiwnego pivota obok mediany
z trzech na jednym wykresie, a to główna puenta quicksorta.

| Katalog | Zarejestrowane nazwy | Rola w projekcie |
|---|---|---|
| `bubble_sort` | `bubble_sort`, `bubble_sort_early_exit` | punkt odniesienia „jak źle może być"; wariant z wyjściem pokazuje adaptacyjność |
| `insertion_sort` | `insertion_sort` | **wygrywa** na prawie posortowanych — łamie intuicję „n² jest zawsze złe" |
| `selection_sort` | `selection_sort` | minimum zapisów przy maksimum porównań; dowodzi, że to dwie różne metryki |
| `shell_sort` | `shell_sort_shell`, `shell_sort_ciura` | most między n² a n log n; wpływ sekwencji odstępów |
| `merge_sort` | `merge_sort` | stabilny, ale kosztuje pamięć — widać to na wykresie RAM |
| `quick_sort` | `quick_sort_last`, `quick_sort_random`, `quick_sort_median3` | dramat: naiwny pivot degeneruje do n² na już posortowanym wejściu |
| `heap_sort` | `heap_sort` | in-place i przewidywalny, ale nigdy najszybszy |
| `counting_sort` | `counting_sort` | zero porównań; podstawa radixa |
| `radix_sort` | `radix_sort` | LSD, baza 10; **przełamuje barierę n log n** — puenta README |
| `builtin_timsort` | `builtin_timsort` | linia odniesienia na każdym wykresie |

`builtin_timsort` to `a[:] = sorted(a)` — spełnia kontrakt in-place, więc przechodzi te same
testy i pomiary co reszta. Ma `max_n` ustawione na maksimum i `expected_exponent = 1.15`.
Uwaga pomiarowa: w trybie liczenia jego licznik porównań wyjdzie zerowy, bo `sorted()` porównuje
w C, poza zasięgiem `Tracked`. To ograniczenie metody i README musi je nazwać wprost —
liczba porównań Timsorta jest niemierzalna tym narzędziem, mierzalny jest tylko jego czas.

Każdy katalog zawiera `algorithm.py` i `README.md` (po polsku: jak działa, złożoność, kiedy
używać, co pokazał pomiar). Implementacje mają być czytelne, nie sprytne — to materiał do
czytania, nie do wyciskania wydajności.

## 7. Testy

Zasada: **jeden współdzielony zestaw testów parametryzowany po rejestrze**. Dziewięć
algorytmów, żaden nie ma własnych testów. Nowy algorytm dziedziczy cały zestaw automatycznie.

| Plik | Zakres |
|---|---|
| `test_registry.py` | discovery znajduje wszystkie katalogi; duplikat nazwy podnosi wyjątek; metadane kompletne |
| `test_correctness.py` | ∀ algorytm × ∀ rozkład: wynik równy `sorted(wejście)`. Brzegi: pusta, 1 element, 2 elementy, wszystkie równe, wartości ujemne |
| `test_contracts.py` | funkcja zwraca `None`; sortuje in-place; `stable=True` → weryfikacja stabilności na parach (klucz, indeks); `in_place=True` → brak wzrostu `tracemalloc` powyżej progu |
| `test_properties.py` | Hypothesis: wynik jest posortowaną permutacją wejścia (`Counter` przed = po) |
| `test_instrument.py` | licznik porównań zgadza się z ręcznie policzoną wartością dla insertion sort na `[3,1,2]`; `count_run` nie modyfikuje wejścia wywołującego; `on_write` dostaje właściwą liczbę wywołań |
| `test_datasets.py` | każdy rozkład ma długość n; determinizm przy tym samym seedzie; `nearly_sorted` faktycznie ma ~1% inwersji |
| `test_complexity.py` | zmierzony wykładnik w tolerancji wokół `expected_exponent`; `fit_power_law` na danych syntetycznych `t = n^2` zwraca 2.0 ± 0.05 |

`test_instrument.py` jest ważniejszy, niż wygląda: licznik, który kłamie, unieważnia cały
projekt. Testujemy narzędzie pomiarowe wzorcem policzonym na piechotę.

Wymagane: pokrycie ≥ 90% dla `src/sortlab/` poza `report.py` i `animate.py` (renderowanie
wykresów testujemy tylko dymnie — plik powstał i jest niepusty).

## 8. CI

GitHub Actions, na push i PR, macierz Python 3.11 / 3.12 / 3.13:

1. `ruff check` + `ruff format --check`
2. `mypy --strict src/`
3. `pytest --cov`
4. benchmark dymny: `sortlab bench --sizes 100,200,400 --distributions random`
   — sprawdza, że runner i serializacja żyją, bez wydłużania CI

Benchmarki pełne uruchamiane lokalnie, wyniki commitowane. CI nie mierzy wydajności —
runnery współdzielone dają wyniki bez wartości.

## 9. README

Kolejność ułożona pod kogoś, kto daje projektowi 20 sekund:

1. **Jedno zdanie** czym to jest + tabela zmierzonych wykładników. Zaczynamy od najmocniejszego
   wyniku, nie od instalacji.
2. **GIF-y** — cztery animacje obok siebie.
3. **Wykresy** — czas vs n (log-log), porównanie rozkładów, mapa cieplna.
4. **Wnioski** — 4–5 rzeczywistych obserwacji z pomiarów, własnymi słowami. Ta sekcja
   odróżnia „przepisałem algorytmy" od „zmierzyłem i zrozumiałem". Kandydaci:
   - gdzie leży punkt przecięcia insertion sort z quicksortem na prawie posortowanych danych,
   - ile dokładnie kosztuje naiwny wybór pivota na posortowanym wejściu,
   - dlaczego selection sort ma najmniej zapisów i kiedy to ma znaczenie,
   - dlaczego radix sort łamie Ω(n log n) i czego to kosztuje,
   - jak daleko `sorted()` jest przed wszystkim, co napisaliśmy, i dlaczego.
5. **Uruchomienie** — instalacja i cztery komendy.
6. **Jak dodać swój algorytm** — katalog plus dekorator, pięć linii. Zaproszenie do PR-ów.
7. **Metodologia pomiaru** — protokół z sekcji 5.5 i uczciwe ograniczenia (szum CPU,
   próbkowanie tylko powyżej 0.5 s, wyniki z jednej maszyny).
8. **Architektura** — dlaczego algorytmy nie wiedzą, że są mierzone.

Punkt „Metodologia pomiaru" jest nieoczywisty i dlatego wartościowy: pokazuje, że autor wie,
gdzie jego pomiary są słabe. To buduje więcej zaufania niż same wykresy.

## 10. Kolejność realizacji

Etapy uporządkowane tak, że po każdym repo jest w stanie zdatnym do pokazania. Jeśli czas się
skończy na etapie 7, projekt nadal jest kompletny.

| Etap | Zakres | Kryterium ukończenia |
|---|---|---|
| 0 | `pyproject.toml`, CI, `types.py`, `registry.py`, `insertion_sort`, współdzielone testy | zielony CI na jednym algorytmie |
| 1 | `datasets.py` + 7 rozkładów + testy | `test_datasets.py` zielony |
| 2 | pozostałe 9 katalogów + README każdego | `test_correctness.py` zielony dla 13 wpisów rejestru |
| 3 | `instrument.py` + `test_instrument.py` | licznik zgodny z wzorcem ręcznym |
| 4 | `bench.py` + JSON + bezpieczniki + `cli.py bench` | `sortlab bench` bez argumentów daje kompletny JSON |
| 5 | `complexity.py` + `test_complexity.py` | bubble → 1.9–2.1, merge → 1.0–1.25 |
| 6 | `report.py` + 6 wykresów + tabele + `cli.py report` | PNG w `docs/charts/`, tabele w README |
| 7 | `profile.py` + wykres pamięci | wykres pokazuje różnicę merge vs heap |
| 8 | `animate.py` + 4 GIF-y | każdy GIF < 2 MB |
| 9 | README: wnioski, metodologia, architektura | README kompletne |

Etapy 8 i 9 zamieniają się kolejnością, jeśli czas jest napięty — README bez GIF-ów jest
kompletne, GIF-y bez README nie znaczą nic.

## 11. Ryzyka

| Ryzyko | Reakcja |
|---|---|
| Animacje zjedzą więcej czasu, niż zakładano | Etap ostatni, wypada bez szkody dla reszty |
| Szum pomiarowy `psutil` na krótkich przebiegach | Próbkujemy tylko > 0.5 s, ograniczenie opisane w README |
| Regresja log-log daje niestabilny wykładnik na małym zakresie n | Minimum 4 punkty, wymóg R² ≥ 0.95, w przeciwnym razie „nierozstrzygnięte" |
| Bubble sort blokuje runner przy dużym n | `max_n` w metadanych + twardy timeout |
| Instrumentacja spowalnia pomiar czasu | Dwa rozdzielone tryby; czas nigdy nie mierzony na `TrackedList` |
| Projekt wygląda jak zadanie ze studiów | Środek ciężkości w warstwie pomiarowej; README otwiera tabelą wykładników, nie listą algorytmów |
