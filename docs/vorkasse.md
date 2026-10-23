# Vorkasse

Beschlüsse für die App **Extended Advance Payment Process**. Stand der Umsetzung unten. ERPNext bleibt für Konten, Bank, **Mode of Payment** und dafür zuständig, welche Kunden eine Vorkasse-Vorlage bekommen.

## Welche Aufträge

Die App prüft am **Sales Order** das Feld `payment_terms_template`. Steht der Wert in **Extended Advance Payment Process Settings**, Tabelle *Payment templates used* (`templates_used`), gilt das Vorkasse-Verhalten. Andere Vorlagen und Aufträge ohne Vorlage bleiben unberührt.

Die Vorlage setzt der User am **Customer** oder am **Sales Order**. Die App vergibt sie nicht.

Die Zeilen der Tabelle sind der Child-DocType **Extended Advance Payment Process Terms**. Das Link-Feld *Payment Term Templates* (`payment_term_templates`) zeigt auf **Payment Terms Template**. Ein Feld vom Typ **Table** kann nicht direkt auf **Payment Terms Template** zeigen, weil das kein Child-DocType ist.

## Wann der Auftrag bezahlt ist

`advance_paid` ist das eingegangene Geld aus dem Advance Payment Ledger. `advance_payment_status` zählt nur **Payment Request** und entscheidet hier nicht.

Der Vergleich gilt, wenn `party_account_currency` und `currency` am **Sales Order** gleich sind. Sonst ist der Auftrag für diese App nicht bezahlt, weil die Beträge in verschiedenen Währungen stehen.

Die Summe ist `rounded_total`, und wenn die Rundung aus ist, `grand_total`. ERPNext steuert das über **Global Defaults**, Feld *Disable Rounded Total* (`disable_rounded_total`), und über dasselbe Feld am Auftrag. Die App hat dafür keine eigene Einstellung.

```python
total = flt(doc.rounded_total) or flt(doc.grand_total)
open_amount = total - flt(doc.advance_paid)
```

`open_amount` ist der noch fehlende Betrag. Ist die Anzahlung höher als `total`, wird `open_amount` negativ und der Auftrag gilt als bezahlt.

Die Toleranz liegt in **Extended Advance Payment Process Settings**:

- **Check** *Allow payment tolerance* (`allow_tolerance`)
- **Currency** *Payment tolerance* (`payment_tolerance`), sichtbar nur wenn der Schalter an ist (`depends_on`: `allow_tolerance`). Standard `0.02` mit Punkt.

Ist der Schalter an, darf `open_amount` höchstens `payment_tolerance` sein. Ist er aus, muss `advance_paid` das Total erreichen. Die Toleranz begrenzt nur, wie weit die Zahlung unter dem Total liegen darf.

```python
tolerance = flt(settings.payment_tolerance) if settings.allow_tolerance else 0
paid = open_amount <= tolerance
```

Die Funktion `is_paid` in `sales_order.py` bildet das ab. `require_release` ruft sie auf, bevor eine Sperre greift.

## Reservierung

Reservieren schaltet der System Manager in **Stock Settings**, Feld *Enable Stock Reservation* (`enable_stock_reservation`). Die App schaltet das nicht ein und setzt auch nicht *Auto Reserve Stock* (`auto_reserve_stock`). Das würde jeden **Sales Order**, **Work Order** und **Production Plan** reservieren. *Allow Negative Stock* und die Reservierung können in ERPNext nicht gleichzeitig an sein.

*Allow reservation for not paid* (`allow_reservation`) gilt nur für Aufträge aus der Vorlagen-Tabelle, und nur wenn `enable_stock_reservation` an ist. Dann setzt die App am **Sales Order** das vorhandene Feld `reserve_stock`. ERPNext legt daraus die **Stock Reservation Entry** an. Ist die Reservierung im System aus, lässt die App `reserve_stock` unverändert.

