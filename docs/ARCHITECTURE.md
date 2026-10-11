# Architektura 0.2.0

| Moduł | Odpowiedzialność |
| --- | --- |
| api.py / coordinator.py | Jeden cykl odczytu na konto, dane wspólne dla encji |
| models.py | Normalizacja, indywidualne strefy, walidacja i migracja |
| config_flow.py | Token, ponowne uwierzytelnienie, odstęp odczytów |
| entity.py | Rejestr urządzeń, stabilne unique_id, wykrywanie nowych zegarków |
| device_tracker.py | Pozycja GPS i strefa przypisana do danego urządzenia |
| sensor.py / binary_sensor.py | Bateria, typ, czas, miejsce i active |
| panel.py | Rejestracja widoku i uwierzytelnione komendy WebSocket |
| frontend/calmean-map.js | Mapa, obrysy, wybór urządzeń, edytor i obsługa dotyku |

`options.device_zones[deviceId]` to uporządkowana lista stref. Strefa ma
`id`, `name`, `kind`, `latitude`, `longitude`, `radius`. Promień nowych stref
wynosi 50–5000 m; maksymalnie 30 stref na urządzenie. Pierwszy pasujący obrys
wygrywa. Nie tworzymy globalnych `zone.*` ani nie zmieniamy `zone.home`.

Stare wspólne `options.zones` są kopiowane jednorazowo do zegarków dostępnych
podczas aktualizacji. Migracja zachowuje dotychczasowy promień, również poniżej
50 m; przy późniejszym zapisie trzeba zwiększyć go do co najmniej 50 m.
Zegarki niewidoczne przy migracji wymagają później własnego ustawienia stref.
Token i unique_id nie zmieniają się.

`calmean/map` zwraca pozycje i strefy bez tokenu. `calmean/zones/save` zapisuje
wyłącznie listę konkretnego zegarka, zachowując ustawienia pozostałych.
Obie komendy wymagają administratora HA. Całkowity `zone_revision` chroni przed
nadpisaniem zmian wykonanych w równoległym oknie. To synchroniczne operacje
w pętli HA, bez przerw await między kontrolą rewizji a zapisem.

Zmiana stref publikuje ponownie stany encji bez odpytywania chmury i bez
przeładowywania panelu. Powiadomienie koordynatora zachowuje stan niedostępności
po wcześniejszym błędzie sieci. Zmiana odstępu odczytów aktualizuje koordynator.

Panel jest web componentem obsługiwanym przez panel_custom. Statyczny moduł JS
jest serwowany lokalnie, a uwierzytelnienie używa już otwartej sesji HA.
Jedynym zewnętrznym zasobem mapy są kafelki OSM. Warstwa SVG przedstawia
punkty i promienie w Web Mercator, z korektą skali szerokością geograficzną.
Mapa pokazuje ostatnie pozycje, bez własnego magazynu historii i tras.
