# Vorkasse

Beschlüsse für die App **Extended Advance Payment Process**. Stand der Umsetzung unten. Englische Fassung: [advance_payment.md](advance_payment.md). ERPNext bleibt für Konten, Bank, **Mode of Payment** und dafür zuständig, welche Kunden eine Vorkasse-Vorlage bekommen.

## Welche Aufträge

Ob ein **Sales Order** ein Vorkasse-Auftrag ist, entscheidet sein Zahlungsplan. Das **Check**-Feld *Counts for Advance* (`custom_counts_for_advance`) am **Payment Term** markiert Anzahlungs-Terms. Es ist ein **Custom Field** neben *Mode of Payment*, exportiert in `custom/payment_term.json`. Hat eine Zeile in `payment_schedule` einen markierten **Payment Term**, gilt das Vorkasse-Verhalten. Aufträge ohne markierte Zeile bleiben unberührt.

Es gibt keine zweite Liste von Vorlagen in den Settings. Das Häkchen am **Payment Term** ist die einzige Stelle. Wer einen Anzahlungs-Term ohne Sperre will, legt einen zweiten **Payment Term** ohne Häkchen an.

Die Vorlage setzt der User am **Customer** oder am **Sales Order**. Die App vergibt sie nicht. Ändert der User den Zahlungsplan am Auftrag von Hand, zählt der Zahlungsplan, nicht die Vorlage.

**Extended Advance Payment Process Settings** zeigt im **HTML**-Feld *Advance payment templates* (`advance_templates_html`) alle **Payment Terms Template**, die einen markierten Term enthalten. Die Anzeige berechnet `get_advance_templates` bei jedem Öffnen. Sie speichert nichts.

`validate` am **Sales Order** setzt `custom_uses_advance_payment` und *Payable Advance* (`custom_payable_advance`). Beides passiert nur vor dem Buchen. Wird das Häkchen an einem **Payment Term** später gesetzt oder entfernt, ändert das gebuchte Aufträge nicht.

## Wann der Auftrag bezahlt ist

`advance_paid` ist das eingegangene Geld aus dem Advance Payment Ledger. `advance_payment_status` zählt nur **Payment Request** und entscheidet hier nicht.

Der Vergleich gilt, wenn `party_account_currency` und `currency` am **Sales Order** gleich sind. Sonst ist der Auftrag für diese App nicht bezahlt, weil die Beträge in verschiedenen Währungen stehen.

Der Betrag, der da sein muss, ist die Summe von `payment_amount` aller Zeilen in `payment_schedule`, deren **Payment Term** das Häkchen hat. So zählen auch mehrere Anzahlungszeilen, zum Beispiel 30 % und 20 %. Volle Vorkasse ist ein markierter Term mit 100 %.

```python
due_now = sum(row.payment_amount for row in doc.payment_schedule if <Payment Term hat custom_counts_for_advance>)
open_amount = due_now - flt(doc.advance_paid)
```

Dieselbe Summe steht im **Currency**-Feld *Payable Advance* (`custom_payable_advance`) am **Sales Order**. Es ist *Read Only* und nur sichtbar, wenn `custom_uses_advance_payment` gesetzt ist. `validate` füllt es über `get_advance_due`. `is_paid` nutzt dieselbe Funktion, damit Anzeige und Prüfung nie auseinanderlaufen.

`open_amount` ist der noch fehlende Betrag. Ist die Anzahlung höher als `due_now`, wird `open_amount` negativ und der Auftrag gilt als bezahlt.

Die Toleranz liegt in **Extended Advance Payment Process Settings**:

- **Check** *Allow payment tolerance* (`allow_tolerance`)
- **Currency** *Payment tolerance* (`payment_tolerance`), sichtbar nur wenn der Schalter an ist (`depends_on`: `allow_tolerance`). Standard `0.02` mit Punkt.

Ist der Schalter an, darf `open_amount` höchstens `payment_tolerance` sein. Ist er aus, muss `advance_paid` den fälligen Betrag `due_now` erreichen. Die Toleranz begrenzt nur, wie weit die Zahlung darunter liegen darf.