Der Hook steht in `hooks.py` unter `# Document Events`: **Sales Order**, Ereignis `validate`, Funktion `validate`. Die setzt `custom_uses_advance_payment` und ruft danach `set_reserve_stock` auf. Ist die Reservierung im System aus, bleibt die Freigabe trotzdem möglich. Der Hook läuft nach `enable_auto_reserve_stock` in ERPNext.

## Freigabe

Bestellen und Liefern sind zwei Freigaben am **Sales Order**. Eine Rolle darf beide setzen. Eine zweite Rolle kommt erst dazu, wenn Einkauf und Versand von verschiedenen Leuten freigegeben werden.

Bestellen umfasst **Material Request**, **Purchase Order** und **Work Order**. Die Ware bleibt bei der Firma. Ein **Production Plan** bleibt frei, Planen und das Bestellen der Rohstoffe darin auch. **Material Request**-Zeilen mit gesetztem `production_plan` überspringt `block_order`. Eine **Material Request** direkt aus dem **Sales Order** bleibt gesperrt.

Liefern umfasst **Delivery Note** und **Sales Invoice** mit *Update Stock* (`update_stock`). Drop-Ship gehört zur Lieferung: eine **Purchase Order** mit *Delivered by Supplier* (`delivered_by_supplier`) schickt die Ware an den Kunden und bleibt gesperrt, solange die Lieferfreigabe fehlt.

Eine **Pick List** bucht kein Lager und erzeugt keine Lieferung. Sie darf deshalb auch ohne Zahlung angelegt werden. Die Auslieferung bleibt am **Delivery Note** gesperrt. Hat der **Sales Order** schon `stock_reserved_qty`, lehnt ERPNext eine **Pick List** mit Zweck "Delivery" ab, bis die Reservierung aufgehoben ist. Das bleibt die Standardprüfung.

Die Rolle steht in **Extended Advance Payment Process Settings** als **Link** *Allow Processing Role* (`allow_processing_role`) auf **Role**. Die Felder am **Sales Order** sind **Custom Field** neben *Advance Paid*. Pro Seite ein **Check**, ein **Link** auf **User** und ein **Datetime**. Alle sechs sind *Read Only* und *Allow on Submit*. Die Freigabe schreibt der Button *Advance Payment* am gebuchten **Sales Order**. Die Methode `set_release` in `sales_order.py` prüft `allow_processing_role` und setzt oder leert Haken, User und Uhrzeit für eine Seite. Das Formular hängt in `public/js/sales_order.js`, eingebunden über `doctype_js` in `hooks.py`.

Exportiert sind sie über **Customize Form**, Aktion *Export Customizations*, Modul **Extended Advance Payment Process**, *Sync on Migrate* an. Die Datei ist `extended_advance_payment_process/custom/sales_order.json`. Beim `bench migrate` legt Frappe die Felder daraus an.

- `custom_order_released`, `custom_order_released_by`, `custom_order_released_on`
- `custom_delivery_released`, `custom_delivery_released_by`, `custom_delivery_released_on`

Beim Freigeben schreibt die App den angemeldeten User und die Uhrzeit. Ein Widerruf leert nur diese Seite. Bestehende Belege bleiben. Was noch nicht bestellt oder geliefert ist, wird wieder gesperrt.

Der Status "On Hold" am **Sales Order** ist dafür nicht geeignet. Er blockiert nicht jede Beschaffung serverseitig und nimmt die klassische Lagerreservierung weg. **Payment Entry** bleibt dabei möglich, die Sperre soll das auch.

## Liegedauer

Ein Bericht zeigt, wie lange reservierte Ware für diese Aufträge liegt. Er hat nur Zeilen, wenn `allow_reservation` an ist und ERPNext tatsächlich eine **Stock Reservation Entry** erzeugt hat. Der Standardbericht **Reserved Stock** hat einen Erstellzeitpunkt, aber kein Alter in Tagen und keinen Filter auf unbezahlte Vorkasse-Aufträge.

## Noch nicht gebaut

- Liegedauer-Bericht. Er hat nur Zeilen, wenn `allow_reservation` an ist und ERPNext eine **Stock Reservation Entry** erzeugt hat.
