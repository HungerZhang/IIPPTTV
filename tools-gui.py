import json  # 添加缺失的json导入
import requests
import os
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import time
from datetime import datetime

class LiveStreamExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("直播源提取与去重工具")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 设置中文字体支持
        self.font = ('SimHei', 10)
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标题标签
        self.title_label = ttk.Label(self.main_frame, text="直播源提取与去重工具", font=('SimHei', 16, 'bold'))
        self.title_label.pack(pady=10)
        
        # 创建参数设置区域
        self.settings_frame = ttk.LabelFrame(self.main_frame, text="设置", padding="10")
        self.settings_frame.pack(fill=tk.X, pady=5)
        
        # API URL设置
        ttk.Label(self.settings_frame, text="API URL:", font=self.font).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.api_url_var = tk.StringVar(value="http://api.hclyz.com:81/mf/json.txt")
        self.api_url_entry = ttk.Entry(self.settings_frame, textvariable=self.api_url_var, width=60, font=self.font)
        self.api_url_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # 前缀设置
        ttk.Label(self.settings_frame, text="地址前缀:", font=self.font).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.prefix_var = tk.StringVar(value="http://api.hclyz.com:81/mf/")
        self.prefix_entry = ttk.Entry(self.settings_frame, textvariable=self.prefix_var, width=60, font=self.font)
        self.prefix_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # 输出文件设置
        ttk.Label(self.settings_frame, text="输出文件:", font=self.font).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.output_file_var = tk.StringVar(value="result_deduplicated.m3u")
        self.output_file_entry = ttk.Entry(self.settings_frame, textvariable=self.output_file_var, width=60, font=self.font)
        self.output_file_entry.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # 创建按钮区域
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.pack(fill=tk.X, pady=10)
        
        self.start_button = ttk.Button(self.button_frame, text="开始处理", command=self.start_processing)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(self.button_frame, text="停止处理", command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(self.button_frame, text="清空日志", command=self.clear_log)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # 创建进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.main_frame, variable=self.progress_var, length=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # 创建日志区域
        self.log_frame = ttk.LabelFrame(self.main_frame, text="处理日志", padding="10")
        self.log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(self.log_frame, wrap=tk.WORD, font=self.font)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # 创建统计信息区域
        self.stats_frame = ttk.LabelFrame(self.main_frame, text="统计信息", padding="10")
        self.stats_frame.pack(fill=tk.X, pady=5)
        
        self.raw_count_var = tk.StringVar(value="原始条目: 0")
        self.extracted_count_var = tk.StringVar(value="提取条目: 0")
        self.deduplicated_count_var = tk.StringVar(value="去重后条目: 0")
        
        ttk.Label(self.stats_frame, textvariable=self.raw_count_var, font=self.font).grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        ttk.Label(self.stats_frame, textvariable=self.extracted_count_var, font=self.font).grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)
        ttk.Label(self.stats_frame, textvariable=self.deduplicated_count_var, font=self.font).grid(row=0, column=2, padx=10, pady=5, sticky=tk.W)
        
        # 处理线程控制
        self.processing_thread = None
        self.stop_event = threading.Event()
    
    def log(self, message):
        """向日志区域添加消息"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def clear_log(self):
        """清空日志区域"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def update_progress(self, value):
        """更新进度条"""
        self.progress_var.set(value)
        
    def update_stats(self, raw_count=None, extracted_count=None, deduplicated_count=None):
        """更新统计信息"""
        if raw_count is not None:
            self.raw_count_var.set(f"原始条目: {raw_count}")
        if extracted_count is not None:
            self.extracted_count_var.set(f"提取条目: {extracted_count}")
        if deduplicated_count is not None:
            self.deduplicated_count_var.set(f"去重后条目: {deduplicated_count}")
    
    def start_processing(self):
        """开始处理数据"""
        # 禁用开始按钮，启用停止按钮
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        # 重置停止事件
        self.stop_event.clear()
        
        # 启动处理线程
        self.processing_thread = threading.Thread(target=self.process_data)
        self.processing_thread.daemon = True
        self.processing_thread.start()
    
    def stop_processing(self):
        """停止处理数据"""
        self.stop_event.set()
        self.log("正在停止处理...")
    
    def extract_data(self):
        """提取数据的核心函数"""
        try:
            url = self.api_url_var.get()
            prefix = self.prefix_var.get()
            
            # 主API URL访问优化
            self.log(f"开始从 {url} 获取数据")
            try:
                response = requests.get(url, timeout=30)
                response.encoding = 'utf-8'
                raw_data = json.loads(response.text)
            except Exception as e:
                self.log(f"访问主API URL失败: {str(e)}")
                self.log("无法获取初始数据，处理终止")
                return None
            
            # 提取title和address，并在address前添加前缀（如果需要），生成JSON暂存数据
            json_data = []
            try:
                for item in raw_data['pingtai']:
                    if self.stop_event.is_set():
                        self.log("处理已停止")
                        return None
                    
                    title = item.get('title', '')
                    address = item.get('address', '')
                    
                    # 需求3: 当title是"卫视直播"时，跳过
                    if title == '卫视直播':
                        self.log(f"跳过标题为'卫视直播'的条目")
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
            except Exception as e:
                self.log(f"解析主数据结构失败: {str(e)}")
                self.log("无法提取有效数据，处理终止")
                return None
            
            self.update_stats(raw_count=len(json_data))
            self.log(f"已成功生成JSON暂存数据，共{len(json_data)}条记录。")
            
            # 保存JSON暂存数据
            try:
                with open('temp_data.json', 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                self.log(f"保存暂存数据失败: {str(e)}")
                # 即使保存失败，也继续处理，因为我们已经有了内存中的数据
            
            # 访问每个条目的address，获取数据并提取title和address
            final_data = []
            total_items = len(json_data)
            
            for i, item in enumerate(json_data):
                if self.stop_event.is_set():
                    self.log("处理已停止")
                    return final_data  # 返回已处理的部分数据
                
                try:
                    # 更新进度
                    progress = (i + 1) / total_items * 100
                    self.root.after(100, lambda p=progress: self.update_progress(p))
                    
                    # 访问address获取数据 - 优化错误处理，确保错误时直接跳过
                    self.log(f"正在访问({i+1}/{total_items}): {item['title']} - {item['address']}")
                    response = requests.get(item['address'], timeout=10)
                    response.encoding = 'utf-8'
                    
                    # 尝试解析为JSON
                    try:
                        data = response.json()
                        self.log(f"成功解析JSON数据")
                        
                        # 检查数据结构
                        if isinstance(data, list):
                            self.log(f"数据是列表，包含{len(data)}个元素")
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
                            self.log(f"数据是字典")
                            # 检查是否包含'zhubo'数组
                            if 'zhubo' in data and isinstance(data['zhubo'], list):
                                self.log(f"包含zhubo数组，有{len(data['zhubo'])}个元素")
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
                                self.log(f"包含pingtai数组，有{len(data['pingtai'])}个元素")
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
                        self.log(f"无法解析{item['title']}的响应数据，非JSON格式")
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
                    self.log(f"访问{item['title']}的address失败: {str(e)[:100]}")
                    self.log(f"跳过此条目，继续处理下一个")  # 明确记录跳过行为
                    # 需求2: 当无法访问地址时，直接放弃，不做数据记录
                    continue  # 关键：确保错误时直接跳过，继续处理下一个
            
            self.update_stats(extracted_count=len(final_data))
            self.log(f"从{total_items}个暂存条目处理得到{len(final_data)}个有效条目")
            return final_data
        except Exception as e:
            self.log(f"提取数据时发生错误: {str(e)}")
            return None
    
    def deduplicate_data(self, data):
        """对数据进行去重处理"""
        # 用于存储唯一标题和对应条目的字典
        unique_entries = {}
        
        for item in data:
            title = item.get('title', '未命名')
            # 如果标题已存在，则跳过
            if title not in unique_entries:
                unique_entries[title] = item
        
        deduplicated_data = list(unique_entries.values())
        self.update_stats(deduplicated_count=len(deduplicated_data))
        self.log(f"去重完成！共处理 {len(deduplicated_data)} 个唯一标题。")
        return deduplicated_data
    
    def generate_m3u(self, data, output_file):
        """生成m3u文件"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('#EXTM3U\n')
                for item in data:
                    title = item.get('title', '未命名')
                    address = item.get('address', '')
                    if address:
                        f.write(f'#EXTINF:-1,{title}\n')
                        f.write(f'{address}\n')
            
            self.log(f"已成功生成m3u文件，共{len(data)}条记录。")
            self.log(f"结果已保存到: {os.path.abspath(output_file)}")
            return True
        except Exception as e:
            self.log(f"生成m3u文件时发生错误: {str(e)}")
            return False
    
    def process_data(self):
        """处理数据的主函数"""
        try:
            # 1. 提取数据
            self.log("开始提取数据...")
            extracted_data = self.extract_data()
            
            if self.stop_event.is_set():
                self.log("数据提取已停止")
                self.root.after(100, lambda: self.reset_ui())
                return
                
            if extracted_data is None or len(extracted_data) == 0:
                self.log("未提取到任何数据或数据提取失败")
                self.root.after(100, lambda: self.reset_ui())
                return
            
            # 2. 去重数据
            self.log("开始去重数据...")
            deduplicated_data = self.deduplicate_data(extracted_data)
            
            if self.stop_event.is_set():
                self.log("数据去重已停止")
                self.root.after(100, lambda: self.reset_ui())
                return
            
            # 3. 生成去重后的m3u文件
            output_file = self.output_file_var.get()
            self.log(f"开始生成m3u文件: {output_file}...")
            success = self.generate_m3u(deduplicated_data, output_file)
            
            if success:
                self.log("处理完成！")
                self.root.after(100, lambda: messagebox.showinfo("成功", "处理完成！\n" + 
                                                                f"原始条目: {self.raw_count_var.get().split(':')[1].strip()}\n" +
                                                                f"提取条目: {self.extracted_count_var.get().split(':')[1].strip()}\n" +
                                                                f"去重后条目: {self.deduplicated_count_var.get().split(':')[1].strip()}\n" +
                                                                f"结果已保存到: {os.path.abspath(output_file)}"))
            else:
                self.log("处理失败！")
                self.root.after(100, lambda: messagebox.showerror("失败", "处理失败，请查看日志了解详情。"))
        except Exception as e:
            self.log(f"处理过程中发生错误: {str(e)}")
            self.root.after(100, lambda: messagebox.showerror("错误", f"处理过程中发生错误: {str(e)}"))
        finally:
            # 重置UI状态
            self.root.after(100, lambda: self.reset_ui())
    
    def reset_ui(self):
        """重置UI状态"""
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_progress(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = LiveStreamExtractorApp(root)
    root.mainloop()
