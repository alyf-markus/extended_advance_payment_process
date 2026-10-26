### Extended Advance Payment Process

**Deutsch:** Vorkasse: Lieferung und Beschaffung bleiben gesperrt, bis die Anzahlung da ist.

Beschlüsse und weiterer Ausbau: [docs/vorkasse.md](docs/vorkasse.md).

**English:** Advance payment: delivery and procurement stay blocked until the advance payment has been received.

Decisions and further development: [docs/advance_payment.md](docs/advance_payment.md).

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch version-16
bench install-app extended_advance_payment_process
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/extended_advance_payment_process
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

mit
