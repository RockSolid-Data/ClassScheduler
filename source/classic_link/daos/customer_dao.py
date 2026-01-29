"""
Customer DAO for Classic Accounting.

Provides data access methods for customers, their preferences, addresses, and tax configuration.
Consolidates functionality from customer_dao, customer_preferences_dao, and customer_tax_item_dao.
"""
from librepy.app.data.base_dao import BaseDAO
from librepy.classic_link.models.ca_model import (
    Org, OrgAddress, OrgItemLink, ItmItems, ItmPriceLevels,
    AcctTerms, AcctViaMethod, AcctSalesRep
)
from librepy.peewee.peewee import fn


class CustomerDAO(BaseDAO):
    """Data access methods for Classic Accounting customers."""
    
    def __init__(self, logger):
        super().__init__(Org, logger)
    
    def search_customers(
        self,
        term="",
        limit=200,
        include_inactive=False
    ):
        """
        Search for customers with optional filtering.
        
        Args:
            term: Search term (searches name, phone, email)
            limit: Maximum results to return
            include_inactive: If True, include inactive customers
            
        Returns:
            List of customer dicts with keys: org_id, display_name, company_name,
            bill_address, phone, active
        """
        def _q():
            term_clean = term.strip()
            params = []
            
            sql = """
                SELECT 
                    org.org_id,
                    CASE 
                        WHEN COALESCE(org.orgname, '') || COALESCE(org.org_name_extension, '') != '' 
                        THEN COALESCE(org.orgname, '') || COALESCE(org.org_name_extension, '')
                        ELSE 'customer - ' || CAST(org.org_id AS TEXT)
                    END AS display_name,
                    org.orgname AS company_name,
                    org.phone1 AS phone,
                    org.active,
                    COALESCE(
                        CONCAT_WS(', ',
                            NULLIF(org_address.streetone, ''),
                            NULLIF(org_address.txtcity, ''),
                            NULLIF(org_address.txtstate, ''),
                            NULLIF(org_address.txtzip, '')
                        ),
                        ''
                    ) AS bill_address
                FROM public.org
                LEFT OUTER JOIN public.org_address 
                    ON org_address.orgid = org.org_id 
                    AND org_address.addresstype = 'BILLTO'
                WHERE org.orgdiscriminator = 'CUST'
            """
            
            if not include_inactive:
                sql += " AND org.active = true"
            
            if term_clean:
                term_lower = term_clean.lower()
                sql += """
                    AND (
                        LOWER(org.orgname) LIKE ?
                        OR LOWER(org.firstname) LIKE ?
                        OR LOWER(org.lastname) LIKE ?
                        OR LOWER(org.phone1) LIKE ?
                        OR LOWER(org.email) LIKE ?
                    )
                """
                search_pattern = f'%{term_lower}%'
                params.extend([search_pattern] * 5)
            
            sql += " ORDER BY org.orgname LIMIT ?"
            params.append(limit)
            
            cursor = self.database.execute_sql(sql, params)
            results = cursor.fetchall()
            
            return [{
                'org_id': row[0],
                'display_name': row[1],
                'company_name': row[2] or '',
                'bill_address': row[5],
                'phone': row[3] or '',
                'active': row[4]
            } for row in results]
        
        return self.execute_query(_q)
    
    def get_by_id(self, org_id):
        """
        Get customer by org_id.
        
        Args:
            org_id: Organization ID
            
        Returns:
            Customer dict or None if not found
        """
        def _q():
            org = Org.get(
                (Org.org_id == org_id) &
                (Org.orgdiscriminator == 'CUST')
            )
            return self._to_dict(org)
        
        return self.safe_execute(f"get_by_id({org_id})", _q, default_return=None)
    
    def get_by_account_number(self, account_number):
        """
        Get customer by account number.
        
        Args:
            account_number: Customer account number
            
        Returns:
            Customer dict or None if not found
        """
        def _q():
            org = Org.get(
                (Org.acctnumber == account_number) &
                (Org.orgdiscriminator == 'CUST')
            )
            return self._to_dict(org)
        
        return self.safe_execute(f"get_by_account_number({account_number})", _q, default_return=None)
    
    def get_active_count(self):
        """
        Count active customers.
        
        Returns:
            Number of active customers
        """
        def _q():
            return (Org
                .select()
                .where(
                    (Org.orgdiscriminator == 'CUST') &
                    (Org.active == True)
                )
                .count())
        
        return self.safe_execute("get_active_count", _q, default_return=0)
    
    def is_active(self, org_id):
        """
        Check if customer is active.
        
        Args:
            org_id: Organization ID
            
        Returns:
            True if customer exists and is active
        """
        def _q():
            org = Org.get(
                (Org.org_id == org_id) &
                (Org.orgdiscriminator == 'CUST')
            )
            return org.active
        
        return bool(self.safe_execute(f"is_active({org_id})", _q, default_return=False))
    
    def get_preference_ids(self, customer_id):
        """
        Get customer's default preference foreign key IDs.
        
        Returns nullable IDs for: price_level, terms, ship_method, sales_rep.
        Validates that referenced records are active.
        
        Args:
            customer_id: Customer org_id
            
        Returns:
            Dict with keys: price_level_id, terms_id, ship_method_id, sales_rep_id
            Values are IDs or None
        """
        def _q():
            org = Org.get(Org.org_id == customer_id)
            
            # Get raw FK IDs
            pl_id = getattr(org, 'pricelevelid_id', None)
            tm_id = getattr(org, 'termsid_id', None)
            via_id = getattr(org, 'default_ship_via_org_id', None)
            rep_id = getattr(org, 'def_sales_rep_id', None)
            
            self.logger.info(f"get_preference_ids({customer_id}): Raw FK values - pl_id={pl_id}, tm_id={tm_id}, via_id={via_id}, rep_id={rep_id}")
            
            pl_active = self._is_active(ItmPriceLevels, pl_id)
            tm_active = self._is_active(AcctTerms, tm_id)
            via_active = self._is_active(AcctViaMethod, via_id)
            rep_active = self._is_active(AcctSalesRep, rep_id)
            
            self.logger.info(f"get_preference_ids({customer_id}): Active checks - pl_active={pl_active}, tm_active={tm_active}, via_active={via_active}, rep_active={rep_active}")
            
            result = {
                "price_level_id": pl_id if pl_active else None,
                "terms_id": tm_id if tm_active else None,
                "ship_method_id": via_id if via_active else None,
                "sales_rep_id": rep_id if rep_active else None,
            }
            
            self.logger.info(f"get_preference_ids({customer_id}): Final result - {result}")
            
            return result
        
        default_prefs = {
            "price_level_id": None,
            "terms_id": None,
            "ship_method_id": None,
            "sales_rep_id": None,
        }
        return self.safe_execute(f"get_preference_ids({customer_id})", _q, default_return=default_prefs)
    
    def get_tax_item_ids(self, org_id, linktype=None):
        """
        Get SALESTAX item IDs linked to customer via org_item_link.
        
        Args:
            org_id: Customer org_id
            linktype: Optional filter for link type
            
        Returns:
            List of tax item IDs
        """
        def _q():
            query = (OrgItemLink
                .select(ItmItems.itemid)
                .join(ItmItems, on=(OrgItemLink.itemid == ItmItems.itemid))
                .where(
                    (ItmItems.itemtypecode == 'SALESTAX') &
                    (OrgItemLink.orgid == org_id)
                ))
            
            if linktype is not None:
                query = query.where(OrgItemLink.linktype == linktype)
            
            return [row.itemid for row in query]
        
        return self.execute_query(_q)
    
    def is_tax_exempt(self, org_id, tax_item_id):
        """
        Check if customer is exempt from a specific tax.
        
        Args:
            org_id: Customer org_id
            tax_item_id: Tax item ID
            
        Returns:
            True if customer is exempt from this tax
        """
        def _q():
            link = OrgItemLink.get(
                (OrgItemLink.orgid == org_id) &
                (OrgItemLink.itemid == tax_item_id)
            )
            return link.exempt
        
        return bool(self.safe_execute(f"is_tax_exempt({org_id}, {tax_item_id})", _q, default_return=False))
    
    def get_bill_address(self, org_id):
        """
        Get customer's billing address.
        
        Args:
            org_id: Customer org_id
            
        Returns:
            Address dict or None if not found
        """
        def _q():
            addr = (OrgAddress
                .select()
                .where(
                    (OrgAddress.orgid == org_id) &
                    (OrgAddress.addresstype == 'BILLTO')
                )
                .first())
            
            if addr:
                return {
                    'gen_addr_id': addr.gen_addr_id,
                    'street_one': addr.streetone,
                    'street_two': addr.streettwo,
                    'city': addr.txtcity,
                    'state': addr.txtstate,
                    'zip': addr.txtzip,
                    'country': addr.txtcountry,
                }
            return None
        
        return self.safe_execute(f"get_bill_address({org_id})", _q, default_return=None)
    
    def get_ship_addresses(self, org_id):
        """
        Get customer's shipping addresses.
        
        Args:
            org_id: Customer org_id
            
        Returns:
            List of address dicts
        """
        def _q():
            query = (OrgAddress
                .select()
                .where(
                    (OrgAddress.orgid == org_id) &
                    (OrgAddress.addresstype == 'SHIPTO') &
                    (OrgAddress.active == True)
                ))
            
            addresses = []
            for addr in query:
                addresses.append({
                    'gen_addr_id': addr.gen_addr_id,
                    'addr_name': addr.addrname,
                    'street_one': addr.streetone,
                    'street_two': addr.streettwo,
                    'city': addr.txtcity,
                    'state': addr.txtstate,
                    'zip': addr.txtzip,
                    'is_default': addr.is_default,
                })
            
            return addresses
        
        return self.execute_query(_q)
    
    # Helper methods
    
    @staticmethod
    def _build_display_name(org):
        """Build display name from organization record."""
        display_name = (org.orgname or '') + (org.org_name_extension or '')
        if not display_name:
            display_name = f"customer - {org.org_id}"
        return display_name
    
    def _get_bill_address_string(self, org_id):
        """Get billing address as formatted string."""
        def _q():
            addr = (OrgAddress
                .select()
                .where(
                    (OrgAddress.orgid == org_id) &
                    (OrgAddress.addresstype == 'BILLTO')
                )
                .first())
            
            if addr:
                parts = []
                if addr.streetone:
                    parts.append(addr.streetone)
                if addr.txtcity:
                    parts.append(addr.txtcity)
                if addr.txtstate:
                    parts.append(addr.txtstate)
                if addr.txtzip:
                    parts.append(addr.txtzip)
                return ', '.join(parts)
            return ''
        
        return self.safe_execute(f"get_bill_address_string({org_id})", _q, default_return='')
    
    def _is_active(self, model, pk):
        """Check if a record exists and is active."""
        if pk is None:
            return False
        try:
            row = model.get_or_none(model._meta.primary_key == pk)
            is_active = bool(getattr(row, 'active', True)) if row is not None else False
            self.logger.debug(f"_is_active({model.__name__}, {pk}): row_found={row is not None}, is_active={is_active}")
            return is_active
        except Exception as e:
            self.logger.error(f"_is_active({model.__name__}, {pk}) failed with error: {e}")
            return False
    
    @staticmethod
    def _to_dict(org):
        """Convert Org model to dict."""
        return {
            'org_id': org.org_id,
            'orgname': org.orgname,
            'org_name_extension': org.org_name_extension,
            'acctnumber': org.acctnumber,
            'active': org.active,
            'balance': org.balance,
            'email': org.email,
            'phone1': org.phone1,
            'phone2': org.phone2,
            'fax1': org.fax1,
            'firstname': org.firstname,
            'lastname': org.lastname,
            'creditlimit': org.creditlimit,
            'taxable': org.taxable,
            'notes': org.notes,
        }

