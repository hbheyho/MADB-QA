# encoding=utf-8

"""

@author: SimmerChan

@contact: hsl7698590@gmail.com

@file: query_main.py

@time: 2017/12/20 15:29

@desc:main函数，整合整个处理流程。

"""
from QA_MADB.KB_Query import neo4j_endpoint, question2cypher

from py2neo import Graph, Node, NodeMatcher, Relationship, RelationshipMatcher
import os

file_path = os.path.split(os.path.realpath(__file__))[0]


class QAInterface:
    def __init__(self):
        # TODO 连接neo4j服务器
        self.neo4j = neo4j_endpoint.Neo4j()

        # TODO 初始化自然语言到Cypher查询的模块，参数是外部词典列表, 并初始化规则模板
        self.q2c = question2cypher.Question2Sparql([os.path.join(file_path, 'external_dict', 'part.txt'),
                                                    os.path.join(file_path, 'external_dict', 'corporation.txt'),
                                                    os.path.join(file_path, 'external_dict', 'vehicle.txt')])


        # # TODO 连接Fuseki服务器。
        # self.fuseki = jena_sparql_endpoint.JenaFuseki()
        # # TODO 初始化自然语言到SPARQL查询的模块，参数是外部词典列表。
        # self.q2s = question2sparql.Question2Sparql([os.path.join(file_path, 'external_dict', 'movie_title.txt'),
        #                                             os.path.join(file_path, 'external_dict', 'person_name.txt')])

    def answer(self, question: str):
        # 进行语义解析, 得到SPARQL语句
        # my_query = self.q2s.get_sparql(question)

        # 进行语义解析, 得到Cypher语句
        my_query = self.q2c.get_cypher(question)

        # 最后选取的cypher语句
        print(my_query)

        if my_query is not None:
            cursor = self.neo4j.get_cypher_result(my_query)
            value = self.neo4j.get_cypher_result_value(cursor)

            # TODO 判断结果是否是布尔值，是布尔值则提问类型是"ASK"，回答“是”或者“不知道”。
            if isinstance(value, bool):
                if value is True:
                    ans = "是的"
                else:
                    ans = "我还不知道这个问题的答案"
            else:
                # TODO 查询结果为空，根据OWA，回答“不知道”
                if len(value) == 0:
                    ans = "我还不知道这个问题的答案"
                # 对单个结果进行处理
                elif len(value) == 1:
                    output = ''
                    if isinstance(value[0], dict):
                        for k, v in value[0].items():
                            output += k + ":" + str(v) + u'、'
                    else:
                        output = value[0] + u'、'
                    ans = output[0:-1]
                else:
                    ans = ''
                    # 遍历每个dict, 生成结果
                    for v in value:
                        output = ''
                        for label, content in v.items():
                            output += label + ":" + str(content) + u'、'
                        output = output[0:-1]
                        ans += output + u'\n'
        else:
            # TODO 自然语言问题无法匹配到已有的正则模板上，回答“无法理解”
            ans = "我不知道你表达的意思"

        return ans


if __name__ == '__main__':
    qa_interface = QAInterface()
    while True:
        question = input(">> 请输入问题：")
        ans = qa_interface.answer(question)
        print(ans)
        print('#' * 100)
