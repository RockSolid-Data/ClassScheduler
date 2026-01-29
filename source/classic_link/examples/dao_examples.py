"""
Example: Using Classic Link DAO Classes

This example demonstrates how to query Classic Accounting data using
the DAO (Data Access Object) classes via DAOFactory.
"""
import logging
from librepy.classic_link.daos.dao_factory import DAOFactory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize DAO factory once
dao_factory = DAOFactory(logger)


def query_customer_data():
    """Query customer information."""
    logger.info("\n--- Customer Queries ---\n")
    
    customer_id = 123
    
    # Get customer by ID
    customer = dao_factory.customer().get_by_id(customer_id)
    if customer:
        logger.info(f"Customer: {customer.get('orgname')}")
        logger.info(f"  Type: {customer.get('org_type_code')}")
        logger.info(f"  Active: {customer.get('active')}")
    
    # Get customer preferences
    prefs = dao_factory.customer().get_preference_ids(customer_id)
    if prefs:
        logger.info(f"  Terms ID: {prefs.get('terms_id')}")
        logger.info(f"  Price Level ID: {prefs.get('price_level_id')}")
    
    # Get billing address
    bill_address = dao_factory.customer().get_bill_address(customer_id)
    logger.info(f"  Bill Address: {bill_address}")
    
    # Search customers by name
    customers = dao_factory.customer().search_customers("ABC")
    logger.info(f"\nFound {len(customers)} customers matching 'ABC'")
    for c in customers[:5]:
        logger.info(f"  • {c.get('orgname')} (ID: {c.get('org_id')})")
    
    # Get all active customers
    active_customers = dao_factory.customer().search_customers("", include_inactive=False)
    logger.info(f"\nTotal active customers: {len(active_customers)}")


def query_item_data():
    """Query item/product information."""
    logger.info("\n--- Item Queries ---\n")
    
    item_id = 456
    
    # Get item by ID
    item = dao_factory.item().get_by_id(item_id)
    if item:
        logger.info(f"Item: {item.get('item_name')}")
        logger.info(f"  Number: {item.get('item_number')}")
        logger.info(f"  Type: {item.get('item_type_code')}")
        logger.info(f"  Price: ${item.get('price')}")
        logger.info(f"  Active: {item.get('active')}")
    
    # Get item metadata (for GL calculations)
    metadata = dao_factory.item().get_metadata([item_id])
    if item_id in metadata:
        meta = metadata[item_id]
        logger.info(f"  Sales GL Account: {meta.get('sales_account_id')}")
        logger.info(f"  Asset GL Account: {meta.get('asset_account_id')}")
    
    # Search items by name
    items = dao_factory.item().search_items("Widget")
    logger.info(f"\nFound {len(items)} items matching 'Widget'")
    for i in items[:5]:
        logger.info(f"  • {i.get('item_name')} - ${i.get('price')}")
    
    # Get all tax item IDs
    tax_item_ids = dao_factory.item().get_all_tax_item_ids()
    logger.info(f"\nTotal tax items: {len(tax_item_ids)}")


def query_tax_data():
    """Query tax information."""
    logger.info("\n--- Tax Queries ---\n")
    
    # Get all active tax items
    taxes = dao_factory.tax().get_all_active_tax_items()
    logger.info(f"Active tax items: {len(taxes)}")
    for tax in taxes:
        logger.info(f"  • {tax['tax_item_name']} - {tax['rate']}%")
    
    # Get tax rates for specific taxes
    tax_ids = [10, 11]
    if tax_ids:
        rates = dao_factory.tax().get_tax_rates(tax_ids)
        logger.info(f"\nTax rates for IDs {tax_ids}:")
        for tax_id, rate in rates.items():
            logger.info(f"  Tax {tax_id}: {rate}%")
    
    # Check customer exemption
    customer_id = 123
    tax_id = 10
    is_exempt = dao_factory.tax().is_customer_exempt(customer_id, tax_id)
    logger.info(f"\nCustomer {customer_id} exempt from tax {tax_id}: {is_exempt}")
    
    # Get applicable taxes for customer
    applicable_taxes = dao_factory.tax().get_applicable_taxes_for_customer(customer_id)
    logger.info(f"Applicable taxes for customer {customer_id}: {applicable_taxes}")


