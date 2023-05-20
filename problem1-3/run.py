import builtins
import re
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

# other global variables
datepattern = re.compile(r'\d{4}-\d{2}-\d{2}')
comp_op = ['>', '<', '=', '!=', '>=', '<=']

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

def insertColumnExistenceError(cname):
    return f"Insertion has failed: '{cname}' does not exist"

def insertColumnNonNullableError(cname):
    return f"Insertion has failed: '{cname}' is not nullable"

def selectColumnResolveError(cname):
    return f"Selection has failed: fail to resolve '{cname}'"

def deleteResult(count):
    return f"'{count}’ row(s) are deleted"

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

insertTypeMismatchError = "Insertion has failed: Types are not matched"
whereIncomparableError = "Where clause trying to compare incomparable values"
whereTableNotSpecified = "Where clause trying to reference tables which are not specified"
whereColumnNotExist = "Where clause trying to reference non existing column"
whereAmbiguousReference = "Where clause contains ambiguous reference"


def super_print(*args, **kwargs):
    builtins.print(*args, **kwargs)


# function to print output with prompt
def printo(*args, **kwargs):
    super_print('DB_2019-12333>', *args, **kwargs)

def compute(operand1, operand2, op):
    if operand1==None or operand2==None:
        return False
    elif op=='>':
        return operand1>operand2
    elif op=='<':
        return operand1<operand2
    elif op=='=':
        return operand1==operand2
    elif op=='!=':
        return operand1!=operand2
    elif op=='>=':
        return operand1>=operand2
    else:
        return operand1<=operand2


