import builtins
import lark.exceptions
import sys
from lark import Lark, Transformer
from berkeleydb import db
import os
import pickle
import itertools

# setting db variables
myDB = None
db_name = 'myDB.db'
db_flag = {}
if len([f for f in os.listdir('.') if f == db_name]) == 0:
    db_flag = {'flags': db.DB_CREATE}


# setting msg
def createTableSuccess(tname):
    return f"\'{tname}\' table is created"


def nonExistingColumnDefError(colname):
    return f"Create table has failed: '{colname}' does not exist in column definition"


def dropSuccess(tname):
    return f"\'{tname}\' table is dropped"


def dropReferencedTableError(tname):
    return f"Drop table has failed: '{tname}' is referenced by other table"


def selectTableExistenceError(tname):
    return f"Selection has failed: '{tname}' does not exist"


syntaxError = "Syntax error"
duplicateColumnDefError = "Create table has failed: column definition is duplicated"
duplicatePrimaryKeryDefError = "Create table has failed: primary key definition is duplicated"
referenceTypeError = "Create table has failed: foreign key references wrong type"
referenceNonPrimaryKeyError = "Create table has failed: foreign key references non primary key column"
referenceColumnExistenceError = "Create table has failed: foreign key references non existing column"
referenceTableExistenceError = "Create table has failed: foreign key references non existing table"
tableExistenceError = "Create table has failed: table with the same name already exists"
charLengthError = "Char length should be over 0"
noSuchTable = "No such table"
insertResult = "The row is inserted"


def super_print(*args, **kwargs):
    builtins.print(*args, **kwargs)


# function to print output with prompt
def printo(*args, **kwargs):
    super_print('DB_2019-12333>', *args, **kwargs)


