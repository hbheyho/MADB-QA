# encoding=utf-8

"""

@author: HB

@file: question_temp.py

@time: 2022/04/25 15:30

@desc:
设置问题模板，为每个模板设置对应的Cypher语句。demo提供如下模板：


读者可以自己定义其他的匹配规则。
"""
from refo import finditer, Predicate, Star, Any, Disjunction
import re

# TODO SPARQL前缀和模板
SPARQL_PREXIX = u"""
PREFIX : <http://www.kgdemo.com#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""


# TODO Cypher模板 - 查询供应商/配件详情
Cypher_SELECT_DETAIL = u"""
    MATCH {select} WHERE {condition} 
    {withCondition}
    RETURN {result} 
"""


# TODO Cypher前缀和模板
Cypher_SELECT_TEM = u"""
    MATCH {select} WHERE {condition} RETURN {result} as record
"""

# 搜索模板
SPARQL_SELECT_TEM = u"{prefix}\n" + \
                    u"SELECT DISTINCT {select} WHERE {{\n" + \
                    u"{expression}\n" + \
                    u"}}\n"

# 计数模板
SPARQL_COUNT_TEM = u"{prefix}\n" + \
                   u"SELECT COUNT({select}) WHERE {{\n" + \
                   u"{expression}\n" + \
                   u"}}\n"

# 询问模板
# ASK 用于测试知识图谱中是否存在满足给定条件的数据，若存在则返回  “True” ，否则返回 ”False” ，注意不会返回具体的匹配数据
SPARQL_ASK_TEM = u"{prefix}\n" + \
                 u"ASK {{\n" + \
                 u"{expression}\n" + \
                 u"}}\n"


class W(Predicate):
    # token == none, token=".*", 否则为token等于传参
    def __init__(self, token=".*", pos=".*"):
        # re.compile()生成的是正则对象，单独使用没有任何意义，需要和findall(),
        # search(), match(）搭配使用
        self.token = re.compile(token + "$")
        self.pos = re.compile(pos + "$")
        super(W, self).__init__(self.match)

    # 判断文本和词性是否同时满足
    def match(self, word):
        """ 采用正则表达式同时匹配对象（word）的字符（token）和词性（pos） """
        m1 = self.token.match(word.token)
        m2 = self.pos.match(word.pos)
        return m1 and m2


# 普通规则
class Rule(object):
    def __init__(self, condition_num, condition=None, action=None):
        assert condition and action
        self.condition = condition
        self.action = action
        self.condition_num = condition_num

    def apply(self, sentence):
        matches = []
        # 首先进行匹配操作，然后将匹配结果传入对应的操作函数中
        # 函数 finditer() 返回所有匹配的一个迭代器
        # 判断sentence是否满足匹配规则condition
        for m in finditer(self.condition, sentence):
            i, j = m.span()
            matches.extend(sentence[i:j])

        # 执行所传过来具体的action
        return self.action(matches), self.condition_num


# 关键字规则
class KeywordRule(object):
    def __init__(self, condition=None, action=None):
        assert condition and action
        self.condition = condition
        self.action = action

    def apply(self, sentence):
        matches = []
        for m in finditer(self.condition, sentence):
            i, j = m.span()
            matches.extend(sentence[i:j])
        if len(matches) == 0:
            return None
        else:
            return self.action()


# 问题集合 => action
class QuestionSet:
    def __init__(self):
        pass

    @staticmethod
    def query_corporation_basic(word_objects):
        """
        查询企业的详情信息
        :param word_objects:
        :return:
        """
        # 返回结果的keyWord构建
        result = None
        for r in corp_basic_keyword_rules:
            result = r.apply(word_objects)
            if result is not None:
                break

        select = u"(c:Corporation)"
        cypher = None
        for w in word_objects:
            if w.pos == pos_corp:
                condition = u"c.corpName = '{name}'".format(name=w.token)
            # 进行模板渲染, 生产Cypher语句
            cypher = Cypher_SELECT_DETAIL.format(select=select,
                                                 condition=condition,
                                                 withCondition='',
                                                 result=result)
            break
        return cypher

    @staticmethod
    def query_part_basic(word_objects):
        """
        配件A的基础信息 - 例如配件规格
        :param word_objects:
        :return:
        """

        # 返回结果的keyWord构建
        result = None
        for r in part_basic_keyword_rules:
            result = r.apply(word_objects)
            if result is not None:
                break

        select = u"(p:Part)"
        cypher = None
        for w in word_objects:
            if w.pos == pos_part:
                condition = u"p.partsName = '{partName}'".format(partName=w.token)
            if w.pos == pos_part_code:
                condition = u"p.partsCode = '{partCode}'".format(partCode=w.token)
            withCondition = u"WITH p MATCH (t:PartType) WHERE t.typeCode = p.midTypeId " \
                                u"WITH p, t MATCH (d:Corporation) WHERE d.corpCode = p.vendorID"
            # 进行模板渲染, 生产Cypher语句
            cypher = Cypher_SELECT_DETAIL.format(select=select,
                                              condition=condition,
                                              withCondition=withCondition,
                                              result=result)
            break
        return cypher

    @staticmethod
    def query_part_vehicle_Type(word_objects):
        """
        配件可以装配的车型
        :param word_objects:
        :return:
        """

        # 返回结果的keyWord构建
        result = u'v.vehicleTypeNames as 车型名称, v.vehicleTypeId as 车型编号'

        select = u"(p:Part)<-[r:assemble]-(v:VehicleType)"
        cypher = None
        for w in word_objects:
            if w.pos == pos_part:
                condition = u"p.partsName = '{partName}'".format(partName=w.token)
            if w.pos == pos_part_code:
                condition = u"p.partsCode = '{partCode}'".format(partCode=w.token)
            # 进行模板渲染, 生产Cypher语句
            cypher = Cypher_SELECT_DETAIL.format(select=select,
                                              condition=condition,
                                              withCondition='',
                                              result=result)
            break
        return cypher

    @staticmethod
    def query_part_replace(word_objects):
        """
        配件的可互换配件
        :param word_objects:
        :return:
        """

        # 返回结果的keyWord构建
        result = u'DISTINCT p.partsCode as 互换件编码, p.partsName as 互换件名称'

        select = u"(v:VehicleType)-[r:assemble]->(p:Part)"
        cypher = None
        for w in word_objects:
            if w.pos == pos_part:
                condition = u"p.partsName CONTAINS '{partName}'".format(partName=w.token)
            # 进行模板渲染, 生产Cypher语句
            cypher = Cypher_SELECT_DETAIL.format(select=select,
                                              condition=condition,
                                              withCondition='',
                                              result=result)
            break
        return cypher

    @staticmethod
    def query_part_fault(word_objects):
        """
        配件容易发生故障
        :param word_objects:
        :return:
        """

        # 返回结果的keyWord构建
        result = u'f.faultCode AS 故障代码, f.faultName AS 故障名称'

        select = u"(p:Part)-[h:happen]->(r:Repair)"
        cypher = None
        for w in word_objects:
            if w.pos == pos_part_code:
                condition = u"p.partsCode = '{partCode}'".format(partCode=w.token)
            if w.pos == pos_part:
                condition = u"p.partsName = '{partName}'".format(partName=w.token)
            # 进行模板渲染, 生产Cypher语句
            withConditon = u"WITH p, h, r MATCH (r:Repair)-[c:class]->(f:Fault)"
            cypher = Cypher_SELECT_DETAIL.format(select=select,
                                              condition=condition,
                                              withCondition=withConditon,
                                              result=result)
            break
        return cypher

    @staticmethod
    def query_vehicle_service_station(word_objects):
        """
        车辆送修过的汽车厂信息
        :param word_objects:
        :return:
        """

        # 返回结果的keyWord构建
        result = u'c.corpName AS 服务站名称, c.linkMan AS 联系人, c.linkMobile AS 联系电话, c.address AS 地址'

        select = u"(v:VehicleBirth)-[r:send]->(c:Corporation)"
        cypher = None
        for w in word_objects:
            if w.pos == pos_vehicle:
                condition = u"v.frameCode  = '{frameCode}'".format(frameCode=w.token)
            # 进行模板渲染, 生产Cypher语句
            cypher = Cypher_SELECT_DETAIL.format(select=select,
                                              condition=condition,
                                              withCondition='',
                                              result=result)
            break
        return cypher


    @staticmethod
    def has_movie_question(word_objects):
        """
        某演员演了什么电影
        :param word_objects:
        :return:
        """
        select = u"?x"

        sparql = None
        for w in word_objects:
            # 判断当前word的词性是否是人名
            if w.pos == pos_person:
                e = u"?s :personName '{person}'." \
                    u"?s :hasActedIn ?m." \
                    u"?m :movieTitle ?x".format(person=w.token)

                # 进行模板渲染, 生产SPARQL语句
                sparql = SPARQL_SELECT_TEM.format(prefix=SPARQL_PREXIX,
                                                  select=select,
                                                  expression=e)
                break
        return sparql

    @staticmethod
    def has_actor_question(word_objects):
        """
        哪些演员参演了某电影
        :param word_objects:
        :return:
        """
        select = u"?x"

        sparql = None
        for w in word_objects:
            # 判断当前word的词性是否是电影名
            if w.pos == pos_movie:
                e = u"?m :movieTitle '{movie}'." \
                    u"?m :hasActor ?a." \
                    u"?a :personName ?x".format(movie=w.token)

                sparql = SPARQL_SELECT_TEM.format(prefix=SPARQL_PREXIX,
                                                  select=select,
                                                  expression=e)
                break

        return sparql

    @staticmethod
    def has_cooperation_question(word_objects):
        """
        演员A和演员B有哪些合作的电影
        :param word_objects:
        :return:
        """
        select = u"?x"

        person1 = None
        person2 = None

        for w in word_objects:
            if w.pos == pos_person:
                if person1 is None:
                    person1 = w.token
                else:
                    person2 = w.token
        if person1 is not None and person2 is not None:
            e = u"?p1 :personName '{person1}'." \
                u"?p2 :personName '{person2}'." \
                u"?p1 :hasActedIn ?m." \
                u"?p2 :hasActedIn ?m." \
                u"?m :movieTitle ?x".format(person1=person1, person2=person2)

            return SPARQL_SELECT_TEM.format(prefix=SPARQL_PREXIX,
                                            select=select,
                                            expression=e)
        else:
            return None

    @staticmethod
    def has_compare_question(word_objects):
        """
        某演员参演的评分高于X的电影有哪些？
        :param word_objects:
        :return:
        """
        select = u"?x"

        person = None
        number = None
        keyword = None

        for r in compare_keyword_rules:
            keyword = r.apply(word_objects)
            if keyword is not None:
                break

        for w in word_objects:
            if w.pos == pos_person:
                person = w.token

            if w.pos == pos_number:
                number = w.token

        if person is not None and number is not None:

            e = u"?p :personName '{person}'." \
                u"?p :hasActedIn ?m." \
                u"?m :movieTitle ?x." \
                u"?m :movieRating ?r." \
                u"filter(?r {mark} {number})".format(person=person, number=number,
                                                     mark=keyword)

            return SPARQL_SELECT_TEM.format(prefix=SPARQL_PREXIX,
                                            select=select,
                                            expression=e)
        else:
            return None

    @staticmethod
    def has_movie_type_question(word_objects):
        """
        某演员演了哪些类型的电影
        :param word_objects:
        :return:
        """
        select = u"?x"

        sparql = None
        for w in word_objects:
            if w.pos == pos_person:
                e = u"?s :personName '{person}'." \
                    u"?s :hasActedIn ?m." \
                    u"?m :hasGenre ?g." \
                    u"?g :genreName ?x".format(person=w.token)

                sparql = SPARQL_SELECT_TEM.format(prefix=SPARQL_PREXIX,
                                                  select=select,
                                                  expression=e)
                break
        return sparql

    @staticmethod
    def has_specific_type_movie_question(word_objects):
        """
        某演员演了什么类型（指定类型，喜剧、恐怖等）的电影
        :param word_objects:
        :return:
        """
        select = u"?x"

        keyword = None
        for r in genre_keyword_rules:
            keyword = r.apply(word_objects)

            if keyword is not None:
                break

        sparql = None
        for w in word_objects:
            if w.pos == pos_person:
                e = u"?s :personName '{person}'." \
                    u"?s :hasActedIn ?m." \
                    u"?m :hasGenre ?g." \
                    u"?g :genreName '{keyword}'." \
                    u"?m :movieTitle ?x".format(person=w.token, keyword=keyword)

                sparql = SPARQL_SELECT_TEM.format(prefix=SPARQL_PREXIX,
                                                  select=select,
                                                  expression=e)
                break
        return sparql

    @staticmethod
    def has_quantity_question(word_objects):
        """
        某演员演了多少部电影
        :param word_objects:
        :return:
        """
        select = u"?x"

        sparql = None
        for w in word_objects:
            if w.pos == pos_person:
                e = u"?s :personName '{person}'." \
                    u"?s :hasActedIn ?x.".format(person=w.token)

                sparql = SPARQL_COUNT_TEM.format(prefix=SPARQL_PREXIX, select=select, expression=e)
                break

        return sparql

    @staticmethod
    def is_comedian_question(word_objects):
        """
        某演员是喜剧演员吗
        :param word_objects:
        :return:
        """
        sparql = None
        for w in word_objects:
            if w.pos == pos_person:
                e = u"?s :personName '{person}'." \
                    u"?s rdf:type :Comedian.".format(person=w.token)

                sparql = SPARQL_ASK_TEM.format(prefix=SPARQL_PREXIX, expression=e)
                break

        return sparql

    @staticmethod
    def has_basic_person_info_question(word_objects):
        """
        某演员的基本信息是什么
        :param word_objects:
        :return:
        """

        keyword = None
        for r in person_basic_keyword_rules:
            keyword = r.apply(word_objects)
            if keyword is not None:
                break

        select = u"?x"
        sparql = None
        for w in word_objects:
            if w.pos == pos_person:
                e = u"?s :personName '{person}'." \
                    u"?s {keyword} ?x.".format(person=w.token, keyword=keyword)

                sparql = SPARQL_SELECT_TEM.format(prefix=SPARQL_PREXIX, select=select, expression=e)

                break

        return sparql

    @staticmethod
    def has_basic_movie_info_question(word_objects):
        """
        某电影的基本信息是什么
        :param word_objects:
        :return:
        """

        keyword = None
        for r in movie_basic_keyword_rules:
            keyword = r.apply(word_objects)
            if keyword is not None:
                break

        select = u"?x"
        sparql = None
        for w in word_objects:
            if w.pos == pos_movie:
                e = u"?s :movieTitle '{movie}'." \
                    u"?s {keyword} ?x.".format(movie=w.token, keyword=keyword)

                sparql = SPARQL_SELECT_TEM.format(prefix=SPARQL_PREXIX, select=select, expression=e)

                break

        return sparql


# 属性值设置 ==> action
class PropertyValueSet:
    def __init__(self):
        pass

    @staticmethod
    def return_part_info_value():
        return u'p.partsCode as 配件编码, p.partsName as 配件名称, p.partSpec as 配件规格,  p.unit as 配件单位, t.typeName as 配件类型, d.corpName as 供应商'

    @staticmethod
    def return_part_spec_value():
        return u'p.partSpec as 配件规格'

    @staticmethod
    def return_part_class_value():
        return u't.typeName as 配件类型'

    @staticmethod
    def return_part_vendor_value():
        return u'd.corpName as 供应商'

    @staticmethod
    def return_corp_info_value():
        return u"c.corpName as 企业名称, c.linkMan as 联系人, c.linkMobile as 联系方式," \
                 u"c.email as 邮箱, c.postCode as 邮编, c.fax as 传真, c.address as 地址"

    @staticmethod
    def return_corp_address_value():
        return u'c.address as 地址'

    @staticmethod
    def return_corp_phone_value():
        return u'c.linkMobile as 联系方式 '

    @staticmethod
    def return_corp_email_value():
        return u'c.email as 邮箱'

    @staticmethod
    def return_corp_fax_value():
        return u'c.fax as 传真'

    @staticmethod
    def return_corp_post_value():
        return u'c.postCode as 邮编'

    @staticmethod
    def return_adventure_value():
        return u'冒险'

    @staticmethod
    def return_fantasy_value():
        return u'奇幻'

    @staticmethod
    def return_animation_value():
        return u'动画'

    @staticmethod
    def return_drama_value():
        return u'剧情'

    @staticmethod
    def return_thriller_value():
        return u'恐怖'

    @staticmethod
    def return_action_value():
        return u'动作'

    @staticmethod
    def return_comedy_value():
        return u'喜剧'

    @staticmethod
    def return_history_value():
        return u'历史'

    @staticmethod
    def return_western_value():
        return u'西部'

    @staticmethod
    def return_horror_value():
        return u'惊悚'

    @staticmethod
    def return_crime_value():
        return u'犯罪'

    @staticmethod
    def return_documentary_value():
        return u'纪录'

    @staticmethod
    def return_fiction_value():
        return u'科幻'

    @staticmethod
    def return_mystery_value():
        return u'悬疑'

    @staticmethod
    def return_music_value():
        return u'音乐'

    @staticmethod
    def return_romance_value():
        return u'爱情'

    @staticmethod
    def return_family_value():
        return u'家庭'

    @staticmethod
    def return_war_value():
        return u'战争'

    @staticmethod
    def return_tv_value():
        return u'电视电影'

    @staticmethod
    def return_higher_value():
        return u'>'

    @staticmethod
    def return_lower_value():
        return u'<'

    @staticmethod
    def return_birth_value():
        return u':personBirthDay'

    @staticmethod
    def return_birth_place_value():
        return u':personBirthPlace'

    @staticmethod
    def return_english_name_value():
        return u':personEnglishName'

    @staticmethod
    def return_person_introduction_value():
        return u':personBiography'

    @staticmethod
    def return_movie_introduction_value():
        return u':movieIntroduction'

    @staticmethod
    def return_release_value():
        return u':movieReleaseDate'

    @staticmethod
    def return_rating_value():
        return u':movieRating'


# TODO 定义关键词
pos_person = "nr"
pos_movie = "nz"
pos_number = "m"

person_entity = (W(pos=pos_person))
movie_entity = (W(pos=pos_movie))
number_entity = (W(pos=pos_number))

# 定义配件和企业词性
pos_part = "part"
pos_part_code = "code"
pos_corp = "corp"
pos_vehicle = "vehicle"

part_entity = (W(pos=pos_part) | W(pos=pos_part_code))
corp_entity = (W(pos=pos_corp))
vehicle_entity = (W(pos=pos_vehicle))

# 配件
part_info = (W("信息") | W("基础信息") | W("详细信息") | W("详情"))
part_spec = (W("规格") | W("型号") | W("规格型号"))
part_type = (W("类型") | W("配件类型") | W("分类") | W("类别"))
part_vendor = (W("供应商") | W("配件供应商"))
part_basic = (part_info | part_spec | part_type | part_vendor)

part_mount = (W("装配") | W("安装") | W("使用") | W("用"))
part_vehicle_Type = (W("车型") | W("型号"))

part_replace = (W("互换件") | W("替换件"))
part_fault = (W("故障") | W("故障名称") | W("问题"))

# 企业
corp_info = (W("信息") | W("基础信息") | W("详细信息") | W("详情"))
corp_address = (W("位置") | W("地址") | W("地方") | W("公司地址") | W("公司位置"))
corp_phone = (W("手机号") | W("手机") | W("联系方式") | W("电话"))
corp_email = (W("邮箱") | W("email") | W("邮箱号"))
corp_fax = (W("传真") | W("传真号") | W("传真号码"))
corp_post = (W("邮编") | W("邮编号码") | W("邮编号"))
corp_basic = (corp_info | corp_address | corp_phone | corp_email | corp_fax | corp_post)
where = (W("哪里") | W("哪儿") | W("何地") | W("何处") | W("在") + W("哪"))


# 车辆
vehicle_repair = (W("送修") | W("维修") | W("修理"))
service_station = (W("服务站") | W("修理厂") | W("汽修厂") | W("维修厂"))

# adventure = {
#   token: re.compile('冒险$')
#   pos: re.compile('.*$')
# }

adventure = W("冒险")
fantasy = W("奇幻")
animation = (W("动画") | W("动画片"))
drama = (W("剧情") | W("剧情片"))
thriller = (W("恐怖") | W("恐怖片"))
action = (W("动作") | W("动作片"))
comedy = (W("喜剧") | W("喜剧片"))
history = (W("历史") | W("历史剧"))
western = (W("西部") | W("西部片"))
horror = (W("惊悚") | W("惊悚片"))
crime = (W("犯罪") | W("犯罪片"))
documentary = (W("纪录") | W("纪录片"))
science_fiction = (W("科幻") | W("科幻片"))
mystery = (W("悬疑") | W("悬疑片"))
music = (W("音乐") | W("音乐片"))
romance = (W("爱情") | W("爱情片"))
family = W("家庭")
war = (W("战争") | W("战争片"))
TV = W("电视")
genre = (adventure | fantasy | animation | drama | thriller | action
         | comedy | history | western | horror | crime | documentary |
         science_fiction | mystery | music | romance | family | war
         | TV)

actor = (W("演员") | W("艺人") | W("表演者"))
movie = (W("电影") | W("影片") | W("片子") | W("片") | W("剧"))
category = (W("类型") | W("种类"))
several = (W("多少") | W("几部"))

higher = (W("大于") | W("高于"))
lower = (W("小于") | W("低于"))
compare = (higher | lower)

birth = (W("生日") | W("出生") + W("日期") | W("出生"))
birth_place = (W("出生地") | W("出生"))
english_name = (W("英文名") | W("英文") + W("名字"))
introduction = (W("介绍") | W("是") + W("谁") | W("简介"))
person_basic = (birth | birth_place | english_name | introduction)

rating = (W("评分") | W("分") | W("分数"))
release = (W("上映"))
movie_basic = (rating | introduction | release)

when = (W("何时") | W("时候"))

# TODO 问题模板/匹配规则
"""
========================= 配件相关问题 ============================
1. A个配件属于什么配件类型 / A配件的规格是什么 / A配件的配件供应商是谁 ✔
2. 配件A的详细信息 ✔
3. B供应商的地址 / 联系方式 / 邮箱 / 传真 / 邮编 (其实不仅仅局限于供应商,也可以是服务站) ✔
4. 供应商A的详细信息 ✔
5. A配件可以装配在哪些车型上 ✔
6. 配件A的可互换件有哪些 ✔
7. 配件A容易发生什么故障  ✔
8. A配件发生了B故障怎么办/原因 (通过配件和故障 => 解决方案) ×

