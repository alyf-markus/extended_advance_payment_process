# Advance Payment

Decisions for the **Extended Advance Payment Process** app. The German version is [vorkasse.md](vorkasse.md). ERPNext stays in charge of accounts, banking, **Mode of Payment** and of which customers get an advance payment template.

## Which orders

A **Sales Order**'s payment schedule decides whether it is an advance payment order. The **Check** field *Counts for Advance* (`custom_counts_for_advance`) on **Payment Term** marks advance terms. It is a **Custom Field** next to *Mode of Payment*. If a row in `payment_schedule` has a flagged **Payment Term**, the advance payment behaviour applies. Orders without a flagged row are not affected.

There is no second list of templates in the settings. The flag on the **Payment Term** is the only place. If you want an advance term without the block, create a second **Payment Term** without the flag.

The user sets the template on the **Customer** or the **Sales Order**. The app does not assign it. If the user edits the payment schedule on the order by hand, the schedule counts, not the template.

**Extended Advance Payment Process Settings** shows all **Payment Terms Template** records that contain a flagged term in the **HTML** field *Advance payment templates* (`advance_templates_html`). `get_advance_templates` calculates the list every time the form opens. It stores nothing.

`validate` on the **Sales Order** sets `custom_uses_advance_payment` and *Payable Advance* (`custom_payable_advance`). Both happen only before submit. Setting or removing the flag on a **Payment Term** later does not change submitted orders.

## When the order is paid

`advance_paid` is the money received, taken from the Advance Payment Ledger. `advance_payment_status` only counts **Payment Request** and does not decide anything here.

The comparison only works if `party_account_currency` and `currency` on the **Sales Order** are the same. Otherwise the order is not paid as far as this app is concerned, because the amounts are in different currencies.

The amount that must be received is the sum of `payment_amount` of all rows in `payment_schedule` whose **Payment Term** is flagged. This also covers several advance rows, for example 30 % and 20 %. A full advance payment is one flagged term with 100 %.

```python
due_now = sum(row.payment_amount for row in doc.payment_schedule if <Payment Term has custom_counts_for_advance>)
open_amount = due_now - flt(doc.advance_paid)
```

The same sum is shown in the **Currency** field *Payable Advance* (`custom_payable_advance`) on the **Sales Order**. It is *Read Only* and only visible when `custom_uses_advance_payment` is set. `validate` fills it through `get_advance_due`. `is_paid` uses the same function, so the displayed amount and the check never disagree.

`open_amount` is the amount still missing. If the advance received is higher than `due_now`, `open_amount` becomes negative and the order counts as paid.

The tolerance lives in **Extended Advance Payment Process Settings**:

- **Check** *Allow payment tolerance* (`allow_tolerance`)
- **Currency** *Payment tolerance* (`payment_tolerance`), only visible when the switch is on (`depends_on`: `allow_tolerance`). Default `0.02`.

If the switch is on, `open_amount` may be at most `payment_tolerance`. If it is off, `advance_paid` must reach the amount due, `due_now`. The tolerance only limits how far the payment may fall short of it.

```python
tolerance = flt(settings.payment_tolerance) if settings.allow_tolerance else 0
paid = open_amount <= tolerance
```

The function `is_paid` in `sales_order.py` implements this. `require_release` calls it before any block applies.

## Reservation

The System Manager turns reservation on in **Stock Settings**, field *Enable Stock Reservation* (`enable_stock_reservation`). The app does not turn it on and does not set *Auto Reserve Stock* (`auto_reserve_stock`) either. That would reserve every **Sales Order**, **Work Order** and **Production Plan**. In ERPNext, *Allow Negative Stock* and reservation cannot be on at the same time.

*Allow reservation for not paid* (`allow_reservation`) only applies to advance payment orders, and only when `enable_stock_reservation` is on. The app then sets the existing field `reserve_stock` on the **Sales Order**. ERPNext creates the **Stock Reservation Entry** from it. If reservation is off system-wide, the app leaves `reserve_stock` unchanged.

The hook is in `hooks.py` under `# Document Events`: **Sales Order**, event `validate`, function `validate`. It sets `custom_uses_advance_payment` and then calls `set_reserve_stock`. If reservation is off system-wide, releasing the order still works. The hook runs after `enable_auto_reserve_stock` in ERPNext.

`reserve_stock` on the **Sales Order** only controls reservation on submit. The app leaves the rows unchanged (**Sales Order Item**, field `reserve_stock`, on by default, *Allow on Submit*). That is why the submitted order still shows the button *Stock Reservation* > *Reserve*. If `allow_reservation` is off, `block_stock_reservation` blocks every **Stock Reservation Entry** for an advance payment order until it is paid or has the delivery release. Reserving counts as delivering, because the goods are then set aside for the customer. After payment, the user reserves through the same button.

## Release

