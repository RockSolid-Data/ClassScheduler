"""
DAO Factory for Classic Link.

Provides centralized access to all Classic Accounting DAO instances.
"""
from librepy.classic_link.daos.customer_dao import CustomerDAO


class DAOFactory:
    """Factory for creating and caching DAO instances."""
    
    def __init__(self, logger):
        """
        Initialize the DAO factory.
        
        Args:
            logger: Logger instance to pass to all DAOs
        """
        self.logger = logger
        self._customer_dao = None
        self._item_dao = None
        self._tax_dao = None
        self._gl_account_dao = None
        self._transaction_dao = None
        self._reference_data_dao = None
    
    def customer(self):
        """
        Get or create CustomerDAO instance.
        
        Returns:
            CustomerDAO: Singleton instance for customer operations
        """
        if self._customer_dao is None:
            self._customer_dao = CustomerDAO(self.logger)
        return self._customer_dao
    
    def item(self):
        """
        Get or create ItemDAO instance.
        
        Returns:
            ItemDAO: Singleton instance for item operations
        """
        if self._item_dao is None:
            # TODO: Import and instantiate ItemDAO when implemented
            raise NotImplementedError("ItemDAO not yet implemented")
        return self._item_dao
    
    def tax(self):
        """
        Get or create TaxDAO instance.
        
        Returns:
            TaxDAO: Singleton instance for tax operations
        """
        if self._tax_dao is None:
            # TODO: Import and instantiate TaxDAO when implemented
            raise NotImplementedError("TaxDAO not yet implemented")
        return self._tax_dao
    
    def gl_account(self):
        """
        Get or create GLAccountDAO instance.
        
        Returns:
            GLAccountDAO: Singleton instance for GL account operations
        """
        if self._gl_account_dao is None:
            # TODO: Import and instantiate GLAccountDAO when implemented
            raise NotImplementedError("GLAccountDAO not yet implemented")
        return self._gl_account_dao
    
    def transaction(self):
        """
        Get or create TransactionDAO instance.
        
        Returns:
            TransactionDAO: Singleton instance for transaction operations
        """
        if self._transaction_dao is None:
            # TODO: Import and instantiate TransactionDAO when implemented
            raise NotImplementedError("TransactionDAO not yet implemented")
        return self._transaction_dao
    
    def reference_data(self):
        """
        Get or create ReferenceDataDAO instance.
        
        Returns:
            ReferenceDataDAO: Singleton instance for reference data operations
        """
        if self._reference_data_dao is None:
            # TODO: Import and instantiate ReferenceDataDAO when implemented
            raise NotImplementedError("ReferenceDataDAO not yet implemented")
        return self._reference_data_dao
