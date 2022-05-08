import pandas as pd
from sqlalchemy import create_engine

# connect to PostgresQL DB

conn_string = ''

engine = create_engine(conn_string)

# Legend:
# old_data (from the db) = od
# new_data (from the parser) = nd

# to subsitute by the parsed file / parser
nd = pd.read_csv('war_loss.csv')

# We start checking in the following order:
# 1. Category
# 2. Types
# 3. Items

# ---------------------
# 1. Categories = cat
# ---------------------

# Get the list of all equipment categories currently in use
od_cat = pd.read_sql_query('select * from public.equipment_categories',con=engine)
# normalising the old data that is going to be used in the key: category bucket (c_type) and category name (c_eng_name)
od_cat['c_eng_name'] = od_cat['c_eng_name'].str.title()
od_cat['t_eng_name'] = od_cat['c_type'].str.title()
# creating key for the old data
od_cat['key'] = od_cat['c_eng_name'].str.lower()+od_cat['t_eng_name'].str.lower()
od_cat['key'] = od_cat['key'].str.replace('[^\d\w]','',regex=True)

# creating df for the parsed data
cat_upd = pd.DataFrame()
# normalising the new data
cat_upd['cat_name'] = nd['Equipment Category'].str.title()
# creating the column for category bucket
cat_upd['c_type'] = ''

# defining equipment category buckets

for i, row in cat_upd.iterrows():
    where = row['cat_name'].lower()
    if 'engineer' in where: 
        cat_upd.at[i,'c_type'] = 'Engineering'
    elif 'communication' in where or 'radar' in where or 'jammer' in where:
        cat_upd.at[i,'c_type'] = 'Communication'
    elif 'logistic' in where or 'truck' in where:
        cat_upd.at[i,'c_type'] = 'Logistics'
    elif 'medical' in where:
        cat_upd.at[i,'c_type'] = 'Medical'
    else: cat_upd.at[i,'c_type'] = 'Battle'

# creating key for the new data
cat_upd['key'] = cat_upd['cat_name'].str.lower()+cat_upd['c_type'].str.lower()
cat_upd['key'] = cat_upd['key'].str.replace('[^\d\w]','',regex=True)
# reconcile new vs old data
cat_upd = pd.merge(cat_upd,od_cat, how='left', on='key')
cat_upd.fillna('New', inplace=True)
cat_upd = cat_upd[cat_upd.c_eng_name == 'New']

# get only unique combinations or equipment category from the newly extracted file
cat_upd = cat_upd.groupby(['cat_name','c_type_x'],as_index=False).size()
    
if cat_upd.shape[0] > 0:
    # feed equipment_categories table w/ unique categories
    for index,row in cat_upd.iterrows():
        engine.execute("insert into public.equipment_categories(c_type,c_eng_name) values ('" + row.c_type_x + "','" + row.cat_name + "')")
    # report progress
print('######### Added ' + str(cat_upd.shape[0]) + ' items to the categories')

# ---------------------
# 2. Types = type
# ---------------------

# Get the list of all equipment types currently in use
od_type = pd.read_sql_query('select * from public.equipment_types_decoded',con=engine)
# normalising the old data that is going to be used in the key: category name (c_eng_name), category type name (t_eng_name) and country of origin name
od_type['category_l2_eng_encoded'] = od_type['category_l2_eng_encoded'].str.title()
od_type['series_number'] = od_type['series_number'].str.title()
od_type['country_of_origin_name'] = od_type['country_of_origin_name'].str.title()
# creating key for the old data
od_type['key'] = od_type['category_l2_eng_encoded'].str.lower()+od_type['series_number'].str.lower()+od_type['country_of_origin_name'].str.lower()
od_type['key'] = od_type['key'].str.replace('[^\d\w]','',regex=True)

# creating df for the parsed data
type_upd = pd.DataFrame()
# normalising the new data
type_upd['country_of_origin_name'] = nd['Equipment Producer'].str.title()
type_upd['category_l2_eng_encoded'] = nd['Equipment Category'].str.title()
type_upd['series_number'] = nd['Equipment Type'].str.title()

# ********** TO REMOVE - START

for i, row in type_upd.iterrows():
    where = row['country_of_origin_name']
    if 'Soviet Union' in where: 
        type_upd.at[i,'country_of_origin_name'] = 'USSR'
    elif 'Russia' in where: 
        type_upd.at[i,'country_of_origin_name'] = 'Russian Federation'
    elif 'Czech Republic' in where: 
        type_upd.at[i,'country_of_origin_name'] = 'Czechia'

# ********** TO REMOVE - END

# creating key for the new data
type_upd['key'] = type_upd['category_l2_eng_encoded'].str.lower()+type_upd['series_number'].str.lower()+type_upd['country_of_origin_name'].str.lower()
type_upd['key'] = type_upd['key'].str.replace('[^\d\w]','',regex=True)
# reconcile new vs old data
type_upd = pd.merge(type_upd,od_type, how='left', on='key')
type_upd.fillna('New', inplace=True)
# drop only those cases where the type does not exist in the old data
type_upd = type_upd[type_upd.series_number_y == 'New']

# get only unique combinations or equipment types from the newly extracted file
type_upd = type_upd.groupby(['category_l2_eng_encoded_x','series_number_x','country_of_origin_name_x'],as_index=False).size()

