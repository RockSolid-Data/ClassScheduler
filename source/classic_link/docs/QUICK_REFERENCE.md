# Classic Link Quick Reference

Fast lookup for common operations with Classic Link.

## Import Statements

```python
# Services
from librepy.classic_link.services.invoice_service import InvoiceService

# DAOs (Data Access Objects)
from librepy.classic_link.daos.dao_factory import DAOFactory

# Helpers (if needed for custom logic)
from librepy.classic_link.helpers.gl_entry_generator import GLEntryGenerator
from librepy.classic_link.helpers.tax_entry_generator import TaxEntryGenerator
from librepy.classic_link.helpers.validation import ValidationHelper
from librepy.classic_link.helpers.document_number_manager import DocumentNumberManager

# Standard imports
from decimal import Decimal
from datetime import date
import logging
```

## Common Operations

### Create Invoice

```python
result = InvoiceService.create_sales_invoice(
    customer_id=123,
    line_items=[
        {'item_id': 456, 'qty': Decimal('2'), 'price': Decimal('50.00')}
    ],
    tax_item_ids=[10, 11],
    invoice_date=date.today(),
    memo='Invoice memo',
    customer_po='PO-12345'
)

if result.success:
    print(f"Invoice {result.doc_number} created: ${result.invoice_total}")
else:
    print(f"Error: {result.error}")
```

### Get Customer

```python
# Initialize DAO factory
dao_factory = DAOFactory(logger)

# By ID
customer = dao_factory.customer().get_by_id(123)

# Search by name
customers = dao_factory.customer().search_customers("ABC Corp")

# Get all active
customers = dao_factory.customer().search_customers("", include_inactive=False)

# Get customer preferences
prefs = dao_factory.customer().get_preference_ids(123)
terms_id = prefs.get('terms_id')

# Get billing address
address = dao_factory.customer().get_bill_address(123)
```

### Get Items

```python
dao_factory = DAOFactory(logger)

# By ID
item = dao_factory.item().get_by_id(456)

# Search by name
items = dao_factory.item().search_items("Widget")

# Get metadata for GL calculations
metadata = dao_factory.item().get_metadata([456, 457, 458])

# Get all tax item IDs
tax_item_ids = dao_factory.item().get_all_tax_item_ids()
```

### Get Taxes

```python
dao_factory = DAOFactory(logger)

# All active taxes
taxes = dao_factory.tax().get_all_active_tax_items()

# Tax rates (batch)
rates = dao_factory.tax().get_tax_rates([10, 11, 12])

# Check customer exemption
is_exempt = dao_factory.tax().is_customer_exempt(customer_id=123, tax_item_id=10)

# Get applicable taxes for customer
applicable = dao_factory.tax().get_applicable_taxes_for_customer(123)
```

### Get GL Accounts

```python
dao_factory = DAOFactory(logger)

# AR account
ar_account_id = dao_factory.gl_account().get_ar_account()

# AP account
ap_account_id = dao_factory.gl_account().get_ap_account()

# By number
account = dao_factory.gl_account().get_by_number(1000)

# Search
accounts = dao_factory.gl_account().search_accounts("Sales")
```

### Get Transactions

```python
dao_factory = DAOFactory(logger)

# By ID
trans = dao_factory.transaction().get_by_id(1000)

# Check if doc number exists
exists = dao_factory.transaction().exists_by_reference_number("INV-00001")

# Search invoices for customer
invoices = dao_factory.transaction().search_invoices(customer_id=123, limit=10)
```

### Reference Data

```python
dao_factory = DAOFactory(logger)

# Payment terms
terms = dao_factory.reference_data().get_all_terms()
term = dao_factory.reference_data().get_terms_by_id(1)

# Price levels
price_levels = dao_factory.reference_data().get_all_price_levels()

# Sales reps
reps = dao_factory.reference_data().get_all_sales_reps()

# Ship methods
methods = dao_factory.reference_data().get_all_ship_methods()
```

## Line Item Structure