def query_gl_accounts():
    """Query GL account information."""
    logger.info("\n--- GL Account Queries ---\n")
    
    # Get AR account
    ar_account_id = dao_factory.gl_account().get_ar_account()
    logger.info(f"AR Account ID: {ar_account_id}")
    
    # Get AP account
    ap_account_id = dao_factory.gl_account().get_ap_account()
    logger.info(f"AP Account ID: {ap_account_id}")
    
    # Get account by number
    if ar_account_id:
        account = dao_factory.gl_account().get_by_number(ar_account_id)
        if account:
            logger.info(f"  Account: {account.get('accountname')}")
    
    # Search accounts
    accounts = dao_factory.gl_account().search_accounts("Sales")
    logger.info(f"\nFound {len(accounts)} accounts matching 'Sales'")
    for acc in accounts[:5]:
        logger.info(f"  • {acc.get('accountname')} ({acc.get('accountnumber')})")


def query_transactions():
    """Query transaction information."""
    logger.info("\n--- Transaction Queries ---\n")
    
    trans_id = 1000
    
    # Get transaction by ID
    trans = dao_factory.transaction().get_by_id(trans_id)
    if trans:
        logger.info(f"Transaction: {trans.get('reference_number')}")
        logger.info(f"  Type: {trans.get('trans_type_code')}")
        logger.info(f"  Amount: ${trans.get('amount')}")
    
    # Check if document number exists
    doc_number = "INV-00001"
    exists = dao_factory.transaction().exists_by_reference_number(doc_number)
    logger.info(f"\nDocument '{doc_number}' exists: {exists}")
    
    # Search invoices for customer
    customer_id = 123
    invoices = dao_factory.transaction().search_invoices(customer_id=customer_id, limit=10)
    logger.info(f"\nFound {len(invoices)} invoices for customer {customer_id}")


def query_reference_data():
    """Query reference data (terms, price levels, etc.)."""
    logger.info("\n--- Reference Data Queries ---\n")
    
    # Payment terms
    all_terms = dao_factory.reference_data().get_all_terms()
    logger.info(f"Payment terms: {len(all_terms)}")
    for term in all_terms[:5]:
        logger.info(f"  • {term.get('termname')}")
    
    # Price levels
    price_levels = dao_factory.reference_data().get_all_price_levels()
    logger.info(f"\nPrice levels: {len(price_levels)}")
    for level in price_levels[:5]:
        logger.info(f"  • {level.get('pricelevelname')}")
    
    # Sales reps
    sales_reps = dao_factory.reference_data().get_all_sales_reps()
    logger.info(f"\nSales reps: {len(sales_reps)}")
    for rep in sales_reps[:5]:
        logger.info(f"  • {rep.get('initial')}")
    
    # Ship methods
    ship_methods = dao_factory.reference_data().get_all_ship_methods()
    logger.info(f"\nShip methods: {len(ship_methods)}")
    for method in ship_methods[:5]:
        logger.info(f"  • {method.get('shipvia')}")


def demonstrate_batch_queries():
    """Demonstrate efficient batch querying."""
    logger.info("\n--- Batch Query Examples ---\n")
    
    # Batch item metadata
    item_ids = [456, 457, 458]
    metadata = dao_factory.item().get_metadata(item_ids)
    logger.info(f"Fetched metadata for {len(item_ids)} items in one query")
    for item_id, meta in metadata.items():
        logger.info(f"  Item {item_id}: Sales GL {meta.get('sales_account_id')}")
    
    # Batch tax rates
    tax_ids = [10, 11, 12]
    rates = dao_factory.tax().get_tax_rates(tax_ids)
    logger.info(f"\nFetched rates for {len(tax_ids)} taxes in one query")
    for tax_id, rate in rates.items():
        logger.info(f"  Tax {tax_id}: {rate}%")
    
    # Batch tax links
    product_ids = [456, 457]
    tax_links = dao_factory.tax().get_item_tax_links_batch(product_ids, tax_ids)
    logger.info(f"\nFetched tax links for {len(product_ids)} products in one query")
    logger.info(f"Total links: {len(tax_links)}")


def main():
    """Run all query examples."""
    logger.info("=" * 60)
    logger.info("CLASSIC LINK - DAO QUERY EXAMPLES")
    logger.info("=" * 60)
    
    try:
        query_customer_data()
        query_item_data()
        query_tax_data()
        query_gl_accounts()
        query_transactions()
        query_reference_data()
        demonstrate_batch_queries()
        
        logger.info("\n" + "=" * 60)
        logger.info("EXAMPLES COMPLETE")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"Error running examples: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    main()

