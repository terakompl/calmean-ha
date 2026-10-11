# CALMEAN → Home Assistant

**1.0.0 — mapa CALMEAN i strefy osobno dla każdego zegarka.**
Nieoficjalna integracja społecznościowa. Instalacja i konfiguracja bez YAML.

![Ikona integracji](custom_components/calmean/brand/icon.png)

Specyfikacja: [wymagania](docs/SPECYFIKACJA.md).
Publikacja: [GitHub i HACS krok po kroku](docs/PUBLIKACJA_GITHUB_HACS.md).

## Mapa i własne strefy

- Wybierz **Wszystkie zegarki**, aby zobaczyć wszystkie pozycje i strefy.
- Wybierz pojedynczy zegarek z listy lub kliknij jego znacznik.
- Panel pokazuje baterię, rozpoznane miejsce, typ oraz czas ostatniej lokalizacji.
- Wybierz **Dodaj strefę** i wpisz nazwę, np. Dom, Szkoła lub Dziadkowie.
- Wybierz typ: Dom / Szkoła / Własna lokalizacja. Typ Dom daje trackerowi
  standardowy stan `home`; pozostałe typy nie nadpisują globalnego domu HA.
- Kliknij punkt na mapie lub wpisz współrzędne ręcznie.
- Promień domyślny to **50 m**, zakres nowych stref **50–5000 m**.
- Kliknij **Zapisz strefę**. Zapis dotyczy wyłącznie wybranego zegarka.
- Edytuj lub usuń istniejące strefy; przyciskiem **↑** zmień ich kolejność.
  Przy nakładaniu promieni pierwszeństwo ma pierwsza strefa na liście.

Obrysy na mapie oznaczają promienie stref. To **tolerancja rozpoznawania
miejsca, nie gwarantowana dokładność GPS**. Integracja nie poprawia pozycji
CALMEAN. Mapa pokazuje ostatnią pozycję API; jeśli odczyt zawiedzie, panel
wyraźnie oznacza ostatnie dane jako nieaktualne pod względem połączenia.
Czas lokalizacji jest widoczny także wtedy, gdy API odpowiada poprawnie.

Mapa obsługuje przesuwanie, zoom przyciskami, kółkiem myszy i gestem dwóch
palców. Przycisk ◎ dopasowuje widok do wybranych lokalizacji. Na telefonie mapa
jest nad formularzem. Klawiatura: strzałki przesuwają, plus/minus zmienia zoom.
Widok nie zawiera historii tras; standardowa karta Mapa HA może ją pokazywać
na podstawie zapisanej historii trackera.

Strefy są wewnętrzne dla integracji i nie tworzą globalnych encji `zone.*`.
Dzięki temu dwa zegarki mogą mieć różne szkoły, nazwy i promienie.
Po usunięciu wszystkich stref danego zegarka jego tracker korzysta ze
standardowych stref HA; sensor Miejsce opisuje wyłącznie strefy CALMEAN.

## Pierwsza instalacja

1. Skopiuj `custom_components/calmean` do `/config/custom_components/calmean`.
2. Uruchom ponownie HA i odśwież przeglądarkę.
3. Ustawienia → Urządzenia i usługi → Dodaj integrację → **CALMEAN**.
4. Wklej token własnego konta; można wkleić sam token lub `Bearer TOKEN`.
5. W menu bocznym otwórz **Mapa CALMEAN** i ustaw strefy zegarków.

Minimalna deklarowana wersja HA: 2025.3. Kod uwzględnia również import
walidatorów używany w nowszych wersjach HA. Zgodność całego panelu wymaga
potwierdzenia na działającym HA. W tej wersji panel mapy i konfiguracji
jest przeznaczony dla administratorów; pozostałe encje są zwykłymi encjami HA.

W menu **Konfiguruj** integracji ustawisz częstotliwość odczytu API:
30–3600 s, domyślnie 60 s. Odświeżanie panelu pobiera jedynie ostatnie dane
z HA, nie wywołuje dodatkowo API CALMEAN. Nowe zegarki są wykrywane automatycznie.

## Jak uzyskać token Bearer

1. Wejdź na https://panel.calmean.com i zaloguj się na własne konto.
2. Naciśnij **F12**, otwórz **Network / Sieć** i odśwież stronę.
3. W filtrze wpisz **getAllDevice** i wybierz pasujące żądanie.
4. Otwórz **Headers → Request Headers** i skopiuj wartość **authorization**.
5. Wklej `Bearer TWOJ_TOKEN` lub sam token do konfiguracji CALMEAN w HA.


## Encje

| Encja | Dane |
| --- | --- |
| device_tracker | Ostatnie współrzędne i stan strefy |
| Bateria | Poziom w procentach |
| Aktywność CALMEAN | Pole `active`, bez zgadywania semantyki online/offline |
| Typ lokalizacji | Surowe `localizationType` |
| Ostatnia lokalizacja | `createTime` |
| Miejsce | Nazwa indywidualnej strefy albo Poza domem |

