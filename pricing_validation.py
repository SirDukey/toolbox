from vf_db import db
from datetime import datetime
from bson import ObjectId
from time import sleep
from vf_lib.connection import loop_all_dbs


TMP_TABLE_NAME = 'TPM-3194_27Mar'


def compare_pricing_data(database_list=None, temp_table=TMP_TABLE_NAME, uat_ip='UAT', prod_ip='PROD'):
    if not database_list:
        dbs = sorted(db.security_db.database.distinct('databaseid'))
    else:
        dbs = database_list
    for db_name in dbs:
        prod = 'promotion_internal_price_{}_{}'.format(temp_table, prod_ip)
        uat = 'promotion_internal_price_{}_{}'.format(temp_table, uat_ip)
        print('DB: {}'.format(db_name))
        try:
            db.connect_by_database_id(db_name, '10.0.2.201')
            a = {(row['aid'], row['pid'], row['frm']): row['prc']['nsv_norm'] for row in
                 db.user_db[prod].find({}, {"_id": 0, 'pid': 1, 'aid': 1, 'frm': 1, 'prc.nsv_norm': 1}) if row.get('prc', {}).get('nsv_norm')}
            b = {(row['aid'], row['pid'], row['frm']): row['prc']['nsv_norm'] for row in
                 db.user_db[uat].find({}, {"_id": 0, 'pid': 1, 'aid': 1, 'frm': 1, 'prc.nsv_norm': 1}) if row.get('prc', {}).get('nsv_norm')}

            mismatch_a = {k: (v, b.get(k)) for k,v in a.items() if v != b.get(k)}
            if mismatch_a:
                k = list(mismatch_a.keys())[0]
                example_a = list(k) + list(mismatch_a[k])
            else:
                example_a = ''

            mismatch_b = {k: (v, a.get(k)) for k,v in b.items() if v != a.get(k)}
            if mismatch_b:
                k = list(mismatch_b.keys())[0]
                example_b = list(k) + list(mismatch_b[k])
            else:
                example_b = ''
            print('{}: Prod {} vs Uat {}, mismatches {} (example: {}) vs {} (example: {})'.format(
                db_name,
                len(a),
                len(b),
                len(mismatch_a),
                example_a,
                len(mismatch_b),
                example_b
            ))
        except:
            print('Error!')



# aid = ObjectId('6152cd29de8e30a2f76c545d')
# pid = ObjectId('60f9168be3e9f3c194f53697')
# frm = datetime(2023, 3, 1, 0, 0)
# to = datetime(2023, 3, 31, 0, 0)
# qf = {'aid': aid, 'pid': pid, 'frm': frm, 'to': to}
# qp = {'prc.disc': 1}
# product_prod = db.user_db['promotion_internal_price_{}_PROD'.format(TMP_TABLE_NAME)].find_one(qf, qp)
# product_uat = db.user_db['promotion_internal_price_{}_UAT'.format(TMP_TABLE_NAME)].find_one(qf, qp)
# product_prod['prc']['disc'] == product_uat['prc']['disc']

########################################################################################################################

#pid = ObjectId('60f9168be3e9f3c194f53697')
#aid = ObjectId('6152cd29de8e30a2f76c545d')