```python
line_items = [
    {
        'item_id': 456,              # Required: product/service item ID
        'qty': Decimal('2.0'),       # Required: quantity
        'price': Decimal('50.00'),   # Required: unit price
        'description': 'Blue Widget', # Optional: line description
        'unit_id': 10,               # Optional: item unit ID
    },
    # ... more line items
]
```

## Result Object

```python
result = InvoiceService.create_sales_invoice(...)

# Check success
if result.success:
    transid = result.transid             # Transaction ID (int)
    doc_number = result.doc_number       # Document number (str)
    total = result.invoice_total         # Invoice total (Decimal)
    warnings = result.warnings           # List of warnings (List[str])
else:
    error = result.error                 # Error message (str)
```

## Error Handling Pattern

```python
try:
    result = InvoiceService.create_sales_invoice(...)
    
    if result.success:
        # Success path
        log.info(f"Invoice {result.doc_number} created")
        
        # Check warnings
        for warning in result.warnings:
            log.warning(f"Warning: {warning}")
            
        return result.transid
    else:
        # Validation error
        log.error(f"Validation failed: {result.error}")
        return None
        
except Exception as e:
    # Unexpected error
    log.error(f"Unexpected error: {e}")
    return None
```

## Common DAO Patterns

### Reuse DAOFactory

```python
# Good: Initialize once per service/component
class MyService:
    def __init__(self, logger):
        self.dao_factory = DAOFactory(logger)
    
    def do_work(self):
        customer = self.dao_factory.customer().get_by_id(123)
        items = self.dao_factory.item().search_items("Widget")

# Bad: Don't create new factory for every operation
def some_function():
    customer = DAOFactory(logger).customer().get_by_id(123)  # Wasteful
```

### Batch Fetch

```python
dao_factory = DAOFactory(logger)

# Good: One query for multiple items
item_ids = [456, 457, 458]
metadata = dao_factory.item().get_metadata(item_ids)

# Bad: Multiple queries
for item_id in item_ids:
    meta = dao_factory.item().get_by_id(item_id)  # Don't do this!
```

### Search with Filters

```python
dao_factory = DAOFactory(logger)

# Get active customers matching name
customers = dao_factory.customer().search_customers("ABC", include_inactive=False)

# Get items with specific tax treatment
items = dao_factory.item().search_items("Widget")
taxable = [i for i in items if not i.get('tax_exempt')]
```

## Validation Pattern

```python
# Validate before calling service
validation = ValidationHelper.validate_invoice_data(
    customer_id=123,
    line_items=[...],
    tax_item_ids=[10, 11]
)

if not validation.valid:
    print(f"Validation errors: {', '.join(validation.errors)}")
    return

# Proceed with invoice creation
result = InvoiceService.create_sales_invoice(...)
```

## Custom GL Entries (Advanced)

```python
# If you need custom GL logic, use the helper directly
from librepy.classic_link.helpers.gl_entry_generator import (
    GLEntryGenerator, LineItemData, TaxLineData
)

gl_entries = GLEntryGenerator.generate_for_invoice(
    invoice_total=Decimal('100.00'),
    line_items=[
        LineItemData(item_id=456, orderseq=0, entrytotal=Decimal('92.59'))
    ],
    tax_lines=[
        TaxLineData(item_id=10, orderseq=1, entrytotal=Decimal('7.41'))
    ]
)

# Validate balance
GLEntryGenerator.validate_balance(gl_entries)

# Now insert manually...
```

## Transaction Management

```python
# Services handle transactions automatically
result = InvoiceService.create_sales_invoice(...)

# For custom code, use database.atomic()
from librepy.database.connection.db_connection import get_database_connection

with get_database_connection().atomic():
    # All operations here are atomic
    # Automatic rollback on exception
    pass
```

## DAO Connection Management

```python
# DAOs automatically handle database connections
# No manual open/close needed

dao_factory = DAOFactory(logger)

# Works standalone (opens connection if needed)
customer = dao_factory.customer().get_by_id(123)

# Works within existing connection context (reuses connection)
from librepy.database.connection.db_connection import get_database_connection

with get_database_connection().connection_context():
    customer = dao_factory.customer().get_by_id(123)
    items = dao_factory.item().search_items("widget")
    taxes = dao_factory.tax().get_all_active_tax_items()

# Zero overhead when connection is already open
# Automatic cleanup via context manager
# No connection leaks
```

