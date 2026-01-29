# Classic Link Component

**High-level abstraction layer for Classic Accounting integration**

The Classic Link component provides a clean, developer-friendly API for working with Classic Accounting (2022+). It abstracts the complexity of GL entries, tax calculations, document numbering, and database operations behind simple service methods.

## Why Classic Link?

Classic Accounting has many nuances and complex requirements:
- GL entries must balance to 0.00
- Document numbers must be unique and sequential
- Tax applicability has intricate rules
- Inventory items require 3 GL entries, while non-inventory items need 1
- ID generation follows Hibernate TABLE strategy
- Transaction management must be atomic

**Classic Link handles all of this automatically**, so developers can focus on business logic instead of accounting rules.

## Quick Start

### Creating an Invoice

```python
from librepy.classic_link.services.invoice_service import InvoiceService
from decimal import Decimal
from datetime import date

result = InvoiceService.create_sales_invoice(
    customer_id=123,
    line_items=[
        {
            'item_id': 456,
            'qty': Decimal('2.0'),
            'price': Decimal('50.00'),
            'description': 'Blue Widget'
        }
    ],
    tax_item_ids=[10, 11],
    invoice_date=date.today()
)

if result.success:
    print(f"Invoice {result.doc_number} created: ${result.invoice_total}")
else:
    print(f"Error: {result.error}")
```

That's it! The service handles:
- ✅ Validation
- ✅ Document numbering
- ✅ GL entries (balanced to 0.00)
- ✅ Tax calculations
- ✅ Tax applicability
- ✅ Transaction management
- ✅ Error handling

### Querying Data

```python
from librepy.classic_link.daos.dao_factory import DAOFactory

# Initialize DAO factory (reuse across operations)
dao_factory = DAOFactory(logger)

# Get customer details
customer = dao_factory.customer().get_by_id(123)
print(f"Customer: {customer.get('orgname')}")

# Search for items
items = dao_factory.item().search_items("Widget")
for item in items:
    print(f"{item.get('item_name')} - ${item.get('price')}")
```

## Architecture

Classic Link follows a **Service + Helper + DAO** pattern:

```
Services (High-level)
    ↓ uses
Helpers (Reusable logic)
    ↓ uses
DAOs (Data access)
    ↓ uses
Models (Database tables)
```

### Services
High-level APIs for complete workflows (e.g., create invoice, process payment).
- Located in: `services/`
- Example: `InvoiceService.create_sales_invoice()`
- Returns: Result objects with success/error info

### Helpers
Reusable components for specific complex tasks (e.g., GL generation, tax calculation).
- Located in: `helpers/`
- Examples: `GLEntryGenerator`, `DocumentNumberManager`, `ValidationHelper`
- Stateless with static methods

### DAOs (Data Access Objects)
Database operations using proven BaseDAO pattern with automatic connection management.
- Located in: `daos/`
- Examples: `CustomerDAO`, `ItemDAO`, `TaxDAO`
- Instance-based with proper connection handling
- Extends BaseDAO for consistent CRUD operations
- Accessed via `DAOFactory` for centralized instantiation

### Models
Peewee ORM models for Classic Accounting database tables.
- Located in: `models/`
- Example: `AcctTrans`, `AcctEntry`, `ItmItems`, `Org`

## Directory Structure

```
classic_link/
├── README.md                    # This file
├── QUICK_REFERENCE.md          # Quick reference guide
├── models/
│   ├── base_model.py           # Base model for all CA tables
│   └── ca_model.py             # All CA database models
├── daos/
│   ├── dao_factory.py          # Centralized DAO instantiation
│   ├── customer_dao.py         # Customer data access
│   ├── item_dao.py             # Item/product data access
│   ├── tax_dao.py              # Tax data access
│   ├── gl_account_dao.py       # GL account data access
│   ├── transaction_dao.py      # Transaction data access
│   ├── transaction_type_dao.py # Transaction type data access
│   └── reference_data_dao.py   # Terms, price levels, etc.
├── helpers/
│   ├── validation.py           # Data validation
│   ├── id_generator.py         # ID generation (Hibernate TABLE)
│   ├── document_number_manager.py  # Document numbering
│   ├── gl_entry_generator.py   # GL entry generation
│   └── tax_entry_generator.py  # Tax applicability
├── services/
│   ├── result_types.py         # Result data structures
│   ├── invoice_service.py      # Invoice operations
│   └── README.md               # Service documentation
├── examples/
│   ├── create_invoice_example.py
│   └── dao_examples.py
└── ui/
    ├── item_selector_dialog.py
    └── item_entry_dialog.py
```