Ordering and delivering are two releases on the **Sales Order**. One role may set both. A second role is only added once purchasing and shipping are released by different people.

Ordering covers **Material Request**, **Purchase Order**, **Work Order** and **Subcontracting Order**. The **Subcontracting Order** has no field of its own for the order. The app reads it from the rows of the linked **Purchase Order**. The **Subcontracting Inward Order** (the customer supplies the material) has the mandatory field `sales_order` and also counts as ordering. The goods stay with the company. A **Production Plan** stays unblocked, and so do planning and ordering raw materials in it. `block_order` skips **Material Request** rows with `production_plan` set. A **Material Request** created directly from the **Sales Order** stays blocked.

Delivering covers **Delivery Note** and **Sales Invoice** with *Update Stock* (`update_stock`). Drop shipping belongs to delivering: a **Purchase Order** with *Delivered by Supplier* (`delivered_by_supplier`) sends the goods to the customer and stays blocked as long as the delivery release is missing.

A **Pick List** does not post stock and does not create a delivery. It may therefore be created without payment. Shipping stays blocked on the **Delivery Note**. If the **Sales Order** already has `stock_reserved_qty`, ERPNext rejects a **Pick List** with purpose "Delivery" until the reservation is removed. That remains the standard check.

The role is set in **Extended Advance Payment Process Settings** as **Link** *Role to allow Processing of blocked Sales Orders* (`allow_processing_role`) to **Role**. The fields on the **Sales Order** are **Custom Field** records next to *Advance Paid*. Each side has a **Check**, a **Link** to **User** and a **Datetime**. All six are *Read Only* and *Allow on Submit*. The button *Advance Payment* on the submitted **Sales Order** writes the release. The method `set_release` in `sales_order.py` checks `allow_processing_role` and write permission on the **Sales Order**. Both are needed, because the method can also be called directly and `db_set` does not check permissions. It then sets or clears the flag, user and time for one side. The form script is `public/js/sales_order.js`, included through `doctype_js` in `hooks.py`.

All custom fields of the app are defined in `setup.py`, function `get_custom_fields`. `make_custom_fields` runs on `after_install` and `after_migrate` and uses `create_custom_fields` to create or update only these fields. Custom fields of other apps and property setters stay untouched. `before_uninstall` removes only the app's own fields. Changes to these fields belong in `setup.py`, not in **Customize Form**, because the next `bench migrate` would reset them. The release fields have *No Copy*, so a duplicated or amended order starts without a release.

- `custom_order_released`, `custom_order_released_by`, `custom_order_released_on`
- `custom_delivery_released`, `custom_delivery_released_by`, `custom_delivery_released_on`

On release, the app records the logged-in user and the time. Revoking clears only that side. Existing documents stay. Whatever has not been ordered or delivered yet is blocked again.

The status "On Hold" on the **Sales Order** is not suitable for this. It does not block every kind of procurement on the server and it removes the classic stock reservation. **Payment Entry** stays possible with it, and the block should allow that too.

## Reservation age

The script report **Advance Payment Reserved Stock** shows which goods are reserved for advance payment orders and for how long. It lives in the module **Extended Advance Payment Process** and is attached to **Stock Reservation Entry**. "Stock User", "Stock Manager", "Sales User" and "Sales Manager" may open it.

Each row is an open **Stock Reservation Entry** for a submitted **Sales Order** with `custom_uses_advance_payment`. Open means status "Reserved", "Partially Reserved", "Partially Delivered" or "Partially Used". The oldest reservation is at the top.

| Column | Meaning |
|---|---|
| *Sales Order*, *Customer* | The advance payment order |
| *Item*, *Warehouse* | What is reserved and where |
| *Reserved Qty* | Still reserved: `reserved_qty` minus `delivered_qty` of the reservation |
| *Reserved Since* | Creation time of the **Stock Reservation Entry** |
| *Days Reserved* | Days from *Reserved Since* until today |
| *Qty in Stock* | Stock of the item in this warehouse (`actual_qty` from **Bin**) |
| *Qty on Open Sales Orders* | Quantity of the item on all open **Sales Order** records for this warehouse (`reserved_qty` from **Bin**), not only advance payment orders |
| *Payable Advance*, *Advance Paid*, *Paid* | Amount due, money received and whether `is_paid` considers the order paid |
| *Stock Reservation Entry* | Link to the reservation |

Filters: *Company*, *Customer*, *Sales Order*, *Item* and *Unpaid Only*. *Unpaid Only* is on by default and hides paid orders.

The report only has rows if ERPNext created a **Stock Reservation Entry**. If `allow_reservation` is off, such a reservation only exists after payment or delivery release. With *Unpaid Only* the report is then usually empty; without the filter it still shows these reservations.

The standard report **Reserved Stock** has a creation time, but no age in days, no stock quantity and no filter for unpaid advance payment orders.