Jedno konto może obsługiwać wiele zegarków. Wiele kont nie jest jeszcze
obsługiwane. Usunięty z odpowiedzi API zegarek staje się niedostępny; wracający
zachowuje identyfikatory encji. Błąd sieci oznacza niedostępność encji,
a nie fałszywe „offline” zegarka.

## HACS / GitHub

Przed publikacją ustaw właściciela i repozytorium:

```sh
python scripts/prepare_repository.py terakompl --repository calmean-ha
```

Skrypt ustawia publiczne adresy oraz codeowner w `manifest.json`. Nie przyjmuje
tokenów. Utwórz publiczne repozytorium; zalecamy pełne wydanie GitHub
z tagiem `v0.2.3`. Bez wydania HACS może korzystać z domyślnej gałęzi.
W HACS dodaj jego adres jako **Niestandardowe repozytorium → Integracja**,
pobierz i uruchom ponownie HA. Nie oznacza to przyjęcia do domyślnego katalogu HACS.

## Dane i prywatność

Token przechowywany jest wyłącznie w config entry HA, formularz go ukrywa.
Kod nie loguje tokenu ani odpowiedzi API. Mapa korzysta z uwierzytelnionego
WebSocket HA; jej odczyt i zmiana stref wymagają administratora także po stronie
serwera. Statyczny plik JavaScript nie zawiera tokenów ani konfiguracji kont.
Zapis stref chroni przed nadpisaniem nowszych zmian z innego okna.

Config entries nie są osobnym szyfrowanym sejfem: dostęp do plików i backupów
HA daje dostęp do tokenu. Pozycje i nazwy mogą być zapisywane przez Recorder.
Nie publikuj `.storage`, tokenów ani prawdziwych odpowiedzi API.
Repozytorium zawiera wyłącznie sztuczne dane testowe.

Mapa pobiera kafelki z `tile.openstreetmap.org`; dostawca otrzymuje adres IP
przeglądarki i adresy kafelków określające oglądany obszar. Nie wysyłamy mu
nazw zegarków, stref ani tokenu. Brak internetu może uniemożliwić wyświetlenie
tła mapy; formularz współrzędnych nadal działa. Nie pobieramy skryptów z CDN,
nie robimy masowego pobierania kafelków ani map offline. Zachowana jest atrybucja
OpenStreetMap. Mapa używa projekcji Web Mercator, ograniczonej do ±85,0511°.

## API i ograniczenia bety

Endpoint: `POST https://apiwww.calmean.com/t/calmean.com/wwwview/1.0.0/getAllDevicesView?controlProfiles=true&sharedProfiles=true`.
Autoryzacja Bearer, standardowa walidacja HTTPS, timeout 20 s, brak przekierowań.
Nie implementujemy niepotwierdzonego logowania hasłem ani automatycznego
odświeżania tokenu. HTTP 401/403 uruchamia ponowne uwierzytelnienie.

Parser obsługuje listy i opakowania zawierające płaskie rekordy z polami
`deviceId`, `name`, `latitude`, `longitude`, `localizationType`, `createTime`,
`battery`, `active`. Zagnieżdżona lokalizacja w `localization` jest obsługiwana. Nie zgadujemy znaczenia `active` i kodów lokalizacji.
`createTime` interpretowany jest jako czas lokalizacji: epoch w s/ms lub
ISO 8601 ze strefą. Czas bez strefy i brak współrzędnych pozostają nieznane.

## Walidacja

```sh
python -m pip install -r requirements-test.txt
python -m unittest discover -s tests -v
python -m compileall -q custom_components
npm install
npm test
node --check custom_components/calmean/frontend/calmean-map.js
```

33 testy Python obejmuje normalizację, klienta HTTP, promień 50 m, niezależność
stref, migrację i zapis z kontrolą wersji. Testy handlerów korzystają z atrap
interfejsów HA. Test DOM sprawdza formularz, pinezkę, koła, zapis, konflikt,
edycję i usuwanie; nie jest testem renderowania przeglądarki ani pełnego HA.
Pełny test instalacji nowej wersji i wyglądu mapy w HA pozostaje do wykonania.

Architektura: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
Weryfikacja przed publikacją: [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md).


## Parser 0.2.3

Odpowiedź deviceView: współrzędne, typ i czas są odczytywane z localization. Bateria jest przeliczana z ułamka 0–1 na procenty. Wpisy DEVICE_PARENT / PARENT_APP są pomijane. Brak localization oznacza brak pozycji; lastActivityDate nie zastępuje czasu lokalizacji. Mapa pokazuje ostatnią pozycję API, bez wymuszania nowego odczytu zegarka.