```python
tolerance = flt(settings.payment_tolerance) if settings.allow_tolerance else 0
paid = open_amount <= tolerance
```

Die Funktion `is_paid` in `sales_order.py` bildet das ab. `require_release` ruft sie auf, bevor eine Sperre greift.

## Reservierung

Reservieren schaltet der System Manager in **Stock Settings**, Feld *Enable Stock Reservation* (`enable_stock_reservation`). Die App schaltet das nicht ein und setzt auch nicht *Auto Reserve Stock* (`auto_reserve_stock`). Das würde jeden **Sales Order**, **Work Order** und **Production Plan** reservieren. *Allow Negative Stock* und die Reservierung können in ERPNext nicht gleichzeitig an sein.

*Allow reservation for not paid* (`allow_reservation`) gilt nur für Vorkasse-Aufträge, und nur wenn `enable_stock_reservation` an ist. Dann setzt die App am **Sales Order** das vorhandene Feld `reserve_stock`. ERPNext legt daraus die **Stock Reservation Entry** an. Ist die Reservierung im System aus, lässt die App `reserve_stock` unverändert.

Der Hook steht in `hooks.py` unter `# Document Events`: **Sales Order**, Ereignis `validate`, Funktion `validate`. Die setzt `custom_uses_advance_payment` und ruft danach `set_reserve_stock` auf. Ist die Reservierung im System aus, bleibt die Freigabe trotzdem möglich. Der Hook läuft nach `enable_auto_reserve_stock` in ERPNext.

`reserve_stock` am **Sales Order** steuert nur die Reservierung beim Buchen. Die Zeilen (**Sales Order Item**, Feld `reserve_stock`, Standard an, *Allow on Submit*) lässt die App unverändert. Deshalb zeigt der gebuchte Auftrag weiter den Button *Stock Reservation* > *Reserve*. Ist `allow_reservation` aus, sperrt `block_stock_reservation` jede **Stock Reservation Entry** zu einem Vorkasse-Auftrag, bis er bezahlt ist oder die Lieferfreigabe hat. Reservieren zählt als Liefern, weil die Ware dann für den Kunden zurückliegt. Nach der Zahlung reserviert der User über denselben Button.

## Freigabe

Bestellen und Liefern sind zwei Freigaben am **Sales Order**. Eine Rolle darf beide setzen. Eine zweite Rolle kommt erst dazu, wenn Einkauf und Versand von verschiedenen Leuten freigegeben werden.

Bestellen umfasst **Material Request**, **Purchase Order**, **Work Order** und **Subcontracting Order**. Die **Subcontracting Order** hat kein eigenes Feld für den Auftrag. Die App liest ihn aus den Zeilen der verknüpften **Purchase Order**. Die **Subcontracting Inward Order** (der Kunde liefert das Material) hat das Pflichtfeld `sales_order` und zählt ebenfalls zum Bestellen. Die Ware bleibt bei der Firma. Ein **Production Plan** bleibt frei, Planen und das Bestellen der Rohstoffe darin auch. **Material Request**-Zeilen mit gesetztem `production_plan` überspringt `block_order`. Eine **Material Request** direkt aus dem **Sales Order** bleibt gesperrt.

Liefern umfasst **Delivery Note** und **Sales Invoice** mit *Update Stock* (`update_stock`). Drop-Ship gehört zur Lieferung: eine **Purchase Order** mit *Delivered by Supplier* (`delivered_by_supplier`) schickt die Ware an den Kunden und bleibt gesperrt, solange die Lieferfreigabe fehlt.

Eine **Pick List** bucht kein Lager und erzeugt keine Lieferung. Sie darf deshalb auch ohne Zahlung angelegt werden. Die Auslieferung bleibt am **Delivery Note** gesperrt. Hat der **Sales Order** schon `stock_reserved_qty`, lehnt ERPNext eine **Pick List** mit Zweck "Delivery" ab, bis die Reservierung aufgehoben ist. Das bleibt die Standardprüfung.

