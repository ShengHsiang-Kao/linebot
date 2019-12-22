from flask import Flask, request, make_response, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_script import  Manager,Server
from flask_moment import Moment
from datetime import datetime, timedelta
import uuid, json
import pymongo,time
import pandas as pd
from confluent_kafka import Producer

app = Flask(__name__)
manager = Manager(app)
def error_cb(err):
    print('Error: %s' % err)

@app.route('/')
def index():
    if 'id' in request.cookies:
        id = request.cookies.get('id')
        return render_template('card2.html',id=id)
    else:
        uid = str(uuid.uuid1())
        resp = make_response(render_template('card2.html'))
        resp.set_cookie('id', uid, max_age=99999)
        id = request.cookies.get('id')
        return resp
@app.route('/card')
def yocard():
    if 'id' in request.cookies:
        id = request.cookies.get('id')
        client = pymongo.MongoClient(host='123.241.175.34', port=27017)
        client.admin.authenticate('root', '1qaz@WSX3edc')
        db = client.Recommend_card
        coll = db.hold_card_list
        mondata = list(coll.find())
        client.close()
        card = pd.DataFrame(mondata)
        result = card["卡名"].tolist()
        bank = []
        card = []
        for i in result:
            bank.append(i.split("-")[0])
            card.append(i.split("-")[1])
        bankset = list(set(bank))
        bankset.sort(key=bank.index)
        return render_template('card4.html', result=result, bank=bank, card=card, bankset=bankset)
    else:
        uid = str(uuid.uuid1())
        client = pymongo.MongoClient(host='123.241.175.34', port=27017)
        client.admin.authenticate('root', '1qaz@WSX3edc')
        db = client.Recommend_card
        coll = db.hold_card_list
        mondata = list(coll.find())
        client.close()
        card = pd.DataFrame(mondata)
        result = card["卡名"].tolist()
        bank = []
        card = []
        for i in result:
            bank.append(i.split("-")[0])
            card.append(i.split("-")[1])
        bankset = list(set(bank))
        bankset.sort(key=bank.index)
        resp = make_response(render_template('card4.html',result=result,bank=bank,card=card,bankset=bankset))
        resp.set_cookie('id', uid, max_age=120)
        id = request.cookies.get('id')
        return resp

@app.route('/havecard', methods=['POST'])
def havecard():
    if request.method == 'POST':
        id = request.cookies.get('id')
        carddata = request.form.getlist('cardname')
        card = {}
        card.update({"id": id})
        for n,i in enumerate(carddata):
            card.update({"card{}".format(n) : i})
        usrcard = json.dumps(card,ensure_ascii=False)
        print(usrcard)
        producer = Producer({'bootstrap.servers': 'kafka:9092','error_cb': error_cb})
        topicName = 'havecard'
        producer.produce(topicName, usrcard, 'test')
        producer.flush()
        return render_template('wating.html',id=id)

@app.route('/nocard', methods=['POST'])
def nocard():
    if request.method == 'POST':
        id = request.cookies.get('id')
        rating1 = str(request.form['卡活動'])
        rating2 = str(request.form['超商'])
        rating3 = str(request.form['交通'])
        rating4 = str(request.form['保險'])
        rating5 = str(request.form['加油'])
        rating6 = str(request.form['電影'])
        rating7 = str(request.form['旅遊機票飯店'])
        rating8 = str(request.form['行動支付'])
        rating9 = str(request.form['網購'])
        rating10 = str(request.form['繳稅繳費'])
        rating11 = str(request.form['現金回饋'])
        t = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
        usrdict = json.dumps({"id":id,"time":t,"卡活動":rating1 ,"超商":rating2,"交通":rating3,"保險":rating4,"加油":rating5,"電影":rating6,"旅遊機票飯店":rating7,"行動支付":rating8,"網購":rating9,"繳稅繳費":rating10,"現金回饋":rating11},ensure_ascii=False)
        producer = Producer({'bootstrap.servers': 'kafka:9092','error_cb': error_cb})
        topicName = 'nocard'
        producer.produce(topicName,usrdict,'test')
        producer.flush()
        return render_template('wating.html',id=id)

@app.route('/result/<id>')
def result(id):
    if 'id' in request.cookies:
        client = pymongo.MongoClient(host='123.241.175.34', port=27017)
        client.admin.authenticate('root', '1qaz@WSX3edc')
        db = client.Recommend_card
        coll = db.no_card_result
        coll2 = db.cardWdata
        result = list(coll.find({"id": id}).sort('_id',-1).limit(1))
        A = result[0]["card1"]
        B = result[0]["card2"]
        C = result[0]["card3"]
        D = result[0]["card4"]
        E = result[0]["card5"]
        card1 = list(coll2.find({"卡名02": A}))[0]
        del card1["_id"];del card1["熱度排名"]
        card2 = list(coll2.find({"卡名02": B}))[0]
        del card2["_id"];del card2["熱度排名"]
        card3 = list(coll2.find({"卡名02": C}))[0]
        del card3["_id"];del card3["熱度排名"]
        card4 = list(coll2.find({"卡名02": D}))[0]
        del card4["_id"];del card4["熱度排名"]
        card5 = list(coll2.find({"卡名02": E}))[0]
        del card5["_id"];del card5["熱度排名"]
        client.close()
        return render_template('result.html',id=id,card1=card1,card2=card2,card3=card3,card4=card4,card5=card5)


if __name__ == "__main__":
    #app.run()
    manager.add_command("runserver", Server(host='0.0.0.0', port='5002', threaded=True))
    manager.run()