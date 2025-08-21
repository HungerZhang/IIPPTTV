import json
import requests
import os

def extract_data():
    # 从URL获取JSON数据
    url = 'http://api.hclyz.com:81/mf/json.txt'
    response = requests.get(url)
    response.encoding = 'utf-8'
    raw_data = json.loads(response.text)

    # 提取title和address，并在address前添加前缀（如果需要），生成JSON暂存数据
    prefix = 'http://api.hclyz.com:81/mf/'
    json_data = []
    for item in raw_data['pingtai']:
        title = item.get('title', '')
        address = item.get('address', '')
        
        # 需求3: 当title是"卫视直播"时，跳过
        if title == '卫视直播':
            print(f"跳过标题为'卫视直播'的条目")
            continue
        
        # 需求1: 当address以rtmp开头时，不需要加前缀
        if address.startswith('rtmp'):
            full_address = address
        else:
            full_address = prefix + address
        
        json_data.append({
            'title': title,
            'address': full_address
        })

    # 保存JSON暂存数据
    with open('temp_data.json', 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    print(f"已成功生成JSON暂存数据，共{len(json_data)}条记录。")

    # 读取暂存的JSON数据
    with open('temp_data.json', 'r', encoding='utf-8') as f:
        json_data = json.load(f)

    # 访问每个条目的address，获取数据并提取title和address
    final_data = []
    for item in json_data:
        try:
            # 访问address获取数据
            print(f"正在访问: {item['title']} - {item['address']}")
            response = requests.get(item['address'], timeout=10)
            response.encoding = 'utf-8'

            # 打印响应状态码和前100个字符，便于调试
            print(f"响应状态码: {response.status_code}")
            print(f"响应内容前100字符: {response.text[:100]}")

            # 尝试解析为JSON
            try:
                data = response.json()
                print(f"成功解析JSON数据")

                # 检查数据结构
                if isinstance(data, list):
                    print(f"数据是列表，包含{len(data)}个元素")
                    for sub_item in data:
                        if isinstance(sub_item, dict):
                            sub_title = sub_item.get('title', item['title'] or '未命名')
                            sub_address = sub_item.get('address', '')
                            if sub_address:
                                # 需求1: 当address以http或rtmp开头时，不需要加前缀
                                if not (sub_address.startswith('http') or sub_address.startswith('rtmp')):
                                    sub_address = prefix + sub_address
                                final_data.append({
                                    'title': sub_title,
                                    'address': sub_address
                                })
                elif isinstance(data, dict):
                    print(f"数据是字典")
                    # 检查是否包含'zhubo'数组
                    if 'zhubo' in data and isinstance(data['zhubo'], list):
                        print(f"包含zhubo数组，有{len(data['zhubo'])}个元素")
                        for sub_item in data['zhubo']:
                            sub_title = sub_item.get('title', item['title'] or '未命名')
                            sub_address = sub_item.get('address', '')
                            if sub_address:
                                # 需求1: 当address以http或rtmp开头时，不需要加前缀
                                if not (sub_address.startswith('http') or sub_address.startswith('rtmp')):
                                    sub_address = prefix + sub_address
                                final_data.append({
                                    'title': sub_title,
                                    'address': sub_address
                                })
                    # 同时检查'pingtai'数组，保持兼容性
                    elif 'pingtai' in data and isinstance(data['pingtai'], list):
                        print(f"包含pingtai数组，有{len(data['pingtai'])}个元素")
                        for sub_item in data['pingtai']:
                            sub_title = sub_item.get('title', item['title'] or '未命名')
                            sub_address = sub_item.get('address', '')
                            if sub_address:
                                # 需求1: 当address以http或rtmp开头时，不需要加前缀
                                if not (sub_address.startswith('http') or sub_address.startswith('rtmp')):
                                    sub_address = prefix + sub_address
                                final_data.append({
                                    'title': sub_title,
                                    'address': sub_address
                                })
                    else:
                        # 直接提取title和address
                        sub_title = data.get('title', item['title'] or '未命名')
                        sub_address = data.get('address', '')
                        if sub_address:
                            # 需求1: 当address以rtmp开头时，不需要加前缀
                            if not (sub_address.startswith('http') or sub_address.startswith('rtmp')):
                                sub_address = prefix + sub_address
                            final_data.append({
                                'title': sub_title,
                                'address': sub_address
                            })
            except json.JSONDecodeError:
                print(f"无法解析{item['title']}的响应数据，非JSON格式")
                # 尝试将文本内容作为address
                text_content = response.text.strip()
                if text_content:
                    # 假设文本内容可能是一个URL
                    # 需求1: 当address以http或rtmp开头时，不需要加前缀
                    if text_content.startswith('http') or text_content.startswith('rtmp'):
                        final_data.append({
                            'title': item['title'] or '未命名',
                            'address': text_content
                        })
                    else:
                        # 或者可能是一个相对路径
                        final_data.append({
                            'title': item['title'] or '未命名',
                            'address': prefix + text_content
                        })
        except Exception as e:
            print(f"访问{item['title']}的address失败: {str(e)[:100]}")
            # 需求2: 当无法访问地址时，直接放弃，不做数据记录
            continue

    print(f"从{len(json_data)}个暂存条目处理得到{len(final_data)}个有效条目")
    return final_data


def deduplicate_data(data):
    # 用于存储唯一标题和对应条目的字典
    unique_entries = {}

    for item in data:
        title = item.get('title', '未命名')
        # 如果标题已存在，则跳过
        if title not in unique_entries:
            unique_entries[title] = item

    deduplicated_data = list(unique_entries.values())
    print(f"去重完成！共处理 {len(deduplicated_data)} 个唯一标题。")
    return deduplicated_data


def generate_m3u(data, output_file):
    # 生成m3u文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('#EXTM3U\n')
        for item in data:
            title = item.get('title', '未命名')
            address = item.get('address', '')
            if address:
                f.write(f'#EXTINF:-1,{title}\n')
                f.write(f'{address}\n')

    print(f"已成功生成m3u文件，共{len(data)}条记录。")


if __name__ == '__main__':
    # 1. 提取数据
    extracted_data = extract_data()

    # 2. 去重数据
    deduplicated_data = deduplicate_data(extracted_data)

    # 3. 生成去重后的m3u文件
    output_file = 'result_deduplicated.m3u'
    generate_m3u(deduplicated_data, output_file)

    print(f"结果已保存到: {os.path.abspath(output_file)}")