Die Rolle steht in **Extended Advance Payment Process Settings** als **Link** *Role to allow Processing of blocked Sales Orders* (`allow_processing_role`) auf **Role**. Die Felder am **Sales Order** sind **Custom Field** neben *Advance Paid*. Pro Seite ein **Check**, ein **Link** auf **User** und ein **Datetime**. Alle sechs sind *Read Only* und *Allow on Submit*. Die Freigabe schreibt der Button *Advance Payment* am gebuchten **Sales Order**. Die Methode `set_release` in `sales_order.py` prüft `allow_processing_role` und das Schreibrecht am **Sales Order**. Beides ist nötig, weil die Methode auch direkt aufrufbar ist und `db_set` keine Rechte prüft. Danach setzt oder leert Haken, User und Uhrzeit für eine Seite. Das Formular hängt in `public/js/sales_order.js`, eingebunden über `doctype_js` in `hooks.py`.

Exportiert sind sie über **Customize Form**, Aktion *Export Customizations*, Modul **Extended Advance Payment Process**, *Sync on Migrate* an. Die Datei ist `extended_advance_payment_process/custom/sales_order.json`. Beim `bench migrate` legt Frappe die Felder daraus an.

- `custom_order_released`, `custom_order_released_by`, `custom_order_released_on`
- `custom_delivery_released`, `custom_delivery_released_by`, `custom_delivery_released_on`

Beim Freigeben schreibt die App den angemeldeten User und die Uhrzeit. Ein Widerruf leert nur diese Seite. Bestehende Belege bleiben. Was noch nicht bestellt oder geliefert ist, wird wieder gesperrt.

Der Status "On Hold" am **Sales Order** ist dafür nicht geeignet. Er blockiert nicht jede Beschaffung serverseitig und nimmt die klassische Lagerreservierung weg. **Payment Entry** bleibt dabei möglich, die Sperre soll das auch.

## Liegedauer

Der Script Report **Advance Payment Reserved Stock** zeigt, welche Ware für Vorkasse-Aufträge reserviert ist und wie lange schon. Er liegt im Modul **Extended Advance Payment Process** und hängt an **Stock Reservation Entry**. Öffnen dürfen ihn "Stock User", "Stock Manager", "Sales User" und "Sales Manager".

Eine Zeile ist eine offene **Stock Reservation Entry** zu einem gebuchten **Sales Order** mit `custom_uses_advance_payment`. Offen heißt Status "Reserved", "Partially Reserved", "Partially Delivered" oder "Partially Used". Die älteste Reservierung steht oben.

| Spalte | Bedeutung |
|---|---|
| *Sales Order*, *Customer* | Der Vorkasse-Auftrag |
| *Item*, *Warehouse* | Was wo reserviert ist |
| *Reserved Qty* | Noch reserviert: `reserved_qty` minus `delivered_qty` der Reservierung |
| *Reserved Since* | Erstellzeitpunkt der **Stock Reservation Entry** |
| *Days Reserved* | Tage seit *Reserved Since* bis heute |
| *Qty in Stock* | Lagerbestand des Artikels in diesem Lager (`actual_qty` aus **Bin**) |
| *Qty on Open Sales Orders* | Menge des Artikels auf allen offenen **Sales Order** für dieses Lager (`reserved_qty` aus **Bin**), nicht nur Vorkasse |
| *Payable Advance*, *Advance Paid*, *Paid* | Fälliger Betrag, eingegangenes Geld und ob `is_paid` den Auftrag als bezahlt sieht |
| *Stock Reservation Entry* | Link auf die Reservierung |

Filter: *Company*, *Customer*, *Sales Order*, *Item* und *Unpaid Only*. *Unpaid Only* ist standardmäßig an und blendet bezahlte Aufträge aus.

Der Bericht hat nur Zeilen, wenn ERPNext eine **Stock Reservation Entry** angelegt hat. Ist `allow_reservation` aus, entsteht eine solche Reservierung erst nach Zahlung oder Lieferfreigabe. Mit *Unpaid Only* bleibt der Bericht dann meist leer, ohne den Filter zeigt er diese Reservierungen trotzdem.

Der Standardbericht **Reserved Stock** hat einen Erstellzeitpunkt, aber kein Alter in Tagen, keinen Lagerbestand und keinen Filter auf unbezahlte Vorkasse-Aufträge.
