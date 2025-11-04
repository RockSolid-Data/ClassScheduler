from librepy.app.data.base_dao import BaseDAO
from librepy.app.data.model import EmployeeContract, Employee


class EmployeeContractDAO(BaseDAO):

    def __init__(self, logger):
        super().__init__(EmployeeContract, logger)


    def create(self, employee, start_date, end_date, time_in=None, time_out=None):
        """Create a new EmployeeContract and return the model instance."""
        def _q():
            return EmployeeContract.create(
                employee=employee,
                start_date=start_date,
                end_date=end_date,
                time_in=time_in,
                time_out=time_out,
            )
        return self.safe_execute('create EmployeeContract', _q, default_return=None)

    def update(self, contract_id, employee=None, start_date=None, end_date=None, time_in=None, time_out=None):
        """Update provided fields on EmployeeContract and return the refreshed instance."""
        updates = {}
        if employee is not None:
            updates['employee'] = employee
        if start_date is not None:
            updates['start_date'] = start_date
        if end_date is not None:
            updates['end_date'] = end_date
        if time_in is not None:
            updates['time_in'] = time_in
        if time_out is not None:
            updates['time_out'] = time_out
        if updates:
            self.update_fields(EmployeeContract.contract_id == contract_id, updates, operation_name='update EmployeeContract')
        def _fetch():
            return EmployeeContract.get(EmployeeContract.contract_id == contract_id)
        return self.safe_execute('get EmployeeContract after update', _fetch, default_return=None)

    def _row_to_dict(self, ec):
        """Map EmployeeContract row to calendar dict (assumes Employee is joined)."""
        emp = getattr(ec, 'employee', None)
        first = getattr(emp, 'first_name', None) if emp is not None else None
        last = getattr(emp, 'last_name', None) if emp is not None else None
        employee_name = None
        if first or last:
            employee_name = f"{(first or '').strip()} {(last or '').strip()}".strip()

        return {
            'id': getattr(ec, 'contract_id', None),
            'employee_id': getattr(emp, 'employee_id', None) if emp is not None else None,
            'employee_name': employee_name,
            'start_date': getattr(ec, 'start_date', None),
            'end_date': getattr(ec, 'end_date', None),
            'time_in': getattr(ec, 'time_in', None),
            'time_out': getattr(ec, 'time_out', None),
            'title': employee_name or f"Contract {getattr(ec, 'contract_id', '')}",
            'status': 'active',
        }

    def get_contracts_between(self, start_date, end_date):
        """Query EmployeeContract rows that overlap the [start_date, end_date] range.

        Overlap condition: end_date >= start_date AND start_date <= end_date
        Returns: List[dict]
        """
        def _query():
            # Join employee to get names (optional)
            query = (EmployeeContract
                     .select(EmployeeContract, Employee)
                     .join(Employee)
                     .where((EmployeeContract.end_date >= start_date) &
                            (EmployeeContract.start_date <= end_date))
                     .order_by(EmployeeContract.start_date))
            return [self._row_to_dict(row) for row in query]

        return self.safe_execute('get_contracts_between', _query, default_return=[])