**How it works:**
All DAOs extend `BaseDAO` which provides `_ensure_connection`:

```python
from librepy.app.data.dao.base_dao import BaseDAO

class MyCustomDAO(BaseDAO):
    def __init__(self, logger):
        super().__init__(MyModel, logger)
    
    def my_custom_query(self):
        def _q():
            return list(MyModel.select())
        
        return self.safe_execute("my_custom_query", _q, default_return=[])
```

**When to use connection contexts:**
- **Standalone calls:** Just call the DAO - connection handled automatically
- **Multiple queries:** Wrap in `connection_context()` for efficiency
- **Services:** Already handled internally - don't nest contexts

```python
dao_factory = DAOFactory(logger)

# Good: Reuse connection for multiple queries
with database.connection_context():
    customers = dao_factory.customer().search_customers("ABC")
    for cust in customers:
        items = dao_factory.item().get_metadata([...])
        
# Also good: Standalone calls (convenience)
customer = dao_factory.customer().get_by_id(123)
```

## Type Conversions

```python
# Always use Decimal for money
from decimal import Decimal

# Good
qty = Decimal('2.0')
price = Decimal('50.00')

# Bad - floats have precision issues
qty = 2.0  # Don't do this
price = 50.00  # Don't do this

# Converting
from_float = Decimal(str(50.0))  # Convert via string
from_int = Decimal(50)           # Direct conversion OK for integers
```

## Common Mistakes

### ❌ Don't Do This

```python
# Don't create records directly
AcctTrans.create(transtypecode='INVOICE', ...)

# Don't fetch data in loops
dao_factory = DAOFactory(logger)
for item_id in [456, 457, 458]:
    item = dao_factory.item().get_by_id(item_id)  # Inefficient!

# Don't use floats for money
price = 50.0

# Don't ignore result.success
result = InvoiceService.create_sales_invoice(...)
transid = result.transid  # Could be None!

# Don't create DAOFactory repeatedly
for i in range(100):
    factory = DAOFactory(logger)  # Wasteful!
    customer = factory.customer().get_by_id(i)
```

### ✅ Do This Instead

```python
# Use services
result = InvoiceService.create_sales_invoice(...)

# Use batch queries
dao_factory = DAOFactory(logger)
metadata = dao_factory.item().get_metadata([456, 457, 458])

# Use Decimal for money
price = Decimal('50.00')

# Check result.success
result = InvoiceService.create_sales_invoice(...)
if result.success:
    transid = result.transid

# Reuse DAOFactory
dao_factory = DAOFactory(logger)
for i in range(100):
    customer = dao_factory.customer().get_by_id(i)
```

## Debugging Tips

### Enable SQL Logging

```python
import logging
peewee_logger = logging.getLogger('peewee')
peewee_logger.setLevel(logging.DEBUG)
```

### Enable Classic Link Logging

```python
import logging
classic_link_logger = logging.getLogger('classic_link')
classic_link_logger.setLevel(logging.DEBUG)
```

### Check GL Balance

```python
from librepy.classic_link.helpers.gl_entry_generator import GLEntryGenerator

# After generating entries
GLEntryGenerator.validate_balance(gl_entries)
# Raises RuntimeError if not balanced
```

### Validate Before Creating

```python
from librepy.classic_link.helpers.validation import ValidationHelper

validation = ValidationHelper.validate_invoice_data(...)
if not validation.valid:
    print("Errors:", validation.errors)
    print("Warnings:", validation.warnings)
```

## Performance Tips

1. **Use batch queries** when fetching multiple records
2. **Limit query results** with `.limit()` when possible
3. **Keep transactions short** - don't do long operations inside `atomic()`
4. **Cache reference data** (terms, price levels, etc.) if querying frequently
5. **Use `.select()` to limit fields** if you don't need all columns

## Further Reading

- **Main README:** `source/classic_link/README.md`
- **Services Guide:** `source/classic_link/services/README.md`
- **Examples:** `source/classic_link/examples/`
- **CA Dev Guide:** `ClassicAccountingDevGuide.md`