## Key Features

### 1. Automatic GL Entry Generation

```python
# GL entries are generated automatically and guaranteed to balance to 0.00
result = InvoiceService.create_sales_invoice(...)

# Behind the scenes:
# - AR account: +$100.00 (debit)
# - Sales GL: -$92.59 (credit)
# - Tax GL: -$7.41 (credit)
# - Plus inventory GL entries if applicable
# Total: $0.00 ✓
```

### 2. Smart Tax Calculations

```python
# Taxes are calculated based on:
# - Selected tax items
# - Item-tax links (item_tax_link table)
# - Customer tax exemptions (org_item_link table)

result = InvoiceService.create_sales_invoice(
    customer_id=123,
    line_items=[...],
    tax_item_ids=[10, 11]  # State and local taxes
)

# Tax applicability is determined automatically
```

### 3. Document Numbering

```python
# Document numbers are generated automatically from acct_trans_type.lastsequence
# No need to worry about sequence management or duplicates

result = InvoiceService.create_sales_invoice(...)
print(result.doc_number)  # "INV-00042"
```

### 4. Validation

```python
# Input data is validated before any database operations
# - Customer exists and is active
# - Items exist and are active
# - Quantities and prices are valid
# - Tax items are valid

result = InvoiceService.create_sales_invoice(
    customer_id=999999,  # Invalid
    line_items=[...]
)

if not result.success:
    print(result.error)  # "Customer 999999 not found"
```

### 5. Transaction Management

```python
# All database operations are wrapped in atomic transactions
# Automatic rollback on any error

with database.atomic():  # Handled automatically by services
    # Create header
    # Insert line items
    # Generate GL entries
    # Update sequences
    # If ANY step fails, ALL changes are rolled back
```

### 6. DAO Pattern with Automatic Connection Management

```python
from librepy.classic_link.daos.dao_factory import DAOFactory

# Initialize factory once (per service/component)
dao_factory = DAOFactory(logger)

# All DAO methods handle connections automatically
customer = dao_factory.customer().get_by_id(123)

# DAOs work within existing connection contexts
with database.connection_context():
    customer = dao_factory.customer().get_by_id(123)
    items = dao_factory.item().search_items("widget")

# Behind the scenes: BaseDAO._ensure_connection
# - Uses proven pattern from base_dao.py
# - Checks if connection is closed using getattr (SDBC compatible)
# - Opens connection_context() only when needed
# - Reuses existing connections for efficiency
# - No connection leaks
```

**Implementation:**
All DAOs extend `BaseDAO` which provides connection management:

```python
class CustomerDAO(BaseDAO):
    def __init__(self, logger):
        super().__init__(Org, logger)
    
    def get_by_id(self, org_id: int) -> Optional[Dict]:
        def _q():
            org = Org.get(Org.org_id == org_id)
            return self._to_dict(org)
        
        return self.safe_execute(f"get_by_id({org_id})", _q, default_return=None)
```

**Benefits:**
- ✅ Battle-tested BaseDAO pattern (proven across LibrePy projects)
- ✅ Automatic connection management
- ✅ SDBC database wrapper compatibility
- ✅ Consistent error handling via safe_execute
- ✅ No connection leaks
- ✅ Centralized via DAOFactory

## Usage Patterns

### Pattern 1: Use Services for Complete Workflows

**Good:** Use services when you want to create/update/delete records

```python
result = InvoiceService.create_sales_invoice(...)
```

**Why:** Services handle validation, transactions, GL generation, etc.

### Pattern 2: Use DAOs for Reading Data

**Good:** Use DAOs when you need to fetch data

```python
dao_factory = DAOFactory(logger)
customer = dao_factory.customer().get_by_id(123)
items = dao_factory.item().search_items("Widget")
```

**Why:** DAOs provide consistent data access with automatic connection management

### Pattern 3: Use Helpers for Reusable Logic

**Good:** Use helpers when you need specific calculations

```python
gl_entries = GLEntryGenerator.generate_for_invoice(...)
is_valid = ValidationHelper.validate_invoice_data(...)
```

**Why:** Helpers are reusable and testable

