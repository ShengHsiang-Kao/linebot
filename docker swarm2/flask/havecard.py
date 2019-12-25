import pandas as pd
import json
import re
import pymongo
import jieba
import operator
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import uuid
from confluent_kafka import Consumer

client = pymongo.MongoClient(host='123.241.175.34', port=27017)
client.admin.authenticate('root', '1qaz@WSX3edc')
db = client.Recommend_card
coll = db.hold_card
user_card_matrix_for_rec=coll.find()
df=pd.DataFrame(list(user_card_matrix_for_rec))
del df['_id']
def CF_Recommend_Item_Based(my_card):
    df_T=df.T
    card_sim=cosine_similarity(df_T,df_T)
    indices = pd.Series(df_T.index)   #所有卡series
    card_index_list=[indices[indices == name].index[0] for name in my_card]  #找出各卡index
    weighted_card_rec=np.zeros(len(df_T.index))   #創全0且為卡片數量長度的array
    for  i in card_index_list:
        weighted_card_rec +=card_sim[i]           #將持有卡於其他卡的相似度相加成推薦權重
    weighted_score=pd.Series(weighted_card_rec).sort_values(ascending = False)
    top_5_indexes=weighted_score.iloc[len(my_card):len(my_card)+5].index
    rec_card=[]
    for i in top_5_indexes:
        rec_card.append(indices[i])
    result = {"id":id,"card1":rec_card[0],"card2":rec_card[1],"card3":rec_card[2],"card4":rec_card[3],"card5":rec_card[4]}
    print(result)
    coll2 = db.no_card_result
    coll2.insert_one(result)
    client.close()
props = {'bootstrap.servers': 'kafka:9092','group.id': 'test3','auto.offset.reset': 'earliest','session.timeout.ms': 6000}
consumer = Consumer(props)
topicName = "havecard"
consumer.subscribe([topicName])
while True:
    records = consumer.consume()
    if records is None:
        continue
    else:
        for record in records:
            msgKey = record.key().decode('utf-8')
            msgValue = record.value().decode('utf-8')
            data = eval(msgValue)
            id = data["id"]
            del data["id"]
            my_card = []
            for i,y in data.items():
                my_card.append(y)
            CF_Recommend_Item_Based(my_card)