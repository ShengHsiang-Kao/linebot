from keras.models import load_model
import pandas as pd
import numpy as np
from gensim.models.keyedvectors import KeyedVectors
import jieba
from gensim.test.utils import datapath
# 引用Web Server套件
from flask import Flask, request, abort
# 從linebot 套件包裡引用 LineBotApi 與 WebhookHandler 類別
from linebot import (
    LineBotApi, WebhookHandler, WebhookParser
)
# 引用無效簽章錯誤
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)
# 載入json處理套件
import json
# 將消息模型，文字收取消息與文字寄發消息 引入
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage, StickerSendMessage, TemplateSendMessage
)

#引入按鍵模板
from linebot.models.template import(
    ButtonsTemplate
)
# 載入基礎設定檔
secretFileContentJson=json.load(open("./line_secret_key",'r',encoding="utf-8"))
server_url=secretFileContentJson.get("server_url")

# 設定Server啟用細節
app = Flask(__name__,static_url_path = "/images" , static_folder = "./images/")

# 生成實體物件
line_bot_api = LineBotApi(secretFileContentJson.get("channel_access_token"))
handler = WebhookHandler(secretFileContentJson.get("secret_key"))

# 啟動server對外接口，使Line能丟消息進來
@app.route("/", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except LineBotApiError:
        return HttpResponseBadRequest()
    return 'OK'

def inputs(list_1):
    for n,i in enumerate(list_1):
        try:
            list_1[n]=int(i)
        except:
            list_1[n]=0
    mean = [26.9859331, 30.2746547, 0.467701106, 741277.863,0.582340575, 2.10021023]
    std = [4.61549746, 47.8120109, 0.807741531, 1397767.31,0.493173428, 0.626818273]
    userdf = pd.DataFrame(columns=["age","serveTime","Loan","SalPerY","holdCard","Career"])
    userdf.loc[0] = list_1
    userdf -= mean
    userdf /= std
    model = load_model('predict.h5')
    preds = model.predict(userdf)
#     print(preds)
    #print(max(preds))
    pp=np.argmax(preds)
#     print(preds.item(np.argmax(preds)))
    list_2=['2萬~4.5萬','4.5萬~9.5萬','9.5萬~19.5萬','19.5萬~29.5萬','29.5萬以上']
    return str(list_2[pp])

def managePredict(event, mtext):  #處理LIFF傳回的FORM資料
    flist = mtext[3:].split('/')  #去除前三個「#」字元再分解字串
    flist[1]=str(int(flist[1])*12+int(flist[2]))
    flist[4]=str(int(flist[4])*10000)
    item1 = int(flist[0])  #取得輸入資料
    item2 = int(flist[1])
    item3 = int(flist[3])
    item4 = int(flist[4])
    item5 = int(flist[5])
    item6 = int(flist[6])
#     text1 = "您輸入的資料如下："
#     text1 += "\n年齡："+ flist[0]
#     text1 += "\n年資："+ flist[1] +"個月"
#     text1 += "\n年薪："+ flist[4] +"元"
#     text1 += "\n職業："+ flist[6]
#     text1 += "\n有無貸款："+ flist[3]
#     text1 += "\n有無持卡："+ flist[5]
    list_1=[item1, item2, item3, item4, item5, item6]
    quota=inputs(list_1)
    text1 = "您的預估額度為："+ quota
    try:
        message = TextSendMessage(  #顯示資料
            text = text1
        )
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))


# 0.撈出存在excel的向量轉為matrix
def get_article_matrix(article, i):
    aa = article.loc[:, ["article_vector_matrix"]][i:i + 1]
    # 轉ARRAY再轉list
    b = np.array(aa)
    b = b[0].tolist()  # list
    # 切
    c = str(b[0]).split(',')
    article_matrix = np.mat(c).astype(float)
    return (article_matrix)


# 1.載入檔案
article = pd.read_excel(r"./article_news_vector _final.xlsx")
articles_matrix = [get_article_matrix(article, i) for i in range(5000)]

# 2.載入bin檔
wv_from_bin = KeyedVectors.load_word2vec_format(
    datapath(r'./100win20min_count3cbow1.bin'),
    binary=True)


# 3.輸入文字
def please_input_words(rlist):
    # 斷詞
    wordlist = jieba.lcut(rlist, cut_all=False)
    print(wordlist)
    input_vector_matrix = get_article_avgvector(wordlist)
    print()
    print("這幾個字的平均向量是:")
    print(input_vector_matrix)
    return (input_vector_matrix)


# 4.獲取輸入詞的平均向量
def get_article_avgvector(wordlist):
    # 取每篇文章平均向量
    # x=np.matrix(wv_from_bin[word])安安?
    len_wordlist = 0
    input_avgvector_matrix = 0

    for word in wordlist:
        try:
            x = np.matrix(wv_from_bin[word])
            input_avgvector_matrix += x
            len_wordlist += 1
        except:
            pass

    if type(input_avgvector_matrix) == int:
        input_avgvector_matrix = np.matrix(wv_from_bin['購物'])
    else:
        input_avgvector_matrix = input_avgvector_matrix / len_wordlist

    return (input_avgvector_matrix)


# 5.餘弦相似度
def cos_similar(vector_a, vector_b):
    """
    计算两个向量之间的余弦相似度
    :param vector_a: 向量 a
    :param vector_b: 向量 b
    :return: sim
    """
    vector_a = np.mat(vector_a)
    vector_b = np.mat(vector_b)
    num = float(vector_a * vector_b.T)
    denom = np.linalg.norm(vector_a) * np.linalg.norm(vector_b)
    cos = num / denom
    similar = 0.5 + 0.5 * cos
    return similar


