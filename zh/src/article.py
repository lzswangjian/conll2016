# -*- coding: utf-8 -*-
__author__ = "Sheng Li"
import sys

from sentence import Sentence
from relation import Relation
from common import DEV_RAW_PATH
from collections import defaultdict

logs = sys.stderr


class Article(object):
    __slots__ = ('id', 'params', 'sentences', 'paragraphs', 'disc_connectives',
                 'entity_relations', 'relations', 'exp_disc_conns', 'implicit_relations', 'real_inter_relations',
                 'real_intra_relations', 'auto_inter_relations', 'auto_intra_relations', 'exp_relations',
                 'nonexp_relations', 'auto_exp_relations', 'auto_nonexp_relations', 'auto_all_relations', 'raw_text_path')

    def __init__(self, name, params):
        self.id = name
        self.params = params  # configs of article

        self.sentences = params['sens']
        self.relations = params['rels']
        self.paragraphs = []

        # explicit-implicit relations
        self.disc_connectives = []
        self.exp_relations = []
        self.nonexp_relations = []

        self.auto_exp_relations = []
        self.auto_nonexp_relations = []

        # auto all relations
        self.auto_all_relations = []

    def read_raw_text(self, raw_text_path):
        characters = ''.join(open(raw_text_path).readlines())
        begin = 0  # each article begins with ".START"
        pid = 0
        while 1:
            pc = characters.find('\n\n', begin)
            if pc == -1:
                break
            self.paragraphs.append(Paragraph(begin, pc, pid))
            pid += 1
            begin = pc + 2  # '\n\n'

        for sen in self.sentences:
            flag = False
            for para in self.paragraphs:
                if sen.begin_offset >= para.begin_offset and sen.end_offset <= para.end_offset:
                    para.sentences.append(sen)
                    flag = True
                    break
            if not flag:
                print >> logs, 'sentence outof paragraph'

    def set_article_level_word_id(self):
        idx = 0
        for sen in self.sentences:
            word_ids = []
            if len(sen.words) == 0:
                print >> logs, 'aritcle:%s sentence %s contains no words' % (self.id, sen.id)
            for w in sen.words:
                word_ids.append(idx)
                idx += 1
            sen.word_ids = word_ids

            if len(sen.leaves) > 0:
                for leaf, wid in zip(sen.leaves, sen.word_ids):
                    leaf.leaf_id = wid

    def has_exp_inter_relation(self, idx):
        sid1 = self.sentences[idx].id
        sid2 = self.sentences[idx+1].id

        for rel in self.exp_relations:
            if rel.arg1_sid == sid1 and rel.arg2_sid == sid2:
                return True
        return False

    def has_exp_intra_relation(self, idx):
        sid1 = self.sentences[idx].id
        for rel in self.exp_relations:
            if rel.arg1_sid == sid1 and rel.arg2_sid == sid1:
                return True
        return False

    def has_inter_relation(self, idx):
        sid1 = self.sentences[idx].id
        sid2 = self.sentences[idx+1].id

        for rel in self.relations:
            if sid1 in rel.arg1_sid and sid2 in rel.arg2_sid:
                return True
        return False

    # only for auto parsed explicit relations
    def remove_confilict_relations(self):
        checked = defaultdict(list)
        for idx, rel in enumerate(self.exp_relations):
            len_of_conn = len(rel.conn_leaves)
            for leaf in rel.conn_leaves:
                checked[leaf.leaf_id].append((idx, len_of_conn))

        removed = set()
        for lid in checked:
            if len(checked[lid]) > 1:
                candidate = sorted(checked[lid], key=lambda x:x[1], reverse=True)
                for t in candidate[1:]:
                    removed.add(t[0])

        if len(removed) > 0:
            print >> sys.stderr, 'article has confilict connectives'
            self.exp_relations = [rel for idx, rel in enumerate(self.exp_relations) if idx not in removed]


if __name__ == '__main__':
    art = Article('wsj_2200', {})
    raw_path = DEV_RAW_PATH + '/wsj_2200'
    art.read_raw_text(raw_path)
