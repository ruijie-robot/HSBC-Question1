import yaml

###### 用户提问模式总结
# 直接查询费率（如"X服务的收费是多少？"）

# 比较不同账户/服务的优劣（如"Y和Z哪个更划算？"）

# 验证特权适用性（如"我是否符合免年费条件？"）

# 操作流程咨询（如"如何申请免收纸质账单费？"）



def get_question_library(type=None):
    with open('data/questions.yaml', 'r') as f:
        questions_data = yaml.safe_load(f)

    if type is None:
        questions = [q['question'] for q in questions_data]
    else:
        questions = [q['question'] for q in questions_data if q['type'] == type]

    return questions