========================= 车辆相关问题 ============================
1. 车辆A在哪里送修过, 即送修服务站信息？


"""
rules = [
    # Rule(condition_num=2, condition=person_entity + Star(Any(), greedy=False) + movie + Star(Any(), greedy=False),
    #      action=QuestionSet.has_movie_question),
    # Rule(condition_num=2, condition=(movie_entity + Star(Any(), greedy=False) + actor + Star(Any(), greedy=False)) | (
    #             actor + Star(Any(), greedy=False) + movie_entity + Star(Any(), greedy=False)),
    #      action=QuestionSet.has_actor_question),
    # Rule(condition_num=3,
    #      condition=person_entity + Star(Any(), greedy=False) + person_entity + Star(Any(), greedy=False) + (
    #                  movie | Star(Any(), greedy=False)), action=QuestionSet.has_cooperation_question),
    # Rule(condition_num=4, condition=person_entity + Star(Any(), greedy=False) + compare + number_entity + Star(Any(),
    #                                                                                                            greedy=False) + movie + Star(
    #     Any(), greedy=False), action=QuestionSet.has_compare_question),
    # Rule(condition_num=3,
    #      condition=person_entity + Star(Any(), greedy=False) + category + Star(Any(), greedy=False) + movie,
    #      action=QuestionSet.has_movie_type_question),
    # Rule(condition_num=3, condition=person_entity + Star(Any(), greedy=False) + genre + Star(Any(), greedy=False) + (
    #             movie | Star(Any(), greedy=False)), action=QuestionSet.has_specific_type_movie_question),
    # Rule(condition_num=3, condition=person_entity + Star(Any(), greedy=False) + several + Star(Any(), greedy=False) + (
    #             movie | Star(Any(), greedy=False)), action=QuestionSet.has_quantity_question),
    # Rule(condition_num=3,
    #      condition=person_entity + Star(Any(), greedy=False) + comedy + actor + Star(Any(), greedy=False),
    #      action=QuestionSet.is_comedian_question),
    # Rule(condition_num=3, condition=(person_entity + Star(Any(), greedy=False) + (when | where) + person_basic + Star(
    #     Any(), greedy=False)) | (person_entity + Star(Any(), greedy=False) + person_basic + Star(Any(), greedy=False)),
    #      action=QuestionSet.has_basic_person_info_question),
    # Rule(condition_num=2, condition=movie_entity + Star(Any(), greedy=False) + movie_basic + Star(Any(), greedy=False),
    #      action=QuestionSet.has_basic_movie_info_question),
    #

    Rule(condition_num=2, condition=corp_entity + Star(Any(), greedy=False) + corp_basic + Star(Any(), greedy=False),
         action=QuestionSet.query_corporation_basic),
    Rule(condition_num=2, condition=part_entity + Star(Any(), greedy=False) + part_basic + Star(Any(), greedy=False),
         action=QuestionSet.query_part_basic),
    Rule(condition_num=3, condition=part_entity + Star(Any(), greedy=False)  + part_mount + Star(Any(), greedy=False) +
        part_vehicle_Type + Star(Any(), greedy=False),action=QuestionSet.query_part_vehicle_Type),
    Rule(condition_num=2, condition=part_entity + Star(Any(), greedy=False) + part_replace + Star(Any(), greedy=False),
         action=QuestionSet.query_part_replace),
    Rule(condition_num=2, condition=part_entity + Star(Any(), greedy=False) + part_fault + Star(Any(), greedy=False),
         action=QuestionSet.query_part_fault),
    Rule(condition_num=2, condition=vehicle_entity + Star(Any(), greedy=False) + (service_station + Star(Any(), greedy=False) | vehicle_repair + Star(Any(), greedy=False)),
         action=QuestionSet.query_vehicle_service_station)
]

# 配件基础信息模板
part_basic_keyword_rules = [
    KeywordRule(
        condition=(part_entity + Star(Any(), greedy=False) + part_info + Star(Any(), greedy=False)),
        action=PropertyValueSet.return_part_info_value),
    KeywordRule(
        condition=(part_entity + Star(Any(), greedy=False) + part_spec + Star(Any(), greedy=False)),
        action=PropertyValueSet.return_part_spec_value),
    KeywordRule(
        condition=(part_entity + Star(Any(), greedy=False) + part_type + Star(Any(), greedy=False)),
        action=PropertyValueSet.return_part_class_value),
    KeywordRule(
        condition=(part_entity + Star(Any(), greedy=False) + part_vendor + Star(Any(), greedy=False)),
        action=PropertyValueSet.return_part_vendor_value)
]

# 企业基础信息模板
corp_basic_keyword_rules = [
    KeywordRule(
        condition=(corp_entity + Star(Any(), greedy=False) + corp_info + Star(Any(), greedy=False)),
        action=PropertyValueSet.return_corp_info_value),
    KeywordRule(
        condition=(corp_entity + Star(Any(), greedy=False) + corp_address + where + Star(Any(), greedy=False)) | (
                corp_entity + Star(Any(), greedy=False) + corp_address + Star(Any(), greedy=False)),
        action=PropertyValueSet.return_corp_address_value),
    KeywordRule(
        condition=(corp_entity + Star(Any(), greedy=False) + corp_phone + Star(Any(), greedy=False)),
        action=PropertyValueSet.return_corp_phone_value),
    KeywordRule(
        condition=(corp_entity + Star(Any(), greedy=False) + corp_email + Star(Any(), greedy=False)),
        action=PropertyValueSet.return_corp_email_value),
    KeywordRule(
        condition=(corp_entity + Star(Any(), greedy=False) + corp_fax + Star(Any(), greedy=False)),
        action=PropertyValueSet.return_corp_fax_value),
    KeywordRule(
        condition=(corp_entity + Star(Any(), greedy=False) + corp_post + Star(Any(), greedy=False)),
        action=PropertyValueSet.return_corp_post_value)
]


# TODO 具体的属性词匹配规则
genre_keyword_rules = [
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + adventure + Star(Any(), greedy=False) + (
                movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_adventure_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + fantasy + Star(Any(), greedy=False) + (
                movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_fantasy_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + animation + Star(Any(), greedy=False) + (
                movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_animation_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + drama + Star(Any(), greedy=False) + (
                movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_drama_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + thriller + Star(Any(), greedy=False) + (
                movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_thriller_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + action + Star(Any(), greedy=False) + (
                movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_action_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + comedy + Star(Any(), greedy=False) + (
                movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_comedy_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + history + Star(Any(), greedy=False) + (
                movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_history_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + western + Star(Any(), greedy=False) + (
                movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_western_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + horror + Star(Any(), greedy=False) + (
                movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_horror_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + crime + Star(Any(), greedy=False) + (
                movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_crime_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + documentary + Star(Any(), greedy=False) + (
                movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_documentary_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + science_fiction + Star(Any(), greedy=False) + (
                movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_fiction_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + mystery + Star(Any(), greedy=False) + (
                movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_mystery_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + music + Star(Any(), greedy=False) + (
                movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_music_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + romance + Star(Any(), greedy=False) + (
                movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_romance_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + family + Star(Any(), greedy=False) + (
                movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_family_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + war + Star(Any(), greedy=False) + (
                movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_war_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + TV + Star(Any(), greedy=False) + (
                movie | Star(Any(), greedy=False)), action=PropertyValueSet.return_tv_value)
]

compare_keyword_rules = [
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + higher + number_entity + Star(Any(),
                                                                                                    greedy=False) + movie + Star(
        Any(), greedy=False), action=PropertyValueSet.return_higher_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + lower + number_entity + Star(Any(),
                                                                                                   greedy=False) + movie + Star(
        Any(), greedy=False), action=PropertyValueSet.return_lower_value)
]


person_basic_keyword_rules = [
    KeywordRule(
        condition=(person_entity + Star(Any(), greedy=False) + where + birth_place + Star(Any(), greedy=False)) | (
                    person_entity + Star(Any(), greedy=False) + birth_place + Star(Any(), greedy=False)),
        action=PropertyValueSet.return_birth_place_value),
    KeywordRule(
        condition=person_entity + Star(Disjunction(Any(), where), greedy=False) + birth + Star(Any(), greedy=False),
        action=PropertyValueSet.return_birth_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + english_name + Star(Any(), greedy=False),
                action=PropertyValueSet.return_english_name_value),
    KeywordRule(condition=person_entity + Star(Any(), greedy=False) + introduction + Star(Any(), greedy=False),
                action=PropertyValueSet.return_person_introduction_value)
]

movie_basic_keyword_rules = [
    KeywordRule(condition=movie_entity + Star(Any(), greedy=False) + introduction + Star(Any(), greedy=False),
                action=PropertyValueSet.return_movie_introduction_value),
    KeywordRule(condition=movie_entity + Star(Any(), greedy=False) + release + Star(Any(), greedy=False),
                action=PropertyValueSet.return_release_value),
    KeywordRule(condition=movie_entity + Star(Any(), greedy=False) + rating + Star(Any(), greedy=False),
                action=PropertyValueSet.return_rating_value),
]

# TODO 用于测试
if __name__ == '__main__':
    pos_person = "nr"
    person_entity = (W(pos=pos_person))
    print(person_entity.token)
    print(person_entity.pos)
    animation = (W("动画") | W("动画片"))
    print(animation)