def test_where(boolean_expr, columns, columns_only, tables):
    boolean_tests = boolean_expr.find_data("boolean_test")
    for boolean_test in boolean_tests:
        if boolean_test.children[0].data=='predicate':
            if boolean_test.children[0].children[0].data=='comparison_predicate':
                operand1 = boolean_test.children[0].children[0].children[0]
                operand2 = boolean_test.children[0].children[0].children[2]
                if not operand1.children[0]:  # only column name
                    operand1 = operand1.children[1].children[0].lower()
                    if not (operand1 in columns_only):
                        printo(whereColumnNotExist)
                        return -1
                    elif not (operand1 in columns):
                        printo(whereAmbiguousReference)
                        return -1
                    table_info = pickle.loads(myDB.get(pickle.dumps({'table': tables[columns.index(operand1)]})))
                    operand1_type = table_info[operand1]['type'][0]
                elif operand1.children[0].data == "table_name":  # column name with table name
                    operand1_table = operand1.children[0].children[0].lower()
                    operand1_column = operand1.children[1].children[0].lower()
                    operand1 = operand1_table + "." + operand1_column
                    if (operand1 in columns):
                        table_info = pickle.loads(myDB.get(pickle.dumps({'table': tables[columns.index(operand1)]})))
                        operand1_type = table_info[operand1_column]['type'][0]
                    elif (operand1_column in columns) and (operand1_table == tables[columns.index(operand1_column)]):
                        table_info = pickle.loads(
                            myDB.get(pickle.dumps({'table': tables[columns.index(operand1_column)]})))
                        operand1_type = table_info[operand1_column]['type'][0]
                    else:
                        if not operand1_table in tables:
                            printo(whereTableNotSpecified)
                            return -1
                        else:
                            printo(whereColumnNotExist)
                            return -1
                else:  # comparable value
                    operand1 = operand1.children[0].children[0]
                    if operand1.startswith("") or operand1.startswith(''):
                        operand1_type = "char"
                    elif "-" in operand1:
                        operand1_type = "date"
                    else:
                        operand1_type = "int"

                if not operand2.children[0]:  # only column name
                    operand2 = operand2.children[1].children[0].lower()
                    if not (operand2 in columns_only):
                        printo(whereColumnNotExist)
                        return -1
                    elif not (operand2 in columns):
                        printo(whereAmbiguousReference)
                        return -1
                    table_info = pickle.loads(myDB.get(pickle.dumps({'table': tables[columns.index(operand2)]})))
                    operand2_type = table_info[operand2]['type'][0]
                elif operand2.children[0].data == "table_name":  # column name with table name
                    operand2_table = operand2.children[0].children[0].lower()
                    operand2_column = operand2.children[1].children[0].lower()
                    operand2 = operand2_table + "." + operand2_column
                    if (operand2 in columns):
                        table_info = pickle.loads(myDB.get(pickle.dumps({'table': tables[columns.index(operand2)]})))
                        operand2_type = table_info[operand2_column]['type'][0]
                    elif (operand2_column in columns) and (operand2_table == tables[columns.index(operand2_column)]):
                        table_info = pickle.loads(
                            myDB.get(pickle.dumps({'table': tables[columns.index(operand2_column)]})))
                        operand2_type = table_info[operand2_column]['type'][0]
                    else:
                        if not operand2_table in tables:
                            printo(whereTableNotSpecified)
                            return -1
                        else:
                            printo(whereColumnNotExist)
                            return -1
                else:  # comparable value
                    operand2 = operand2.children[0].children[0]
                    if operand2.startswith("\"") or operand2.startswith("\'"):
                        operand2_type = "char"
                    elif "-" in operand2:
                        operand2_type = "date"
                    else:
                        operand2_type = "int"

                if operand1_type != operand2_type:
                    printo(whereIncomparableError)
                    return -1
            else: #null predicate
                null_predicate = boolean_test.children[0].children[0]
                operand_table = null_predicate.children[0]
                operand_column = null_predicate.children[1].children[0].lower()
                operand = operand_column
                if operand_table:
                    operand_table = operand_table.children[0].lower()
                    operand = operand_table + "." + operand_column
                    if not ((operand in columns) or (
                            (operand_column in columns) and (operand_table == tables[columns.index(operand_column)]))):
                        if not (operand_table in tables):
                            printo(whereTableNotSpecified)
                            return -1
                        else:
                            printo(whereColumnNotExist)
                            return -1
                else:
                    if not (operand in columns_only):
                        printo(whereColumnNotExist)
                        return -1
                    if not (operand in columns):
                        printo(whereAmbiguousReference)
                        return -1

        else: # only to notify that we're only checking predicate nodes
            pass