def check_promotion_internal_price(aid_filter=None, pid_filter=None, uat_collection='promotion_internal_price_simulation',
                                   prod_collection='promotion_internal_price', slow_output=0.0, verbose_level=0):
    """
    The combination of account, product, to, frm is used to check if prc.disc value is the same between the collections
    generated from sap_pricing_test.py
    This can only be run from a production process server with access to the production databases
    Example usage:
        check_promotion_internal_price([aid], [pid])
    Args:
        aid_filter: list of ObjectId values
        pid_filter: list of ObjectId values
        uat_collection: collection where pricing was generated using uat code
        prod_collection: collection where pricing was generated using production code
        slow_output: float, seconds to delay product output information, useful if no aid or pid is set
        verbose_level: 0 for standard output, 1 for product details, 2 for product discount details

    Returns:
        terminal output information for different verbose levels
        verbose_level == 0:
            (db_name, 'product issue found, set verbose_level=1 for details')
        verbose_level == 1:
            (db_name, aid, pid, frm, to) where there is a difference in the prc.disc value
        verbose_level == 2:
            (db_name, aid, pid, frm, to) where there is a difference in the prc.disc value and
            (db_name, 'uat: ', extra_values_uat, 'prod: ', extra_values_prod) where extra_values_uat is a value in the
            prc.disc list which is not in extra_value_prod and vice versa
    """
    db_name = db.user_db.name
    collection_uat = db.user_db[uat_collection]
    collection_prod = db.user_db[prod_collection]
    aid_filter = aid_filter or collection_uat.distinct('aid')

    count_prod = 0
    count_uat = 0
    if aid_filter:
        for aid in aid_filter:
            count_prod_per_aid = collection_prod.count_documents({'aid': aid})
            count_prod += count_prod_per_aid
            count_uat_per_aid = collection_uat.count_documents({'aid': aid})
            count_uat += count_uat_per_aid
    else:
        count_prod = collection_prod.count_documents({})
        count_uat = collection_uat.count_documents({})

    # check the overall collection size
    if count_uat == 0 and count_prod == 0:
        print(db_name, 'no data in uat or prod')
        return
    elif count_uat == 0 or count_prod == 0:
        # pricing test did not yield any data, skip the database
        print(db_name, 'a collection is empty, uat: {} vs prod: {}'.format(count_uat, count_prod))
        return
    elif count_uat != count_prod:
        print(db_name, 'collections are not the same, uat: {} != prod: {}'.format(count_uat, count_prod))

    qp = {'_id': 0, 'prc.disc': 1}

    # loop through the accounts
    for aid in aid_filter:
        qf = {'aid': aid}
        pid_filter = pid_filter or collection_uat.distinct('pid', {'aid': aid})
        total = len(pid_filter)

        # loop through the products
        product_issue_found = False
        for counter, pid in enumerate(pid_filter, start=1):
            qf['pid'] = pid
            date_start = collection_uat.distinct('frm', qf)
            date_end = collection_uat.distinct('to', qf)
            product_date_range = zip(date_start, date_end)
            # loop through the date ranges
            for (frm, to) in product_date_range:
                qf['frm'] = frm
                qf['to'] = to
                product_prod = collection_prod.find_one(qf, qp)
                product_uat = collection_uat.find_one(qf, qp)
                if not product_uat or not product_prod:
                    print(db_name, aid, pid, frm, to, 'missing product data, uat: {} vs prod: {}'.format(
                        bool(product_uat), bool(product_prod)))
                    continue
                disc_uat = product_uat['prc']['disc']
                disc_prod = product_prod['prc']['disc']
                check = disc_prod == disc_uat
                if not check:
                    product_issue_found = True
                    if verbose_level >= 1:
                        print(db_name, aid, pid, frm, to, '{} of {}'.format(counter, total))
                        sleep(slow_output)

                        if verbose_level == 2:
                            extra_values_uat = [x for x in disc_uat if x not in disc_prod]
                            extra_values_prod = [x for x in disc_prod if x not in disc_uat]
                            print(db_name, 'uat: ', extra_values_uat, 'prod: ', extra_values_prod)

        if product_issue_found and verbose_level < 1:
            print(db_name, 'product issue found, set verbose_level=1 for details and 2 for details & values')



db.security_connect()
db_list = sorted(
    x for x in db.security_db.database.distinct('databaseid') if
    'demo' not in x and
    'zendesk' not in x and
    'qa' not in x and
    'bootcamp' not in x and
    'test' not in x and
    'system_reporting' not in x and
    'deloitte' not in x and
    'bpx' not in x
)

# loop through the databases
for database_name in db_list:
    db.connect_by_database_id(database_name)
    check_promotion_internal_price(TMP_TABLE_NAME)


@loop_all_dbs()
def purge_test_collections(clean=False):
    tmp_table_name = 'TPM-3194_27Mar'
    production_collections = ['sap_condition', 'promotion_internal_price']

    total_collections_to_remove = []
    for production_collection in production_collections:
        collections_to_remove = [x for x in db.user_db.list_collection_names() if production_collection in x
                                 and x != production_collection
                                 and tmp_table_name not in x
                                 and 'autotest' not in x
                                 and 'backup' not in x
                                 and x != '{}_tmp'.format(production_collection)]
        total_collections_to_remove.extend(collections_to_remove)

    if clean:
        for c in total_collections_to_remove:
            db.user_db.drop_collection(c)
    else:
        for col in total_collections_to_remove:
            print(col)
