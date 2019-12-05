import yaml
import requests
from string import Template


def request(*args, **kwargs):
    res = requests.request(*args, **kwargs)
    return res

funcs = {}
funcs['request'] = request


def format_args(args, variables):   # 处理参数化请求中的${变量}
    args_str = yaml.dump(args)  # 先转为字符串
    if '$' in args_str:
        args_str = Template(args_str).safe_substitute(variables)  # 替换${变量}为局部变量中的同名变量
        args = yaml.safe_load(args_str)  # 重新转为字典
    return args


def main():
    with open('httpbird.yaml', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    variables = data.get('variables', {})
    # tests = data.get('tests', [])
    tests = {key: value for key, value in data.items() if key.startswith('test')}
    session = requests.session()
    for name, test in tests.items():
        print("执行测试:", name, '-'*25)
        steps = test.get('steps')
        for i, step in enumerate(steps):
            print(f'步骤{i+1}:', step.get('func'))
            args = step.get('args', {})  # 请求报文，默认值为{}

            # 处理参数化请求中的${变量}
            func = funcs.get(step.get('func'))
            args = format_args(args, variables)

            # 发送请求
            res = func(**args)  # 字典解包，发送接口
            print('请求数据:', args)
            print("响应数据:", res.text.strip())
            variables['res'] = res
            # 提取变量
            register = step.get('register')
            if register is not None:  # 如果存在extract
                for key, value in register.items():
                    # 计算value表达式，可使用的全局变量为空，可使用的局部变量为RESPONSE(响应对象)
                    # 保存变量结果到局部变量中
                    print("提取变量:", key, value)
                    variables[key] = eval(value, {}, variables)

            # 处理断言
            asserts = step.get('assert')
            if asserts is not None:
                for line in asserts:
                    result = eval(line, {}, variables) # 计算断言表达式，True代表成功，False代表失败
                    print("执行断言:", line, "结果:", "PASS" if result else "FAIL")


if __name__ == '__main__':
    main()