# class to print out appropriate output for each parsed query.
class MyTransformer(Transformer):
    def create_table_query(self, items):
        # printo('\'CREATE TABLE\' requested')
        empty_dict = {}
        table_name = items[2].children[0].lower()
        col_def_iter = items[3].find_data("column_definition")
        primconstraint_iter = items[3].find_data("primary_key_constraint")
        primiter1, primiter2 = itertools.tee(primconstraint_iter)
        refconstraint_iter = items[3].find_data("referential_constraint")
        schema = (table_name, dict())

        # if such table exists
        if myDB.get(pickle.dumps({'table': table_name})):
            printo(tableExistenceError)
            return items

        for col in col_def_iter:
            col_name = col.children[0].children[0].lower()
            col_type = (col.children[1].children[0],
                        None if len(col.children[1].children) == 1 else int(col.children[1].children[2]))
            col_notnull = 1 if col.children[2] == "not" else 0

            # if column name is repeated
            if col_name in schema[1].keys():
                printo(duplicateColumnDefError)
                return items
            # if char length is set less than 1
            if col_type[1] is not None and col_type[1] <= 0:
                printo(charLengthError)
                return items

            # add the column info to the schema, and make an empty list to store the column records
            schema[1][col_name] = {'type': col_type, 'notnull': col_notnull, 'pk': 0, 'fk': None}
            empty_dict[col_name] = []

        # primary key should be declared once
        prim_line = len(list(primiter1))
        if prim_line > 1:
            printo(duplicatePrimaryKeryDefError)
            return items
        if prim_line == 1:
            primary = next(primiter2)
            for col in primary.children[2].find_data("column_name"):
                # if the column itself has not been declared, it cannot be a pk
                if col.children[0].lower() not in schema[1].keys():
                    printo(nonExistingColumnDefError(col.children[0].lower()))
                    return items
                # note that a duplicate input of pk columns in a same line is redundant, so not an error.
                schema[1][col.children[0].lower()]['pk'] = 1
                schema[1][col.children[0].lower()]['notnull'] = 1

        for ref in refconstraint_iter:
            # cur: iterator for foreign key columns
            # origin: iterator for primary keys(yet assumed) of the table being referenced
            cols = ref.find_data("column_name_list")
            cur = next(cols).find_data("column_name")
            cur1, cur2 = itertools.tee(cur)
            origin = next(cols).find_data("column_name")
            origin1, origin2 = itertools.tee(origin)

            # referencing table should exist
            ref_table = ref.children[4].children[0].lower()
            if not myDB.get(pickle.dumps({'table': ref_table})):
                printo(referenceTableExistenceError)
                return items

            # cur length == origin length == primary keys'(real) length
            ref_columns = pickle.loads(myDB.get(pickle.dumps({'table': ref_table})))
            pk_cnt = 0
            for col, content in ref_columns.items():
                if content['pk'] == 1:
                    pk_cnt += 1
            col_len = len(list(cur1))
            if col_len != len(list(origin1)) or col_len != pk_cnt:
                printo(referenceNonPrimaryKeyError)
                return items

            # check errors by comparing rth column from cur and origin
            for r in range(col_len):
                cur_col = next(cur2).children[0].lower()
                origin_col = next(origin2).children[0].lower()
                if cur_col not in schema[1].keys():
                    printo(nonExistingColumnDefError(cur_col))
                    return items
                if origin_col not in ref_columns.keys():
                    printo(referenceColumnExistenceError)
                    return items
                if schema[1][cur_col]['type'] != ref_columns[origin_col]['type']:
                    printo(referenceTypeError)
                    return items
                if ref_columns[origin_col]['pk'] != 1:
                    printo(referenceNonPrimaryKeyError)
                    return items
                schema[1][cur_col]['fk'] = ref_table
        # to be transactional, put the schema to the db after all constraints are checked
        # {'table':~} is for table info
        # {'record':~} is for saving record
        myDB.put(pickle.dumps({'table': schema[0]}), pickle.dumps(schema[1]))
        myDB.put(pickle.dumps({'record': schema[0]}), pickle.dumps(empty_dict))
        printo(createTableSuccess(table_name))
        return items

    def drop_table_query(self, items):
        # printo('\'DROP TABLE\' requested')
        table_name = items[2].children[0].lower()
        table_name_key = pickle.dumps({'table': table_name})
        record_key = pickle.dumps(({'record': table_name}))

        # dropping table must exist
        if not myDB.get(table_name_key):
            printo(noSuchTable)
            return items

        # check other table infos in order to find the referencing info
        cursor = myDB.cursor()
        while x := cursor.next():
            if 'record' in pickle.loads(x[0]).keys():
                continue
            col_dict = pickle.loads(x[1])
            for col in col_dict.keys():
                if col_dict[col]['fk'] == table_name:
                    printo(dropReferencedTableError(table_name))
                    return items

        # delete both info and record
        myDB.delete(table_name_key)
        myDB.delete(record_key)
        printo(dropSuccess(table_name))
        return items

    # in project 1-2, we assume that all columns are selected
    def select_query(self, items):
        # printo('\'SELECT\' requested')
        table_names = items[2].find_data("table_name")
        for table in table_names:
            table_name_key = pickle.dumps({'table': table.children[0].lower()})
            # selecting table must exist
            if not myDB.get(table_name_key):
                printo(selectTableExistenceError(table.children[0].lower()))
                return items
            table_name = table.children[0].lower()
            # select_columns: table(column) infos, column_records: actual records
            select_columns = pickle.loads(myDB.get(table_name_key))
            column_records = pickle.loads(myDB.get(pickle.dumps({'record': table_name})))
            super_print("+-------------------------" * len(select_columns.keys()) + "+")
            for col_name, col_content in select_columns.items():
                super_print(f"|{col_name.upper():^25}", end="")
            super_print("|")
            super_print("+-------------------------" * len(select_columns.keys()) + "+")
            # the length of the records
            rec_len = len(column_records[next(iter(column_records))])
            for idx in range(rec_len):
                super_print("|", end="")
                for col, records in column_records.items():
                    super_print(f"  {records[idx]:<23}|", end="")
                super_print()
            super_print("+-------------------------" * len(select_columns.keys()) + "+")
        return items

    # in project 1-2, we assume that valid tuples are inserted
    def insert_query(self, items):
        # printo('\'INSERT\' requested')
        insert_table = items[2].children[0].lower()
        value_list = next(items[4].find_data("value_list"))
        insert_dict = {}
        if not myDB.get(pickle.dumps({'table': insert_table})):
            printo(noSuchTable)
            return items
        insert_columns = pickle.loads(myDB.get(pickle.dumps({'table': insert_table})))
        column_records = pickle.loads(myDB.get(pickle.dumps({'record': insert_table})))
        # assuming appropriate number of appropriate values are in the value_list!
        line_columns = value_list.find_data("comparable_value")
        for col_name, col_content in insert_columns.items():
            insert_value = next(line_columns).children[0]
            # slicing the string to match the length constraint
            # we assumed that the tuple is valid, so the string should always start and end with "'"
            if col_content['type'][0] == 'char':
                insert_value = insert_value[1:-1][:col_content['type'][1]]
            insert_dict[col_name] = insert_value

        for col, val_list in insert_dict.items():
            column_records[col].append(insert_dict[col])
        myDB.put(pickle.dumps({'record': insert_table}), pickle.dumps(column_records))
        printo(insertResult)
        return items

    def explain_query(self, items):
        # printo('\'EXPLAIN\' requested')
        table_name = items[1].children[0].lower()
        table_name_key = pickle.dumps({'table': table_name})
        if not myDB.get(table_name_key):
            printo(noSuchTable)
            return items
        super_print("-----------------------------------------------------------------")
        super_print(f"table_name [{table_name}]")
        columns = pickle.loads(myDB.get(table_name_key))
        super_print(f"column_name              type           null      key       ")
        for col_name, col_content in columns.items():
            super_print(
                f"{col_name:<25}{col_content['type'][0] + '(' + str(col_content['type'][1]) + ')' if col_content['type'][0] == 'char' else col_content['type'][0]:<15}"
                f"{'N' if col_content['notnull'] else 'Y':<10}"
                f"{'PRI/FOR' if col_content['pk'] and col_content['fk'] else 'PRI' if col_content['pk'] else 'FOR' if col_content['fk'] else '':<10}")
        super_print("-----------------------------------------------------------------")
        return items

    def describe_query(self, items):
        # printo('\'DESCRIBE\' requested')
        table_name = items[1].children[0].lower()
        table_name_key = pickle.dumps({'table': table_name})
        if not myDB.get(table_name_key):
            printo(noSuchTable)
            return items
        super_print("-----------------------------------------------------------------")
        super_print(f"table_name [{table_name}]")
        columns = pickle.loads(myDB.get(table_name_key))
        super_print(f"column_name              type           null      key       ")
        for col_name, col_content in columns.items():
            super_print(
                f"{col_name:<25}{col_content['type'][0] + '(' + str(col_content['type'][1]) + ')' if col_content['type'][0] == 'char' else col_content['type'][0]:<15}"
                f"{'N' if col_content['notnull'] else 'Y':<10}"
                f"{'PRI/FOR' if col_content['pk'] and col_content['fk'] else 'PRI' if col_content['pk'] else 'FOR' if col_content['fk'] else '':<10}")
        super_print("-----------------------------------------------------------------")
        return items

    def desc_query(self, items):
        # printo('\'DESC\' requested')
        table_name = items[1].children[0].lower()
        table_name_key = pickle.dumps({'table': table_name})
        if not myDB.get(table_name_key):
            printo(noSuchTable)
            return items
        super_print("-----------------------------------------------------------------")
        super_print(f"table_name [{table_name}]")
        columns = pickle.loads(myDB.get(table_name_key))
        super_print(f"column_name              type           null      key       ")
        for col_name, col_content in columns.items():
            super_print(
                f"{col_name:<25}{col_content['type'][0] + '(' + str(col_content['type'][1]) + ')' if col_content['type'][0] == 'char' else col_content['type'][0]:<15}"
                f"{'N' if col_content['notnull'] else 'Y':<10}"
                f"{'PRI/FOR' if col_content['pk'] and col_content['fk'] else 'PRI' if col_content['pk'] else 'FOR' if col_content['fk'] else '':<10}")
        super_print("-----------------------------------------------------------------")
        return items

    def delete_query(self, items):
        printo('\'DELETE\' requested')
        return items

    def show_query(self, items):
        # printo('\'SHOW TABLES\' requested')
        super_print("------------------------")
        cursor = myDB.cursor()
        while x := cursor.next():
            typeinfo = pickle.loads(x[0])
            if typeinfo.get('table'):
                super_print(typeinfo.get('table'))
        super_print("------------------------")
        return items

    def update_query(self, items):
        printo('\'UPDATE\' requested')
        return items

    def exit_query(self, items):
        if myDB:
            myDB.close()
        sys.exit()


# setting tools for parsing
my_transformer = MyTransformer()
with open('grammar.lark') as file:
    sql_parser = Lark(file.read(), start="command", lexer="basic")

# setting db with variables
myDB = db.DB()
myDB.open(db_name, dbtype=db.DB_HASH, **db_flag)

# Loops until the transformer detects an exit query.
# Appends ' ' at the end of each line to as we ignore newline.
while True:
    inputs = input('DB_2019-12333> ') + ' '
    # Loops until the query(queries) ends with ';'
    while not inputs.strip().endswith(';'):
        inputs += input() + ' '
    input_array = inputs.strip().split(';')
    # The last element in the array should be '', so ignore it.
    for i in range(len(input_array) - 1):
        try:
            output = sql_parser.parse(input_array[i] + ';')
            my_transformer.transform(output)
        except lark.exceptions.UnexpectedInput as e:
            # printo(f'Syntax error in pos {e.pos_in_stream} of number {i+1} request.')
            printo('Syntax error')
            break
