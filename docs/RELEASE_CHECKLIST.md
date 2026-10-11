# Weryfikacja 0.2.0 przed stabilną publikacją

- [ ] Sprawdzić zanonimizowany JSON i semantykę active/createTime.
- [ ] Sprawdzić aktualizację istniejącego HA oraz świeżą instalację.
- [ ] Sprawdzić migrację wspólnych stref i stabilność identyfikatorów encji.
- [ ] Potwierdzić sidebar, ładowanie mapy, komputer, telefon i tablet.
- [ ] Sprawdzić zapis 50 m, kliknięcie punktu, ręczne dane i obrysy.
- [ ] Sprawdzić różne szkoły dla różnych zegarków, nakładanie i kolejność stref.
- [ ] Sprawdzić role użytkowników: mapa i zapis tylko dla administratorów.
- [ ] Sprawdzić konflikt dwóch okien, edycję, usuwanie i pustą listę stref.
- [ ] Sprawdzić reauth, restart, 429/5xx i brak internetu.
- [ ] Zmienić automatyzacje sensora Miejsce na nowe nazwane stany.
- [ ] Ustawić prawdziwe repo/owner, sprawdzić CI, hassfest i walidację HACS.
- [ ] Potwierdzić brak danych prywatnych, dodać release v0.2.0.

Automatyczne testy zostały uruchomione lokalnie. Testy handlerów i DOM
używają atrap, nie zastępują pełnego uruchomienia Home Assistant ani
wizualnej weryfikacji mapy. Projekt pozostaje nieoficjalną wersją beta.
