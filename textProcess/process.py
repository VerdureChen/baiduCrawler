import jieba
import jieba.posseg as pseg
from gensim import corpora, models
import re

class textPro:
    def __init__(self):
        jieba.enable_paddle()

    def cut_sent(self, para):
        para = re.sub('([。！？\?])([^”’])', r"\1\n\2", para)  # 单字符断句符
        para = re.sub('(\.{6})([^”’])', r"\1\n\2", para)  # 英文省略号
        para = re.sub('(\…{2})([^”’])', r"\1\n\2", para)  # 中文省略号
        para = re.sub('([。！？\?][”’])([^，。！？\?])', r'\1\n\2', para)
        # 如果双引号前有终止符，那么双引号才是句子的终点，把分句符\n放到双引号后，注意前面的几句都小心保留了双引号
        para = para.rstrip()  # 段尾如果有多余的\n就去掉它
        # 很多规则中会考虑分号;，但是这里我把它忽略不计，破折号、英文双引号等同样忽略，需要的再做些简单调整即可。
        return para.split("\n")

    def word_split(self, txt):
        seg_list = []
        for txts in self.cut_sent(txt):
            seg = jieba.lcut(txts, cut_all=False)
            seg_list.append('/'.join(seg))
        #print("Default Mode: " + "/ ".join(seg_list))  # 精确模式
        return seg_list

    def word_split2(self, txt):
        seg_list = []

        seg = jieba.lcut(txt, cut_all=False)

        #print("Default Mode: " + "/ ".join(seg_list))  # 精确模式
        return seg

    def POS(self, txt):
        pos_list = []
        for txts in self.cut_sent(txt):
            words = pseg.cut(txts, use_paddle=True)  # paddle模式
            combine = []
            for word, flag in words:
                combine.append('%s/%s' % (word, flag))
            pos_list.append('  '.join(combine))
        return  pos_list

    def getStopwords(self):
        f = open('stops.txt', 'r', encoding='utf-8')
        words = f.readlines()
        stopwords = []
        for word in words:
            stopwords.append(word.strip())

        return stopwords
    def LDA(self, txts):
        '''
        对传入文本进行LDA提取关键词
        :param txts: [txt1, txt2, txt3...]
        :return:
        '''
        stopwords = self.getStopwords()
        #print(stopwords)
        word_lists = []
        for text in txts:
            word_list = [word for word in self.word_split2(text) if word not in stopwords]
            word_lists.append(word_list)
        # 构造词典
        dictionary = corpora.Dictionary(word_lists)
        # 基于词典，使【词】→【稀疏向量】，并将向量放入列表，形成【稀疏向量集】
        corpus = [dictionary.doc2bow(words) for words in word_lists]
        # lda模型，num_topics设置主题的个数
        lda = models.ldamodel.LdaModel(corpus=corpus, id2word=dictionary, num_topics=2, passes=200)
        # 打印所有主题，每个主题显示5个词
        for topic in lda.print_topics(num_words=5):
            print(topic)
        #print(lda.show_topics())
        # 主题推断
        print(lda.inference(corpus)[0])






if __name__ == '__main__':
    processer = textPro()
    processer.word_split('今天吃了毛血旺。')
    processer.POS('今天中午没睡觉。')
    txts = [
        '美国教练这会儿坦言，没输给中国女排，是输给了郎平',
        '美国无缘四强，听听主教练的评价',
        '中国女排晋级世锦赛四强，全面解析主教练郎平的执教艺术',
        '为什么越来越多的人买MPV，而放弃SUV？跑一趟长途就知道了',
        '跑了长途才知道，SUV和轿车之间的差距',
        '家用的轿车买什么好']

    processer.LDA(txts)