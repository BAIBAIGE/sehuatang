# 连接mongodb

import pymongo
from config import get_config

host = get_config("db_host")
port = get_config("db_port")
date = get_config("date").strftime("%Y-%m-%d")


client = pymongo.MongoClient(host, port)
db = client.sehuatang

# 枚举，通过fid获取板块名称
def get_plate_name(fid):
    if fid == 103:
        return "hd_chinese_subtitles"
    elif fid == 104:
        return "vegan_with_mosaic"
    elif fid == 37:
        return "asia_mosaic_originate"
    else:
        return "test"


# 保存数据(已存在的数据不保存)
def save_data(data_list, fid):
    """
    :param data: 字典
    """
    collection_name = get_plate_name(fid)
    collection = db[collection_name]
    tid_list = find_data_tid(collection_name, date)
    data_list_new = compare_data(data_list, tid_list)
    collection.insert_many(data_list_new)


# 查询数据, 拿到已存在的数据id
def find_data_tid(collection_name, date):
    """
    :param data: 字典
    """
    collection = db[collection_name]
    # 构造查询条件
    query = {"post_time": {"$regex": "^" + date}}
    # 查询数据, 返回指定的字段
    res = collection.find(query, {"_id": 0, "date": 1, "tid": 1})
    # 将查询结果中的id提取出来
    tid_list = []
    for i in res:
        tid_list.append(i["tid"])
    return tid_list


# 比对tid，将不存在的信息筛选出来
def compare_data(data_list, id_list):
    """
    :param data: 字典
    """
    data_list_new = []
    for i in data_list:
        if i["tid"] not in id_list:
            data_list_new.append(i)
    return data_list_new


# res = find_data_tid("zhongwen666", "2022-03-31")
# print(res)
# print(len(res))