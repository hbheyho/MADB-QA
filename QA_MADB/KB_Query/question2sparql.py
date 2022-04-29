# encoding=utf-8

"""

@author: SimmerChan

@contact: hsl7698590@gmail.com

@file: question2sparql.py

@time: 2017/12/20 15:29

@desc: 将自然语言转为SPARQL查询语句

"""
from QA_MADB.KB_Query import question_temp, word_tagging


class Question2Sparql:
    def __init__(self, dict_paths):
        # 加载外部词典
        self.tw = word_tagging.Tagger(dict_paths)
        # 加载规则模板
        self.rules = question_temp.rules

    def get_sparql(self, question):
        """
        进行语义解析，找到匹配的模板，返回对应的SPARQL查询语句
        :param question:
        :return:
        """
        # 对属于的进行分词与词性标注
        word_objects = self.tw.get_word_objects(question)
        # 保存所有可能的SPARQL语句
        queries_dict = dict()

        # 依次进行模板匹配
        for rule in self.rules:
            query, num = rule.apply(word_objects)

            if query is not None:
                queries_dict[num] = query

        if len(queries_dict) == 0:
            return None
        elif len(queries_dict) == 1:
            return list(queries_dict.values())[0]
        else:
            # TODO 匹配多个语句，以匹配关键词最多的句子作为返回结果
            sorted_dict = sorted(queries_dict.items(), key=lambda item: item[0], reverse=True)
            return sorted_dict[0][1]
