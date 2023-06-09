from random import randint
from typing import ClassVar

MIN_ID, MAX_ID = 10000, 999999999


class CompanyUniqueIds:
    """
    A class to manage unique identifiers for companies.

    This class provides methods to generate and manage unique identifiers for
    companies. It keeps track of the generated identifiers in a set to
    ensure uniqueness.

    Class Methods:
        get_initial_ids(): Initialize the set of company IDs by reading
        from a file.
        generate(): Generate a new unique company ID.
        remove(_id): Remove a company ID from the set of unique IDs.
        populate_ids_cache_map(key, value): Populate the IDs cache map with the
        given key-value pair.
        get_ids_cache_map(): Get the IDs cache map.


    Class Attributes:
        ids (set): A set containing the unique company IDs.
    """
    _company_id_to_elasticsearch_id_cache: \
        ClassVar[dict[str | int, str | int]] = dict()

    @classmethod
    def get_initial_ids(cls) -> None:
        """
        Get the initial set of unique company IDs from a file and set it to
        the class variable `ids`.
        """
        cls.ids = set(int(line.rstrip()) for line in open('/tmp/companies.txt'))

    @classmethod
    def generate(cls) -> int:
        """
        Generate a new unique company ID.

        Returns:
            int: The generated company ID.
        """
        id_: int = randint(MIN_ID, MAX_ID)
        if id_ in cls.ids:
            while id_ in cls.ids:
                id_: int = randint(MIN_ID, MAX_ID)
        cls.ids.add(id_)
        return id_

    @classmethod
    def remove(cls, id_: int) -> None:
        """
        Remove a company ID from the set of unique IDs.

        Args:
            id_ (int): The company ID to remove.
        """
        cls.ids.discard(id_)

    @classmethod
    def populate_ids_cache_map(cls, key: str | int, value: str | int) -> None:
        """Populate the IDs cache map with the given key-value pair."""
        cls._company_id_to_elasticsearch_id_cache[key] = value
        cls._company_id_to_elasticsearch_id_cache[value] = key

    @classmethod
    def get_ids_cache_map(cls) -> dict[str | int, str | int]:
        """Get the IDs cache map."""
        return cls._company_id_to_elasticsearch_id_cache


CompanyUniqueIds.get_initial_ids()
