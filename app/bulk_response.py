from dataclasses import dataclass
from typing import Any, Mapping, Iterable

from company import Company


@dataclass
class BulkResponse:
    """A class representing the response from a bulk operation.

    Attributes:
        raw_response (tuple[int, list[Mapping[str, Any]]]): The raw response from
        the bulk operation.
        operation_type (str): The type of operation performed
        (one of: 'index', 'update', 'delete').
        internal_errors (Iterable[tuple[int, str]]): Internal errors occurred
        during the operation.

    Properties:
        num_of_successful_operations (int): The number of successful operations.
        errors (Mapping[int, str]): Mapping of company IDs to error messages.
    """
    raw_response: tuple[int, list[Mapping[str, Any]]]
    operation_type: str
    internal_errors: Iterable[tuple[int, str]]

    @property
    def num_of_successful_operations(self) -> int:
        """Get the number of successful operations."""
        return self.raw_response[0]

    @property
    def errors(self) -> Mapping[int, str]:
        """Get a mapping of company IDs to error messages."""
        error = dict()
        for message in self.raw_response[1]:
            error_msg: str = message[self.operation_type]['error']['caused_by']['reason']
            es_id: int = message[self.operation_type]['_id']
            company_id = Company.get_ids_cache_map()[es_id]
            error[company_id] = error_msg

        for message in self.internal_errors:
            error[message[0]] = message[1]
        return error
