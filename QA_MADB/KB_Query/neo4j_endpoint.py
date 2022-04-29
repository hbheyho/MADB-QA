# encoding=utf-8

"""

@author: HB

@file: neo4j_endpoint.py

@time: 2022/04/28 14:49

@desc: neo4j连接并结果解析

"""

from collections import OrderedDict
from py2neo import Graph, Node, NodeMatcher, Relationship, RelationshipMatcher


class Neo4j:
    # 连接初始化
    def __init__(self, endpoint_url='http://localhost:7474/browser'):
        self.neo4j_con = Graph(endpoint_url, auth=("neo4j", "123456789"))
        self.propertiesDict = ['corpCode']

    def get_cypher_result(self, query):
        """
        进行neo4j查询
        :param query:
        :return: cursor
        """
        cursor = self.neo4j_con.run(query)
        return cursor

    @staticmethod
    def parse_result(query_result):
        """
        解析返回的结果
        :param query_result:
        :return:
        """
        try:
            # 结果形式为{'head': {'vars': ['x', 'n']},
            # 'results': {'bindings': [{'x': {'type': 'uri', 'value': 'xxx'},'n': {'type': 'literal', 'value': 'xx'}}]}
            query_head = query_result['head']['vars']
            query_results = list()
            for r in query_result['results']['bindings']:
                temp_dict = OrderedDict()
                for h in query_head:
                    temp_dict[h] = r[h]['value']
                query_results.append(temp_dict)
            return query_head, query_results
        except KeyError:
            return None, query_result['boolean']

    def print_result_to_string(self, query_result):
        """
        直接打印结果，用于测试
        :param query_result:
        :return:
        """
        query_head, query_result = self.parse_result(query_result)

        if query_head is None:
            if query_result is True:
                print('Yes')
            else:
                print('False')
        else:
            for h in query_head:
                print(h, ' ' * 5, end="")
            print()
            for qr in query_result:
                for _, value in qr.items():
                    print(value, ' ', end="")
                print()

    def get_cypher_result_value(self, cursor):
        """
        用列表存储结果的值
        :param : string
        :return: List[dict]
        """
        # results = list()

        # while cursor.forward():
        #     # 将Node类型的结果转换为dict
        #     for key in cursor.current.keys():
        #         results.append((cursor.current[key]))
        results = list()
        while cursor.forward():
            # 结果转换为dict, key/value => "地址"/"广州市巴拉巴拉"
            result = dict()
            for key in cursor.current.keys():
                result[key] = cursor.current[key]
            results.append(result)
        return results


# TODO 用于测试
if __name__ == '__main__':
    neo4j = Neo4j()
    query = """
        MATCH (c:Corporation) 
        RETURN c.corpName as 企业名称, c.linkMan as 联系人, c.linkMobile as 联系方式,
        c.email as 邮箱, c.postCode as 邮编, c.fax as 传真, c.address as 地址
        """
    cursor = neo4j.get_cypher_result(query)
    results = neo4j.get_cypher_result_value(cursor)
    for result in results:
        print(result)