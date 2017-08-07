# -*- coding: utf-8 -*-
# file: poems.py
# author: JinTian
# time: 08/03/2017 7:39 PM
# Copyright 2017 JinTian. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------
import collections
import os
import sys
import numpy as np

start_token = 'G'
end_token = 'E'


def process_poems(file_name):
    # 诗集
    poems = []
    with open(file_name, "r", encoding='utf-8', ) as f:  # with open方法省去了打开文件的try catch过程，也不用f.close
        for line in f.readlines():
            try:
                title, content = line.strip().split(':')  # 分割古诗title和content
                content = content.replace(' ', '')  # 去掉空格
                # 如果 content 包含了特殊字符'_','(','（','《','[','G','E' 则不处理
                if '_' in content or '(' in content or '（' in content or '《' in content or '[' in content or \
                        start_token in content or end_token in content:
                    continue
                if len(content) < 5 or len(content) > 79:  # 不懂这两个magic number在考虑什么情况，但utf-8中文len=3
                    continue
                content = start_token + content + end_token  # 给内容加上标记
                poems.append(content)  # 保存到list
            except ValueError as e:
                pass
    # 按诗的字数排序
    poems = sorted(poems, key=lambda l: len(l))

    # 统计每个字出现次数
    all_words = []
    for poem in poems:
        # 建议把'G''E'去掉
        #poem = poem.strip('GE')
        #poem = poem.replace('，', '')
        #poem = poem.replace('。', '')
        all_words += [word for word in poem]  # (word for word in poem) 也可
    # 这里根据包含了每个字对应的频率
    counter = collections.Counter(all_words)  # 返回得到的是 Counter({'花': 6, '梦': 5, '春': 5, '归': 4}) 的 KV对
    count_pairs = sorted(counter.items(), key=lambda x: -x[1])
    # lambda x, x对应一个 KV,选择 x[1]就是用value排序,负数是倒序
    # 返回值是[('花', 6), ('梦', 5), ('春', 5), ('处', 4)] 这个映射表应该有用
    words, _ = zip(*count_pairs)
    # unzip words=('花', '梦', '春', '处') _=(6, 5, 5, 4)

    # 取前多少个常用字 words[:x] 现在是全选，但为什么加一个空项？
    words = words[:len(words)] + (' ',)
    # 每个字映射为一个数字ID
    word_int_map = dict(zip(words, range(len(words))))
    # list(map(lambda word: word_int_map.get(word, len(words)), poem)) 为什么取最后一首诗的映射表？
    # [list_x for poem in poems] 总共有多少首诗就做出多少vector
    poems_vector = [list(map(lambda word: word_int_map.get(word, len(words)), poem)) for poem in poems]

    # 返回的是 映射数字列表，映射关系词典，常用字
    return poems_vector, word_int_map, words


def generate_batch(batch_size, poems_vec, word_to_int):
    # 每次取64首诗进行训练
    n_chunk = len(poems_vec) // batch_size
    x_batches = []
    y_batches = []
    for i in range(n_chunk):  # 从0开始
        start_index = i * batch_size
        end_index = start_index + batch_size  # 这里没有减1 是因为list的截取[a:b]取得是 [a:b) 并不包含b

        batches = poems_vec[start_index:end_index]
        # 找到这个batch的所有poem中最长的poem的长度
        length = max(map(len, batches))
        # 填充一个这么大小的空batch，空的地方放空格对应的index标号
        x_data = np.full((batch_size, length), word_to_int[' '], np.int32)
        for row in range(batch_size):
            # 每一行就是一首诗，在原本的长度上把诗还原上去
            x_data[row, :len(batches[row])] = batches[row]
        y_data = np.copy(x_data)
        # y的话就是x向左边也就是前面移动一个
        y_data[:, :-1] = x_data[:, 1:]
        """
        x_data             y_data
        [6,2,4,6,9]       [2,4,6,9,9]
        [1,4,2,8,5]       [4,2,8,5,5]
        """
        x_batches.append(x_data)
        y_batches.append(y_data)
    # 所以最后返回的是每个item等长的列表，item是array形式， x是原始数据，y是左移后的数据
    # 比如x_batches
    # [array([[1, 5, 4, 3, 2, 6, 4, 3, 0]], dtype=int32),
    #  array([[ 1, 11, 18,  7,  8, 20, 14,  9,  0]], dtype=int32),
    #  array([[ 1, 19,  6, 10,  5,  2, 15, 12, 21, 13, 16, 23, 22, 17,  0]], dtype=int32)]
    return x_batches, y_batches
