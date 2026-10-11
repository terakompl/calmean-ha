# 0.2.3

- Poprawiono przeliczanie długości geograficznej kliknięcia i przesuwania mapy: usunięto błędne przesunięcie o 180 stopni.
- Nowy URL modułu mapy odświeża cache przeglądarki.
- Istniejące błędnie zapisane strefy wymagają ponownego ustawienia.

# 0.2.2

- Obsługa deviceView/localization: współrzędne, typ i czas lokalizacji.
- Bateria API 0–1 przeliczana na procenty.
- Pomijanie aplikacji rodziców. Brak lokalizacji pozostaje nieznany.

# Changelog

## 0.2.1

- Naprawa dodawania stref w niezabezpieczonym kontekście lokalnego HTTP.
- Jawna polityka Referer obrazów OSM, zgodna z wymaganiami dostawcy.
- Formularz działa bez kafelków i bez pozycji API; osobny komunikat braku GPS.
- Początkowe centrowanie na rzeczywistej strefie Dom HA, jeżeli jest dostępna.
- Test regresji bez randomUUID, błędu kafelków i ręcznego zapisu bez GPS.

## 0.2.0

- Osobna Mapa CALMEAN w menu bocznym, bez konfiguracji YAML.
- Nazwane strefy osobno dla każdego zegarka; domyślnie 50 m.
- Edycja kliknięciem/pinezka lub ręczne współrzędne.
- Obrysy stref, wiele urządzeń, bateria i czas ostatniej pozycji.
- Edycja, usuwanie i kolejność rozpoznawania nakładających się stref.
- Migracja dawnych wspólnych stref, zachowanie tokenu i entity unique_id.
- Sensor Miejsce zwraca teraz nazwę strefy albo Poza domem.
- Panel i jego WebSocket wymagają administratora HA.
- Testy migracji, granicy 50 m, handlerów i logiki frontend DOM.

## 0.1.0

- Pierwsza beta: Config Flow, trackery, sensory, wspólny Dom/Szkoła.