# 測試開始_餘弦相似度
def manageRecommend(event, mtext):
    rlist = mtext[1:]
    input_vector_matrix = please_input_words(rlist)
    most_similar_article = 餘弦相似度找文章(rlist, input_vector_matrix)
    text_1 = str(most_similar_article)
    try:
        message = TextSendMessage(  # 顯示資料
            text=text_1
        )
        line_bot_api.reply_message(event.reply_token, message)
    except:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text='發生錯誤！'))

    # 比對


def 餘弦相似度找文章(rlist, input_vector_matrix):
    articles_matrix_list = []
    for b in range(5000):
        result = cos_similar(input_vector_matrix, articles_matrix[b])
        articles_matrix_list.append(result)
    print("第", articles_matrix_list.index(max(articles_matrix_list)), "篇新聞最相似")
    most_similar = articles_matrix_list.index(max(articles_matrix_list))
    most_similar_article = np.array(article[most_similar:most_similar + 1]['content'])[0]
    print("文章內文為:", "\n", "\n", "------------------------------------------------------------", "\n",
          np.array(article[most_similar:most_similar + 1]['content'])[0])
    return most_similar_article

# 消息清單
reply_message_list = [
TextSendMessage(text="關注信我卡來，找到適合你的卡片。"),
    TextSendMessage(text="哈囉！😊歡迎加入信我卡來，我們提供關於信用卡💳的各種資訊，歡迎點擊您有興趣的功能喔！😄"),
    ImageSendMessage(original_content_url='https://%s/images/card.jpg' %server_url ,
    preview_image_url='https://%s/images/card-to-woman.jpg' %server_url),
    ImageSendMessage(original_content_url='https://%s/images/card_hand.jpg' %server_url,
    preview_image_url='https://%s/images/credit-card.jpg' %server_url)
]

# 預測額度流程
reply_message_list_predict = [
TextSendMessage(text="想知道您的核卡額度？🤔輸入下列訊息，我們就會幫您預測喔！😉"),
    TemplateSendMessage(
     alt_text='Buttons template',
      template=ButtonsTemplate(
      title='信用卡核卡額度',
    text='輸入訊息，開始預測',
    actions=[
      {
        "type": "uri",
        "label": "開始預測",
        "uri": "line://app/1653471513-2vnJK4EJ"
      }
    ],
  )
  )
]

# 新聞推薦流程
reply_message_list_news = [
TextSendMessage(text="您想知道哪一類的信用卡相關資訊呢？點選下方按鈕或是輸入@加上您感興趣的內容，例如:@我想知道2020最強神卡，我們就會提供相關訊息給您🙂"),
]

# 卡片推薦流程
reply_message_list_recommend = [
TextSendMessage(text="不知道哪張信用卡適合自己嗎？😥讓我們來幫你挑選適合您的卡片吧！🤗"),
    TemplateSendMessage(
     alt_text='Buttons template',
      template=ButtonsTemplate(
      thumbnailImageUrl='https://%s/images/debit-card.png',
        title='持卡狀況',
        text='您是初次辦卡？還是已經有信用卡了呢？',
    actions=[
      {
        "type": "uri",
        "label": "已持有信用卡",
        "uri": "18.192.172.180:5002/card"
      },
      {
        "type": "uri",
        "label": "初次辦卡小白",
        "uri": "18.192.172.180:5002"
      }
    ],
  )
  )
]

'''

設計一個字典
    當用戶輸入相應文字消息時，系統會從此挑揀消息

'''

# 根據自定義菜單四張故事線的圖，設定相對應訊息
template_message_dict = {
    "[::text:]請幫我預測核卡額度":reply_message_list_predict,
    "[::text:]請給我信用卡相關新聞":reply_message_list_news,
    "[::text:]請幫我推薦信用卡":reply_message_list_recommend,
}

'''

當用戶發出文字消息時，判斷文字內容是否包含[::text:]，
    若有，則從template_message_dict 內找出相關訊息
    若無，則回傳預設訊息。

'''

# 用戶發出文字消息時， 按條件內容, 回傳文字消息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if(event.message.text.find('::text:')!= -1):
#         print(event.message.text)
        line_bot_api.reply_message(
        event.reply_token,
        template_message_dict.get(event.message.text)
        )
    elif event.message.text.find('###')!= -1 and len(event.message.text) > 3:
        managePredict(event, event.message.text)
    elif event.message.text.find('@')!= -1 and len(event.message.text) > 2:
        manageRecommend(event, event.message.text)


'''

撰寫用戶關注時，我們要處理的商業邏輯
1. 取得用戶個資，並存回伺服器
2. 把先前製作好的自定義菜單，與用戶做綁定
3. 回應用戶，歡迎用的文字消息與圖片消息

'''

# 載入Follow事件
from linebot.models.events import (
    FollowEvent
)

# 載入requests套件
import requests


# 告知handler，如果收到FollowEvent，則做下面的方法處理
@handler.add(FollowEvent)
def reply_text_and_get_user_profile(event):
    # 取出消息內User的資料
    user_profile = line_bot_api.get_profile(event.source.user_id)

    # 將用戶資訊存在檔案內
    with open("./users.txt", "a") as myfile:
        myfile.write(json.dumps(vars(user_profile), sort_keys=True))
        myfile.write('\r\n')

        # 將菜單綁定在用戶身上
    linkRichMenuId = secretFileContentJson.get("rich_menu_id")
    linkResult = line_bot_api.link_rich_menu_to_user(secretFileContentJson["self_user_id"], linkRichMenuId)

    # 回覆文字消息與圖片消息
    line_bot_api.reply_message(
        event.reply_token,
        reply_message_list
    )

'''

執行此句，啟動Server，觀察後，按左上方塊，停用Server

'''

if __name__ == "__main__":
    app.run(host='0.0.0.0', threaded=False)