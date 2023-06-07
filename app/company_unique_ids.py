from random import randint

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

    Class Attributes:
        ids (set): A set containing the unique company IDs.
    """

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
        _id: int = randint(MIN_ID, MAX_ID)
        if _id in cls.ids:
            print(_id in cls.ids)
            while _id in cls.ids:
                _id: int = randint(MIN_ID, MAX_ID)
        cls.ids.add(_id)
        return _id

    @classmethod
    def remove(cls, _id: int) -> None:
        """
        Remove a company ID from the set of unique IDs.

        Args:
            _id (int): The company ID to remove.
        """
        cls.ids.discard(_id)


CompanyUniqueIds.get_initial_ids()
