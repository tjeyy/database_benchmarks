import enum
import os
import re

"""
Optimization Support/Trigger:
  Postgres: - no dependent group-by reduction
            - no join to semi (not forceable)
            - no join to scan
            - does not rewrite subqueries to joins (nice)
  Umbra: - dependent-group by reduction (at least for primary keys, also Unique?)
         - probably no join to semi-join
         - no join to scan
  Orca: - dependent group-by reduction, distinct removal
        - rest s.t. test
"""


@enum.unique
class DependencyType(enum.Enum):
    Unique = enum.auto()
    Order = enum.auto()
    Inclusion = enum.auto()
    Functional = enum.auto()

    @classmethod
    def from_str(cls, string):
        if string == "UCC":
            return DependencyType.Unique
        if string == "OD":
            return DependencyType.Order
        if string == "IND":
            return DependencyType.Inclusion
        if string == "FD":
            return DependencyType.Functional
        raise ArgumentError(f"Unknown candidate type '{string}'")

    def to_str(self):
        return super().name


class DependencyCandidate:
    def __init__(self, dependency_type):
        self.type = dependency_type

    def validate(self, cursor):
        raise NotImplementedError(f"No validation method specified for {self.__class__.__name__}")

    def validate_repeatedly(self, cursor, num_repetitions):
        for _ in range(num_repetitions):
            self.validate(cursor)

    def __str__(self):
        return f"{self.__class__.__name__} {self._to_str()}"

    def _to_str(self):
        raise NotImplementedError(f"No string method specified for {self.__class__.__name__}")


class UccCandidate(DependencyCandidate):
    def __init__(self, table, column):
        DependencyCandidate(DependencyType.Unique)
        self.table = table
        self.column = column

    def validate(self, cursor):
        validate_ucc(cursor, self.table, self.column)

    def _to_str(self):
        return f"{self.table}.{self.column}"


class OdCandidate(DependencyCandidate):
    def __init__(self, table, ordering_column, ordered_column):
        DependencyCandidate(DependencyType.Order)
        self.table = table
        self.ordering_column = ordering_column
        self.ordered_column = ordered_column

    def validate(self, cursor):
        validate_od(cursor, self.table, self.column)

    def _to_str(self):
        return f"{self.table}.{self.ordering_column} |-> {self.table}.{self.ordered_column}"


class IndCandidate(DependencyCandidate):
    def __init__(self, foreign_key_table, foreign_key_column, primary_key_table, primary_key_column):
        DependencyCandidate(DependencyType.Inclusion)
        self.foreign_key_table = foreign_key_table
        self.foreign_key_column = foreign_key_column
        self.primary_key_table = primary_key_table
        self.primary_key_column = primary_key_column

    def validate(self, cursor):
        validate_ind(
            cursor, self.foreign_key_table, self.foreign_key_column, self.primary_key_table, self.primary_key_column
        )

    def _to_str(self):
        return (
            f"{self.foreign_key_table}.{self.foreign_key_column} |-> {self.primary_key_table}.{self.primary_key_column}"
        )


class FdCandidate(DependencyCandidate):
    def __init__(self, table, columns):
        self.table = table
        # Columns are already ordered by the DependentGroupByReductionCandidateRule.
        self.columns = columns

    def validate(self, cursor):
        validate_fd(cursor, table, columns)

    def _to_str(self):
        return ", ".join([f"{self.table}.{column}" for column in self.columns])