# Get the list of all equipment categories currently in use
countries = pd.read_sql_query('select * from public.countries_orgs',con=engine)
# source foreign key = country_of_origin_id
type_upd = pd.merge(type_upd,countries, how='left', left_on='country_of_origin_name_x',right_on='full_name')
# source foreign key = equipment_categories_id
type_upd = pd.merge(type_upd,od_cat, how='left', left_on='category_l2_eng_encoded_x',right_on='c_eng_name')

type_upd = type_upd[['id_y','series_number_x','id_x']]
type_upd = type_upd.rename(columns={'id_y': 'category_type_id', 'series_number_x': 'series_number','id_x':'country_of_origin_id'})

type_upd['series_number'] = type_upd['series_number'].str.replace('[\']','',regex=True)

if type_upd.shape[0] > 0:
    # feed equipment_categories table w/ unique categories
    for index,row in type_upd.iterrows():
        engine.execute("insert into public.equipment_types(category_type_id,series_number,country_of_origin_id) values (" + str(row.category_type_id) + ",'" + str(row.series_number) + "'," + str(row.country_of_origin_id) + ")")
    # report progress
print('######### Added ' + str(type_upd.shape[0]) + ' items to the types')

# ---------------------
# 3. Items = item
# ---------------------

# Get the list of all items currently reported in logs
od_item = pd.read_sql_query('select * from public.daily_losses_log_decoded',con=engine)

# normalising the old data that is going to be used in the key: link, category, type, and link
od_item['link'] = od_item['source_link'].str.title()
od_item['country'] = od_item['country_name'].str.title()
od_item['category'] = od_item['c_eng_name'].str.title()
od_item['type'] = od_item['series_number'].str.title()
# creating key for the old data
od_item['key'] = od_item['country'].str.lower()+od_item['category'].str.lower()+od_item['type'].str.lower()+od_item['link'].str.lower()
od_item['key'] = od_item['key'].str.replace('[^\d\w]','',regex=True)

# creating df for the parsed data
item_upd = pd.DataFrame()
# normalising the new data
item_upd['link'] = nd['Source Link']
item_upd['category'] = nd['Equipment Category'].str.title()
item_upd['type'] = nd['Equipment Type'].str.title()
item_upd['country'] = nd['Impacted Country']
item_upd['impact_type'] = nd['Action Type']

# ********** TO REMOVE - START

for i, row in item_upd.iterrows():
    where = row['country']
    if 'Soviet Union' in where: 
        item_upd.at[i,'country'] = 'USSR'
    elif 'Russia' in where: 
        item_upd.at[i,'country'] = 'Russian Federation'
    elif 'Czech Republic' in where: 
        item_upd.at[i,'country'] = 'Czechia'

# ********** TO REMOVE - END

# creating key for the new data
item_upd['key'] = item_upd['country'].str.lower()+item_upd['category'].str.lower()+item_upd['type'].str.lower()+item_upd['link'].str.lower()
item_upd['key'] = item_upd['key'].str.replace('[^\d\w]','',regex=True)

# reconcile new vs old data
item_upd = pd.merge(item_upd,od_item, how='left', on='key')
item_upd.fillna('New', inplace=True)
# drop only those cases where the item log does not exist in the old data
item_upd = item_upd[item_upd.link_y == 'New']

# reduce columns
item_upd = item_upd[['country_x','category_x','type_x','link_x','impact_type_x']]
item_upd = item_upd.rename(columns={'country_x': 'country', 'category_x': 'category','type_x':'series_number','link_x':'link','impact_type_x':'impact_type'})

# source foreign key = country_of_origin_id (-> id)
item_upd = pd.merge(item_upd,countries, how='left', left_on='country',right_on='full_name')
item_upd = item_upd.rename(columns={'id': 'country_id'})
# ----------
# conflict id - find a way to automate in the future?
item_upd['conflict_id'] = 1
# ----------

# source_name
item_upd['source_name'] = 'Oryx'
# ----------

# date
item_upd['date_'] = '2022-02-24'
# ----------

# reduce cols
item_upd = item_upd[['conflict_id','country_id','impact_type','category','series_number','source_name','link','date_']]

# source category data
item_upd = pd.merge(item_upd,od_cat, how='left', left_on='category',right_on='c_eng_name')
item_upd = item_upd.rename(columns={'id': 'category_id'})

# Get the list of all equipment types currently in use
curr_type = pd.read_sql_query('select * from public.equipment_types',con=engine)

# clean series number from single quotes
item_upd['series_number'] = item_upd['series_number'].str.replace('[\']','',regex=True)

# source type data
item_upd = pd.merge(item_upd,curr_type, how='left', left_on='series_number',right_on='series_number')
item_upd = item_upd.rename(columns={'id': 'series_number_id'})

# clean impact type from comma
item_upd['impact_type'] = item_upd['impact_type'].str.replace('[,]','',regex=True)

if item_upd.shape[0] > 0:
    # feed equipment_categories table w/ unique categories
    for index,row in item_upd.iterrows():
        engine.execute("insert into public.daily_losses_log(conflict_id, impacted_side_id, impact_type, equipment_category, equipment_type, source_name, source_link, date) values (" + str(row.conflict_id) + "," + str(row.country_id) + ",'" + row.impact_type + "'," + str(row.category_id) + "," + str(row.series_number_id) + ",'" + row.source_name + "','" + row.link + "','" + row.date_ + "')")
    # report progress
print('######### Added ' + str(type_upd.shape[0]) + ' items to the items')

