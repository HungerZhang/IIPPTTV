import json
import requests

# 从URL获取JSON数据
url = 'http://api.hclyz.com:81/mf/json.txt'
response = requests.get(url)
response.encoding = 'utf-8'
raw_data = json.loads(response.text)

# 提取title和address，并在address前添加前缀，生成JSON暂存数据
prefix = 'http://api.hclyz.com:81/mf/'
json_data = []
for item in raw_data['pingtai']:
    title = item.get('title', '')
    address = item.get('address', '')
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
                            if not sub_address.startswith('http'):
                                sub_address = prefix + sub_address
                            final_data.append({
                                'title': sub_title,
                                'address': sub_address
                            })
            elif isinstance(data, dict):
                print(f"数据是字典")
                # 检查是否包含'zhubo'数组（从日志中观察到的结构）
                if 'zhubo' in data and isinstance(data['zhubo'], list):
                    print(f"包含zhubo数组，有{len(data['zhubo'])}个元素")
                    for sub_item in data['zhubo']:
                        sub_title = sub_item.get('title', item['title'] or '未命名')
                        sub_address = sub_item.get('address', '')
                        if sub_address:
                            if not sub_address.startswith('http'):
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
                            if not sub_address.startswith('http'):
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
                        if not sub_address.startswith('http'):
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
                if text_content.startswith('http'):
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

print(f"从{len(json_data)}个暂存条目处理得到{len(final_data)}个有效条目")

# 生成m3u8文件
with open('result.m3u8', 'w', encoding='utf-8') as f:
    f.write('#EXTM3U\n')
    for item in final_data:
        title = item.get('title', '未命名')
        address = item.get('address', '')
        if address:
            f.write(f'#EXTINF:-1,{title}\n')
            f.write(f'{address}\n')

print(f"已成功生成m3u8文件，共{len(final_data)}条记录。")