def candidates_from_log(benchmark, log_file_path):
    assert os.path.isfile(log_file_path), f"Log file {log_file_path} does not exist"
    candidates = list()
    candidate_re = re.compile(r"(?<=Checking )\w+")

    candidate_parser = {
        DependencyType.Unique: re.compile(r"(\w+)\.(\w+)"),
        DependencyType.Order: re.compile(r"(\w+)\.(\w+) \|-> (\w+)\.(\w+)"),
        DependencyType.Inclusion: re.compile(r"(\w+)\.(\w+) in (\w+)\.(\w+)"),
        DependencyType.Functional: re.compile(r"(\w+)\.(\w+)"),
    }

    # Checking OD household_demographics.hd_demo_sk |-> household_demographics.hd_dep_count
    # Checking UCC date_dim.d_dow
    # Checking IND store_returns.sr_store_sk in store.s_store_sk
    # Checking FD customer.c_custkey, customer.c_name

    with open(log_file_path) as f:
        for line in f:
            match = candidate_re.search(line.strip())
            if match is None:
                continue
            dependency_type = DependencyType.from_str(match.group())
            args = candidate_parser[dependency_type].findall(line)
            assert len(args) > 0, f"Could not parse line: '{line}'"

            if dependency_type == DependencyType.Functional:
                assert len(args) > 1, f"Invalid arguments for FD (expected many, got {len(args)})"
                table = None
                columns = list()
                for table_name, column_name in args:
                    if table is None:
                        table = table_name
                    else:
                        assert table == table_name, "Expected FD candidates from same table"
                    columns.append(column_name)

                candidates.append(FdCandidate(table, columns))
                continue

            for candidate_args in args:
                if dependency_type == DependencyType.Unique:
                    assert (
                        len(candidate_args) == 2
                    ), f"Invalid arguments for UCC (expected 2, got {len(candidate_args)})"
                    candidates.append(UccCandidate(candidate_args[0], candidate_args[1]))
                    continue
                if dependency_type == DependencyType.Order:
                    assert len(candidate_args) == 4, f"Invalid arguments for OD (expected 4, got {len(candidate_args)})"
                    assert candidate_args[0] == candidate_args[2], "Mismatching tables for OD"
                    candidates.append(OdCandidate(candidate_args[0], candidate_args[1], candidate_args[3], str))
                    continue
                if dependency_type == DependencyType.Inclusion:
                    assert (
                        len(candidate_args) == 4
                    ), f"Invalid arguments for IND (expected 4, got {len(candidate_args)})"
                    candidates.append(
                        IndCandidate(candidate_args[0], candidate_args[1], candidate_args[2], candidate_args[3])
                    )
    return candidates


def validate_ucc(cursor, table, column):
    """
    SELECT COUNT(DISTINCT column) = COUNT(column) FROM table
    """
    cursor.execute(f"SELECT COUNT(DISTINCT {column}) = COUNT({column}) FROM {table}")
    if cursor.fetchone() == "1":
        return True
    return False


def validate_ind(cursor, foreign_key_table, foreign_key_column, primary_key_table, primary_key_column):
    """Variants from Abedjan et al.
    (i) Outer Join:
    SELECT foreign_key_column
      FROM foreign_key_table LEFT OUTER JOIN primary_key_table ON foreign_key_column = primary_key_column
     WHERE primary_key_column IS NULL
       AND foreign_key_column IS NOT NULL
     LIMIT 1;

    Note: "In most database management systems, left outer joins provide the fastest SQL-based validation option
           [...]." [p. 58]

    (ii) Set Operation:
    SELECT foreign_key_column
      FROM foreign_key_table
     WHERE foreign_key_column NOT IN (
           SELECT primary_key_column
             FROM primary_key_table
           )
       AND foreign_key_column IS NOT NULL
     LIMIT 1;

    Note: "The performance of the not in join depends very much on the query optimizer." [p. 58]

    (iii) Correlated Subquery:
    SELECT foreign_key_column
      FROM foreign_key_table
     WHERE NOT EXISTS (
           SELECT *
             FROM primary_key_table
            WHERE foreign_key_column = primary_key_column
           )
       AND foreign_key_column IS NOT NULL
     LIMIT 1;

    Note: "In general, correlated subqueries are more expressive than joins and set operations [...]." [p. 59]

    """
    cursor.execute(
        f"SELECT {foreign_key_column} \
        FROM {foreign_key_table} LEFT OUTER JOIN {primary_key_table} ON {foreign_key_column} = {primary_key_column} \
        WHERE {primary_key_column} IS NULL AND {foreign_key_column} IS NOT NULL LIMIT 1;"
    )
    return cursor.fetchone() is None


def validate_od(cursor, table, ordering_column, ordered_column):
    """
    SELECT ordered_column FROM table ORDER BY ordering_column ASCENDING

    Then, check if the result is also ordered ascending (cowardly refusing NULL values for now).
    """
    cursor.execute(f"SELECT {ordered_column} FROM {table} ORDER BY {ordering_column} ASCENDING")
    last_value = None
    values = cursor.fetchall()

    for value in values:
        if value is None:
            return False

        if last_value is None:
            last_value = int(value)
            continue

        # Need to cast to type to ensure correct < comparison. E.g., '9' !< '10'. For now, all ordered_colum candidates
        # are primary keys that can safely be casted to int.
        current_value = int(value)
        if current_value < last_value:
            return False
        last_value = current_value

    return True


def validate_fd(cursor, table, columns):
    for column in columns:
        if validate_ucc(cursor, table, column):
            return True
    return False