### Pattern 4: Don't Use Models Directly for Business Logic

**Avoid:** Don't create records directly with models in business code

```python
# Bad - bypasses validation, GL generation, etc.
AcctTrans.create(transtypecode='INVOICE', ...)
```

**Instead:** Use services which handle everything correctly

```python
# Good - uses service which handles all requirements
InvoiceService.create_sales_invoice(...)
```

## Classic Accounting Version Support

Classic Link supports **Classic Accounting 2022 and later**.

- ✅ ID Generation: Hibernate TABLE strategy (newer version)
- ✅ Document Numbering: `acct_trans_type.lastsequence`
- ✅ Tax Handling: New tax tables (`acct_trans_tax_regions`, `acct_entry_applic_taxes`)
- ❌ Older versions: Not supported

## Error Handling

All services return result objects with success/error information:

```python
result = InvoiceService.create_sales_invoice(...)

if result.success:
    # Success path
    transid = result.transid
    doc_number = result.doc_number
    total = result.invoice_total
    
    # Check for warnings
    for warning in result.warnings:
        logger.warning(warning)
else:
    # Error path
    logger.error(result.error)
```

## Examples

See the `examples/` directory for complete working examples:

- **create_invoice_example.py**: Creating invoices with various options
- **dao_examples.py**: Querying Classic Accounting data using DAOs

## Documentation

Each subdirectory has its own README:

- **services/README.md**: Service usage and API reference
- **daos/**: See docstrings in each DAO file and DAOFactory
- **helpers/**: See docstrings in each helper file
- **QUICK_REFERENCE.md**: Quick reference for common operations

## Development Guidelines

### Adding New Features

1. **New service method**: Add to appropriate service class in `services/`
2. **New DAO method**: Add to appropriate DAO class in `daos/`
3. **New DAO class**: Extend `BaseDAO` and add to `DAOFactory`
4. **New helper**: Create new file in `helpers/` with static methods
5. **New model**: Add to `models/ca_model.py`

### Code Style

- Use type hints for all parameters and return values
- Write comprehensive docstrings (Google style)
- Keep methods focused and single-purpose
- Use static methods for stateless operations
- Validate inputs early

### Testing

- Test services with real database (integration tests)
- Test helpers with mock data (unit tests)
- Test DAOs with real database (integration tests)
- Always test error paths
- DAOs inherit BaseDAO's connection management - no need to test that

## Migration from Old Code

If you have existing code using DAOs or direct model access:

### Before (Old Pattern)
```python
# Old: Manual GL calculation, validation, etc.
trans = PubAcctTrans.create(...)
for line in lines:
    PubAcctEntry.create(...)
# ... complex GL logic ...
# ... tax calculation ...
# ... document numbering ...
```

### After (Classic Link)
```python
# New: Service handles everything
result = InvoiceService.create_sales_invoice(
    customer_id=123,
    line_items=[...],
    tax_item_ids=[...]
)
```

**Benefits:**
- 90% less code
- Automatic validation
- Automatic GL generation
- Automatic tax calculation
- Better error handling
- Easier to test

## FAQ

**Q: Do I still need to understand GL entries?**  
A: Not for basic operations. Services handle GL generation automatically. However, understanding the concepts helps when debugging or adding advanced features.

**Q: Can I use Classic Link with older versions of Classic Accounting?**  
A: No, Classic Link only supports Classic Accounting 2022+. Older versions use different ID generation and tax handling.

**Q: What if I need custom GL logic?**  
A: You can use `GLEntryGenerator` directly and customize the entries before inserting. Or create a new helper for your specific use case.

**Q: Can I query data without using services?**  
A: Yes! DAOs are independent. Use `DAOFactory` to access them anytime you need to read data.

**Q: How do I handle transactions?**  
A: Services handle transactions automatically. If you're writing custom code, use `database.atomic()`.

**Q: Where are the unit tests?**  
A: Tests are coming soon in a separate PR. Current focus is on core functionality.

## Support

For questions or issues:
1. Check the examples in `examples/`
2. Read the service documentation in `services/README.md`
3. Check docstrings in the relevant module
4. Consult Classic Accounting Developer Guide (`ClassicAccountingDevGuide.md`)

## Future Enhancements

Planned features:
- Payment processing service
- Credit memo service
- Vendor bill service
- Customer service (create/update customers)
- Item service (create/update items)
- Batch operations
- Reporting helpers

