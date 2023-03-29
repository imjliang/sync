# -*- coding: utf-8 -*-
"""
大文件以及包含大文件的目录重命名建议直接手动操作
因为本代码只要名字不同都认为是不同的文件，没有做内容比较的优化
a -> b, 由 a 目录向 b 目录备份
Author:   Andy Dennis AIron
Date:     2021.11.11
Version:  V4.0
Detail:
V4.0改动(2021.11.19): 
    增加统计 比较目录花费的时间和同步操作花费的时间 的操作
    主函数目录输入的格式进行了修改
V3.0改动(2021.11.12):
    相比V2.0, 修复exFAT格式文件系统时间戳精度问题。（line 84 判断条件）
判断文件是否相同方法: 文件大小和修改时间戳区别是否大于2秒, 所以请您修改完文件选择保存
的时间 与 上一次修改文件的时间(备份时的那个版本的文件)大于2秒即可
V2.0改动(2021.11.11):
    修复判断文件相同的比较条件的bug
"""

import shutil
import os
from tqdm import tqdm
import time


class Sync:
    def __init__(self, d_a:str, d_b:str):
        """
        同步目录: d_a -> d_b
        """
        self.add_dir_lt = []  # 增加的目录列表
        self.del_dir_lt = []  # 删除的目录列表
        self.add_file_lt = []      # 增加的文件列表
        self.edit_file_lt = []     # 修改的文件列表
        self.del_file_lt = []      # 删除的文件列表
        self.dir_origin = d_a      # 原始目录
        self.dir_target = d_b      # 目标目录

        start_compare_time = time.time()
        self.compare_directory(d_a=d_a, d_b=d_b)
        end_compare_time = time.time()

        print('---> 比较目录时长花费: {} 秒\n'.format(round(end_compare_time - start_compare_time, 2)))

        flag = self.show_tip_ask()    # 显示操作并询问是否继续
        if flag == 'yes':
            start_op_time = time.time()
            self.start_operation()
            end_op_time = time.time()
            print('---> 执行操作花费: {} 秒'.format(round(end_op_time - start_op_time, 2)))

        elif flag == 'useless':
            print(' 两个目录已经是相同的啦, 您不需要再进行操作~~~')
        else:
            print('您取消了操作...')


    # 比较目录差别
    def compare_directory(self, d_a:str, d_b:str):
        d_a_set = set(os.listdir(d_a))
        d_b_set = set(os.listdir(d_b))

        # a目录比 b 目录多的, 目录 b 待添加项
        d_a_more_item_lt = []
        # b目录比 a 目录多的
        d_a_more_item_lt = []
        # 相同的部分需要比较文件大小等, 有可能进行了修改
        path_same_item_lt = []

        d_a_more_item_lt = list(d_a_set - d_b_set)
        d_b_more_item_lt = list(d_b_set - d_a_set)
        path_same_item_lt = list(d_a_set & d_b_set)

        # 处理 a 目录多的
        for item in d_a_more_item_lt:
            item_path = '{}/{}'.format(d_a, item)
            if os.path.isdir(item_path):  
                # 如果是目录, 那么无疑该目录下的所有文件都是要添加的
                self.add_dir_lt.append(item_path.replace(self.dir_origin, self.dir_target))
                self.add_all_director_item(item_path, True)
            else:
                self.add_file_lt.append(item_path)

        # 处理 b 目录多的
        for item in d_b_more_item_lt:
            item_path = '{}/{}'.format(d_b, item)
            if os.path.isdir(item_path):  
                # 如果是目录, 那么无疑该目录下的所有文件都是要添加的
                self.del_dir_lt.append(item_path)
                self.add_all_director_item(item_path, False)
            else:
                self.del_file_lt.append(item_path)

        # 处理一样的
        for item in path_same_item_lt:
            item_a_path = '{}/{}'.format(d_a, item)
            item_b_path = '{}/{}'.format(d_b, item)
            if os.path.isdir(item_a_path):  
                # 如果是目录, 那么递归处理
                self.compare_directory(d_a=item_a_path, d_b=item_b_path)
            else:
                time_a = os.path.getmtime(item_a_path)
                time_b = os.path.getmtime(item_b_path)
                if os.path.getsize(item_a_path) == os.path.getsize(item_b_path) and \
                    abs(time_a - time_b) <= 2:
                    # 两个文件一样大, 如果修改时间相差小于2秒
                    pass
                else:
                    self.edit_file_lt.append([item_a_path, item_b_path])


    # 将该目录下的所有目录和文件添加到待创建和待复制的任务列表中
    def add_all_director_item(self, dir_path:str, is_add:bool):
        for item in os.listdir(dir_path):
            item_path = '{}/{}'.format(dir_path, item)
            if os.path.isdir(item_path):
                if is_add:
                    self.add_dir_lt.append(item_path.replace(self.dir_origin, self.dir_target))
                self.add_all_director_item(item_path, is_add)
            else:
                if is_add:
                    self.add_file_lt.append(item_path)
                else:
                    self.del_file_lt.append(item_path)

    # 展示即将要进行的操作以及询问是否继续
    def show_tip_ask(self):
        print('原始目录: ', self.dir_origin)
        print('目标目录: ', self.dir_target)
        
        if len(self.add_dir_lt) == 0 and len(self.del_dir_lt) == 0 and \
            len(self.add_file_lt) == 0 and len(self.del_file_lt) == 0 and \
                len(self.edit_file_lt) == 0:
            return 'useless'   # 没有必要更新, 两个目录相同
        print('执行完操作后 目标目录 将与 原始目录一样\n')
        self.print_operation_lt(self.add_dir_lt, '要创建的目录')
        self.print_operation_lt(self.del_dir_lt, '要删除的目录')
        self.print_operation_lt(self.add_file_lt, '要复制的文件')
        self.print_operation_lt(self.del_file_lt, '要删除的文件')
        self.print_operation_lt(self.edit_file_lt, '要修改的文件')

        choice = input('请您仔细查看后，确认是否继续操作(y/n)')
        if choice.isalpha() and choice.lower() == 'y':
            return 'yes'
        return 'false'
        

    # 更好的打印项目提示
    def print_operation_lt(self, lt:list, tip:str):
        if len(lt) > 0:
            print(' {} '.format(tip).center(50, '-'))
            for item in lt:
                if isinstance(item , list): # 修改文件
                    print(' {} -> {}'.format(item[0], item[1]))
                else:
                    print(' ' * 4, item)
            print()


    # 开始执行操作
    def start_operation(self):
        print('\n ^_^开始操作...')

        if len(self.add_dir_lt) > 0:
            print('正在创建目录...')
            for item in tqdm(self.add_dir_lt):
                os.makedirs(item)
            print()

        
        if len(self.add_file_lt) > 0:
            print('正在复制文件...')
            for item in tqdm(self.add_file_lt):
                item_target = item.replace(self.dir_origin, self.dir_target)
                shutil.copyfile(item, item_target)
                # 设置文件的访问时间和修改时间
                self.set_a_m_time(item, item_target)
            print()
        
        if len(self.del_file_lt) > 0:
            print('正在删除文件...')
            for item in tqdm(self.del_file_lt):
                os.remove(item)
            print()

        if len(self.edit_file_lt) > 0:
            print('正在修改文件...')
            for item in tqdm(self.edit_file_lt):
                os.remove(item[1])
                shutil.copyfile(item[0], item[1])
                # 设置文件的访问时间和修改时间
                self.set_a_m_time(item[0], item[1])
            print()

        if len(self.del_dir_lt) > 0:
            print('正在删除目录...')
            for item in tqdm(self.del_dir_lt):
                shutil.rmtree(item)
        print(' 执行结束 done!')

    # 设置文件的访问时间和修改时间
    def set_a_m_time(self, item_o, item_t):
        # 设置它们的修改时间一样
        st_item_o = os.stat(item_o)
        os.utime(item_t, (st_item_o.st_atime, st_item_o.st_mtime))


if __name__ == '__main__':
    # 想要被备份的目录 (后者会被前者覆盖)
    dir_pair = [
        r'C:\Users\Jinjin\OneDrive\Pictures\Screenshots', r'I:\tmp'
    ]


    # 开始操作
    _ = Sync(dir_pair[0], dir_pair[1])