def test(notidx, boolean_test, record, columns, columns_only, tables):
    if boolean_test.children[0].data == "predicate":
        if boolean_test.children[0].children[0].data == "comparison_predicate":
            operand1 = boolean_test.children[0].children[0].children[0]
            operand2 = boolean_test.children[0].children[0].children[2]
            op = boolean_test.children[0].children[0].children[1].children[0]
            if not operand1.children[0]:  # only column name
                operand1 = operand1.children[1].children[0].lower()
                operand1 = record[columns.index(operand1)]
            elif operand1.children[0].data == "table_name":  # column name with table name
                operand1_table = operand1.children[0].children[0].lower()
                operand1_column = operand1.children[1].children[0].lower()
                operand1 = operand1_table + "." + operand1_column
                if (operand1 in columns):
                    operand1 = record[columns.index(operand1)]
                elif (operand1_column in columns) and (operand1_table==tables[columns.index(operand1_column)]):
                    operand1 = record[columns.index(operand1_column)]
            else:  # comparable value
                operand1 = operand1.children[0].children[0]
                if operand1.startswith("") or operand1.startswith(''):
                    operand1=operand1[1:-1]
                elif not ("-" in operand1):
                    operand1=int(operand1)

            if not operand2.children[0]:  # only column name
                operand2 = operand2.children[1].children[0].lower()
                operand2 = record[columns.index(operand2)]
            elif operand2.children[0].data == "table_name":  # column name with table name
                operand2_table = operand2.children[0].children[0].lower()
                operand2_column = operand2.children[1].children[0].lower()
                operand2 = operand2_table + "." + operand2_column
                if (operand2 in columns):
                    operand2 = record[columns.index(operand2)]
                elif (operand2_column in columns) and (operand2_table == tables[columns.index(operand2_column)]):
                    operand2 = record[columns.index(operand2_column)]
            else:  # comparable value
                operand2 = operand2.children[0].children[0]
                if operand2.startswith("\"") or operand2.startswith("\'"):
                    operand2=operand2[1:-1]
                elif not ("-" in operand2):
                    operand2=int(operand2)

            if notidx:
                op = comp_op[5 - comp_op.index(op)]
            return int(compute(operand1, operand2, op))

        else:  # null_predicate
            null_predicate = boolean_test.children[0].children[0]
            operand_table = null_predicate.children[0]
            operand_column = null_predicate.children[1].children[0].lower()
            operand = operand_column
            if operand_table:
                operand_table = operand_table.children[0].lower()
                operand = operand_table+"."+operand_column
                if operand in columns:
                    operand = record[columns.index(operand)]
                elif (operand_column in columns) and (operand_table==tables[columns.index(operand_column)]):
                    operand = record[columns.index(operand_column)]
            else:
                operand = record[columns.index(operand)]

            if (notidx and null_predicate.children[2].children[1]) or (not notidx and not null_predicate.children[2].children[1]):
                return int(operand is None)
            else:
                return int(not(operand is None))

    elif boolean_test.children[0].data == "parenthesized_boolean_expr":
        boolean_terms = boolean_test.children[0].children[1].children
        for boolean_term in boolean_terms:
            if boolean_term == "or": continue
            boolean_factors=boolean_term.children
            for boolean_factor in boolean_factors:
                if boolean_factor == "and": continue
                test_result = test(boolean_factor.children[0], boolean_factor.children[1], record, columns,columns_only, tables)
                if not test_result:
                    break
            else: #all boolean_facors true
                if notidx: return 0
                else: return 1
        if notidx: return 1
        else: return 0


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

    def select_query(self, items):
        # printo('\'SELECT\' requested')
        # from clause
        table_names = next(items[2].find_data("table_reference_list")).find_data("table_name")
        temp_from_table = [] # final cartesian from table
        table_col_names = [] # final col names of temp_from_table
        table_for_columns=[] # final table names(duplicated) of temp_from_table
        table_onlycol_names = []
        for table in table_names:
            temp_records=[]
            tname = table.children[0].lower()
            t_records = myDB.get(pickle.dumps({'record':tname}))
            # checking table existence
            if t_records:
                t_records = pickle.loads(t_records)
            else:
                printo(selectTableExistenceError(tname))
                return items

            # appending new column names to table_col_names, and add table name when duplicate name exists
            for colname, values in t_records.items():
                try:
                    index = table_onlycol_names.index(colname)
                    table_col_names[index]=table_for_columns[index]+'.'+colname
                    table_col_names.append(tname+'.'+colname)
                    table_for_columns.append(tname)
                    table_onlycol_names.append(colname)
                except ValueError:
                    table_col_names.append(colname)
                    table_for_columns.append(tname)
                    table_onlycol_names.append(colname)
                temp_records.append(values)
            # cartesian product of current table and new table
            if temp_from_table:
                temp_cartesian_table = []
                # construct empty temporary cartesian table
                for i in range(len(temp_from_table)):
                    temp_cartesian_table.append([])
                for i in range(len(temp_records)):
                    temp_cartesian_table.append([])
                # cartesian product of two tables
                for i in range(len(temp_from_table[0])):
                    for r in range(len(temp_records[0])):
                        for j in range(len(temp_from_table)):
                            if temp_from_table[j]:
                                temp_cartesian_table[j].append(temp_from_table[j][i])
                        for j in range(len(temp_records)):
                            temp_cartesian_table[j + len(temp_from_table)].append(temp_records[j][r])
                temp_from_table = temp_cartesian_table
            else:
                temp_from_table = temp_records

        # where clause
        temp_select_table = []
        try:
            where_clause = next(items[2].find_data('where_clause'))
            boolean_terms = where_clause.children[1].children
            # building empty select table from from table
            for i in range(len(temp_from_table)):
                temp_select_table.append([])

            # checking where_clause validity
            if test_where(where_clause.children[1], table_col_names, table_onlycol_names, table_for_columns)==-1:
                        return items
            for record_index in range(len(temp_from_table[0])):
                record = [temp_from_table[j][record_index] for j in range(len(temp_from_table))]
                for boolean_term in boolean_terms:
                    if boolean_term == "or": continue
                    boolean_factors = boolean_term.children
                    # if 'and' in boolean_factors:
                    #     boolean_factors.remove('and')
                    for boolean_factor in boolean_factors:
                        if boolean_factor== "and": continue
                        test_result = test(boolean_factor.children[0], boolean_factor.children[1], record, table_col_names, table_onlycol_names, table_for_columns)
                        if test_result == 0:
                            break
                        elif test_result < 0:
                            return items
                    else: # all conditions met
                        for i in range(len(temp_from_table)):
                            temp_select_table[i].append(record[i])
                        break
        except StopIteration:
            temp_select_table = temp_from_table
        # select clause
        # selecting columns from temp_select_table.
        # total columns are in table_col_names
        # total tables are in table_for_columns
        selected_columns = items[1].children
        if selected_columns[0] =="*":
            final_select_table = temp_select_table
            final_select_colnames = table_col_names
        else:
            final_select_table = []
            final_select_colnames = []
            for select_column in selected_columns:
                tname = select_column.children[0]
                cname = select_column.children[1].children[0].lower()
                if tname:
                    tname = tname.children[0].lower()
                    tcname = tname + "." + cname
                    if tcname in table_col_names:
                        final_select_colnames.append(tcname)
                        final_select_table.append(temp_select_table[table_col_names.index(tcname)])
                    elif (cname in table_col_names) and (tname==table_for_columns[table_col_names.index(cname)]):
                        final_select_colnames.append(tcname)
                        final_select_table.append(temp_select_table[table_col_names.index(cname)])
                    else:
                        printo(selectColumnResolveError(cname))
                        return items
                else:
                    if not cname in table_col_names: # no such col/ambiguous
                        printo(selectColumnResolveError(cname))
                        return items
                    final_select_colnames.append(cname)
                    final_select_table.append(temp_select_table[table_col_names.index(cname)])

        super_print("+----------------------------------------" * len(final_select_colnames) + "+")
        for cname in final_select_colnames:
            super_print(f"|{cname.upper():^40}", end="")
        super_print("|")
        super_print("+----------------------------------------" * len(final_select_colnames) + "+")
        # the length of the records
        for idx in range(len(final_select_table[0])):
            super_print("|", end="")
            for column in final_select_table:
                if column[idx] == None:
                    super_print(f"  {'null':<38}|", end="")
                else:
                    super_print(f"  {column[idx]:<38}|", end="")
            super_print()
        super_print("+----------------------------------------" * len(final_select_colnames) + "+")
        return items

    # in project 1-3, we assume that inserted tuples do not violate pk/fk constraints
    def insert_query(self, items):
        # printo('\'INSERT\' requested')
        insert_table = items[2].children[0].lower()
        insert_table_key = pickle.dumps(({'table': insert_table}))
        if not myDB.get(insert_table_key):
            printo(noSuchTable)
            return items
        value_list = next(items[4].find_data("value_list"))
        if not myDB.get(pickle.dumps({'table': insert_table})):
            printo(noSuchTable)
            return items
        i_columns = pickle.loads(myDB.get(pickle.dumps({'table': insert_table})))
        # if column_clause exists, insert_columns are redefined.
        # here we assume that only the order of the columns can be redefined.
        if items[3]:
            insert_columns = {}
            for col in items[3].children[1:-1]:
                try:
                    insert_columns[col.children[0].lower()] = i_columns[col.children[0].lower()]
                except KeyError:
                    printo(insertColumnExistenceError(col.children[0].lower()))
                    return items
        else:
            insert_columns = i_columns
        # column_clauses should be identical with original columns except for ordering
        if len(insert_columns) != len(i_columns):
            printo(insertTypeMismatchError)
            return items
        column_records = pickle.loads(myDB.get(pickle.dumps({'record': insert_table})))
        # assuming appropriate number of appropriate values are in the value_list!
        line_columns = value_list.find_data("comparable_value_null")
        line_columns, line_columns2 = itertools.tee(line_columns)
        # numbers of attributes should match
        if len(list(line_columns2)) != len(insert_columns):
            printo(insertTypeMismatchError)
            return items
        insert_dict = {}
        for col_name, col_content in insert_columns.items():
            insert_value = next(line_columns).children[0].children[0]
            if isinstance(insert_value, str) and insert_value.lower() == "null":
                if col_content['notnull']:
                    printo(insertColumnNonNullableError(col_name))
                    return items
                else:
                    insert_dict[col_name] = None
                    continue
            # slicing the string to match the length constraint
            if not ((col_content['type'][0], insert_value.type) in [('char', 'STR'), ('int','INT'), ('date', 'DATE')]):
                printo(insertTypeMismatchError)
                return items
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
        # printo('\'DELETE\' requested')
        table_name = items[2].children[0].lower()
        table = myDB.get(pickle.dumps({'record': table_name}))
        if not table:
            printo(noSuchTable)
            return items
        table = pickle.loads(table)
        deleted_indices = []
        temp_delete_table=[]
        table_col_names = []
        table_onlycol_names = []
        table_for_columns = []
        for cname, values in table.items():
            temp_delete_table.append(values)
            table_col_names.append(cname)
            table_onlycol_names.append(cname)
            table_for_columns.append(table_name)
        where_clause = items[3]
        if where_clause:
            boolean_terms=where_clause.children[1].children
            # checking where_clause validity
            for boolean_term in boolean_terms:
                if boolean_term == "or": continue
                boolean_factors = boolean_term.children
                for boolean_factor in boolean_factors:
                    if boolean_factor == "and": continue
                    if test_where(boolean_factor.children[1], table_col_names, table_onlycol_names,
                                  table_for_columns) == -1:
                        return items

            for record_index in range(len(temp_delete_table[0])):
                record = [temp_delete_table[j][record_index] for j in range(len(temp_delete_table))]
                for boolean_term in boolean_terms:
                    if boolean_term == "or": continue
                    boolean_factors = boolean_term.children
                    for boolean_factor in boolean_factors:
                        if boolean_factor == "and": continue
                        test_result = test(boolean_factor.children[0], boolean_factor.children[1], record, table_col_names, table_onlycol_names, table_for_columns)
                        if test_result == 0:
                            break
                        elif test_result < 0:
                            return items
                    else: # all conditions met
                        deleted_indices.append(record_index)
                        break
        else:
            deleted_indices = [i for i in range(len(temp_delete_table[0]))]
        newtable={}
        for cname, values in table.items():
            newvalues=[]
            for value_index in range(len(values)):
                if not(value_index in deleted_indices):
                    newvalues.append(values[value_index])
            newtable[cname] = newvalues
        myDB.put(pickle.dumps({'record': table_name}), pickle.dumps(newtable))
        printo(deleteResult(len(deleted_indices)))


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
            # print(output.pretty())
            # print(output)
            my_transformer.transform(output)
        except lark.exceptions.UnexpectedInput as e:
            # printo(f'Syntax error in pos {e.pos_in_stream} of number {i+1} request.')
            printo('Syntax error')
            break
