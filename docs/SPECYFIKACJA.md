# Specyfikacja wymagań — CALMEAN dla Home Assistant

Wersja: 0.2.1 beta. Nieoficjalna integracja społecznościowa; projekt nie jest produktem CALMEAN. Dystrybucja: publiczne repozytorium GitHub dodawane w HACS jako niestandardowe repozytorium typu Integracja.

## Wymagania użytkownika

| Wymaganie | Opis |
| --- | --- |
| Home Assistant | Zadeklarowane minimum 2025.3; nie jest to potwierdzona macierz zgodności wszystkich wersji. Przed wydaniem należy sprawdzić instalację na rzeczywistym HA. |
| HACS | Zainstalowany i skonfigurowany, jeśli instalacja ma odbywać się przez HACS. Alternatywnie instalacja ręczna. |
| Konto CALMEAN | Własne konto z urządzeniami widocznymi w panel.calmean.com i prawidłowym tokenem Authorization. |
| Internet | HA musi łączyć się z API CALMEAN; przeglądarka z dostawcą map OpenStreetMap. |
| Uprawnienia | Administrator HA do instalacji, konfiguracji oraz panelu Mapa CALMEAN. |
| Przeglądarka | Aktualna przeglądarka obsługująca moduły JavaScript i WebSocket. |

Nie jest wymagane programowanie ani konfiguracja YAML. Token pochodzi z CALMEAN, a nie z Home Assistant.

## Pobranie tokenu Bearer

1. Wejdź na https://panel.calmean.com i zaloguj się na własne konto.
2. Otwórz narzędzia programistyczne klawiszem **F12** (na niektórych komputerach Fn + F12).
3. Wybierz zakładkę **Network / Sieć**.
4. Odśwież stronę przy otwartej zakładce Network, aby pojawiły się żądania.
5. W filtrze wpisz **getAllDevice**. Pasuje również do żądania `getAllDevicesView`.
6. Wybierz żądanie i otwórz **Headers / Nagłówki → Request Headers / Nagłówki żądania**.
7. Odszukaj **authorization** i skopiuj jego wartość: `Bearer TWOJ_TOKEN`.
8. Wklej wartość do konfiguracji CALMEAN w HA. Integracja przyjmuje pełną wartość z prefiksem Bearer albo sam token.

Jeśli brak żądania, usuń inne filtry i odśwież widok urządzeń w panelu. Token daje dostęp do danych konta: nie publikuj go, zrzutów nagłówków ani plików HAR. Nie umieszczaj go w GitHub. Po wygaśnięciu należy pobrać nowy i wykonać ponowne uwierzytelnienie; automatyczne odświeżanie tokenu nie jest zaimplementowane.

## Wymagania funkcjonalne i kryteria odbioru

| ID | Wymaganie | Kryterium odbioru |
| --- | --- | --- |
| F01 | Konfiguracja przez interfejs HA | Dodanie CALMEAN i poprawnego tokenu tworzy urządzenia oraz encje bez YAML. |
| F02 | Wiele zegarków jednego konta | Każdy zegarek otrzymuje własne encje; wiele kont nie jest obsługiwane. |
| F03 | Odczyt lokalizacji i danych | Tracker, bateria, aktywność CALMEAN, typ i czas lokalizacji oraz Miejsce odzwierciedlają dostępne pola API. Brak danych pozostaje nieznany. |
| F04 | Osobny widok mapy | Administrator otwiera Mapa CALMEAN, wybiera jeden lub wszystkie zegarki, przesuwa i przybliża mapę. |
| F05 | Indywidualne strefy | Dom, Szkoła i własne lokalizacje zapisane dla jednego zegarka nie zmieniają stref innych zegarków. |
| F06 | Promień strefy | Domyślnie 50 m, zakres 50–5000 m. To promień rozpoznawania miejsca, nie gwarancja dokładności GPS. |
| F07 | Zarządzanie strefami | Dodawanie, edycja, usuwanie i zmiana kolejności; punkt z kliknięcia mapy lub ręcznych współrzędnych. Maksymalnie 30 stref na urządzenie. |
| F08 | Nakładanie stref | Pierwsza pasująca strefa na liście określa Miejsce. |
| F09 | Aktualizowanie danych | Jeden wspólny odczyt konta: domyślnie co 60 s, konfigurowalny zakres 30–3600 s. |
| F10 | Obsługa błędów | 401/403 API wymagają ponownego uwierzytelnienia; błędy połączenia powodują niedostępność encji. Brak kafelków nie blokuje ręcznego ustawienia strefy. |
| F11 | Trwałość konfiguracji | Restart zachowuje token i strefy; aktualizacja nie wymaga usuwania integracji. |

Tracker zwraca `home` w strefie typu Dom, nazwę pozostałej pasującej strefy i `not_home` poza nimi. Gdy zegarek nie ma stref CALMEAN, tracker korzysta ze standardowych stref HA. Sensor Miejsce opisuje wyłącznie strefy CALMEAN, poza nimi zwraca `Poza domem`. Strefy nie tworzą globalnych encji `zone.*`.

## Wymagania techniczne i prywatność

- Kod integracji znajduje się w `custom_components/calmean/`; frontend jest dostarczany razem z integracją i nie wymaga skryptów CDN.
- API: HTTPS POST `getAllDevicesView`, Authorization Bearer, timeout 20 s. Jeden koordynator udostępnia dane wszystkim encjom.
- Parser obsługuje rekordy z polami `deviceId`, `name`, `latitude`, `longitude`, `battery`, `active`, `localizationType`, `createTime`. Zmiany schematu API mogą wymagać aktualizacji.
- Pole active jest prezentowane jako Aktywność CALMEAN; jego znaczenie online/offline nie zostało potwierdzone. Interpretacja createTime jako czasu lokalizacji wymaga zgodności z rzeczywistą odpowiedzią API.
- Token przechowywany w konfiguracji HA; nie jest wpisywany w kod frontendowy ani logowany. Pliki konfiguracji i backupy HA mogą zawierać token.
- WebSocket panelu wymaga uwierzytelnienia i administratora. Kontrola wersji zapisu chroni strefy przed nadpisaniem zmian z drugiego okna.
- OpenStreetMap otrzymuje IP przeglądarki i zapytania o kafelki oglądanego obszaru, bez tokenu i nazw urządzeń. Dane lokalizacji mogą być zapisywane w historii HA.

## Wymagania dystrybucji

Publiczne repozytorium GitHub z README, licencją MIT, hacs.json, manifest.json, opisem, tematami i włączonym Issues. Manifest musi wskazywać rzeczywistego właściciela, adres dokumentacji, zgłoszeń i codeowners. W katalogu integracji znajduje się ikona brand/icon.png. GitHub Actions uruchamia testy Python, frontend, hassfest i walidację HACS. Pełne wydanie GitHub z tagiem v0.2.1 jest zalecane; nie jest warunkiem samego dodania niestandardowego repozytorium.

Przed udostępnieniem: brak tokenów i danych osobowych, poprawna struktura repozytorium, zielone walidacje oraz rzeczywisty test pobrania przez HACS, restartu, konfiguracji i zapisu stref. Testy jednostkowe i DOM nie zastępują testu pełnego HA.

## Poza zakresem wersji

Logowanie hasłem CALMEAN, automatyczne odnawianie tokenu, wiele kont, historia tras w osobnym panelu, mapy offline, wysyłanie poleceń do zegarków i gwarantowana dokładność pozycji GPS.
