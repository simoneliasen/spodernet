from os.path import join

import os
import json

from spodernet.preprocessing.vocab import Vocab

from spodernet.logger import Logger
log = Logger('pipeline.py.txt')

class Pipeline(object):
    def __init__(self, name):
        self.text_processors = []
        self.sent_processors = []
        self.token_processors = []
        self.post_processors = []
        self.paths = []
        home = os.environ['HOME']
        self.root = join(home, '.data', name)
        if not os.path.exists(self.root):
            os.mkdir(self.root)
        self.state = {'name' : name, 'home' : home, 'path' : self.root, 'data' : {}}
        self.state['vocab'] = Vocab(path=self.root)

    def add_text_processor(self, text_processor):
        text_processor.link_with_pipeline(self.state)
        log.debug('Added text preprocessor {0}', type(text_processor))
        self.text_processors.append(text_processor)

    def add_sent_processor(self, sent_processor):
        sent_processor.link_with_pipeline(self.state)
        log.debug('Added sent preprocessor {0}', type(sent_processor))
        self.sent_processors.append(sent_processor)

    def add_token_processor(self, token_processor):
        token_processor.link_with_pipeline(self.state)
        log.debug('Added token preprocessor {0}', type(token_processor))
        self.token_processors.append(token_processor)

    def add_post_processor(self, post_processor):
        post_processor.link_with_pipeline(self.state)
        log.debug('Added post preprocessor {0}', type(post_processor))
        self.post_processors.append(post_processor)

    def add_path(self, path):
        log.debug('Added path to JSON file {0}', path)
        self.paths.append(path)

    def stream_file(self, path):
        log.debug('Processing file {0}'.format(path))
        for line in open(path):
            # we have comma separated files
            inp, support, target = json.loads(line)
            log.statistical('this is some input in text format {0}', inp)
            log.statistical('this is a support in text format {0}', support)
            log.statistical('this is a target in text format {0}', target)
            yield inp, support, target

    def clear_processors(self):
        self.post_processors = []
        self.sent_processors = []
        self.token_processors = []
        self.text_processors = []

    def execute(self):
        '''Tokenizes the data, calcs the max length, and creates a vocab.'''

        for path in self.paths:
            for inp, sup, target in self.stream_file(path):
                for textp in self.text_processors:
                    inp = textp.process(inp, inp_type='input')
                    sup = textp.process(sup, inp_type='support')
                    target = textp.process(target, inp_type='target')

                inp_sents = (inp if isinstance(inp, list) else [inp])
                sup_sents = (sup if isinstance(sup, list) else [sup])
                t_sents = (target if isinstance(target, list) else [target])

                for sentp in self.sent_processors:
                    for i in range(len(inp_sents)):
                        inp_sents[i] = sentp.process(inp_sents[i], inp_type='input')
                    for i in range(len(sup_sents)):
                        sup_sents[i] = sentp.process(sup_sents[i], inp_type='support')
                    for i in range(len(t_sents)):
                        t_sents[i] = sentp.process(t_sents[i], inp_type='target')

                inp_words = (inp_sents if isinstance(inp_sents[0], list) else [[sent] for sent in inp_sents])
                sup_words = (sup_sents if isinstance(sup_sents[0], list) else [[sent] for sent in sup_sents])
                t_words = (t_sents if isinstance(t_sents[0], list) else [[sent] for sent in t_sents])

                for tokenp in self.token_processors:
                    for i in range(len(inp_words)):
                        for j in range(len(inp_words[i])):
                            inp_words[i][j] = tokenp.process(inp_words[i][j], inp_type='input')

                    for i in range(len(sup_words)):
                        for j in range(len(sup_words[i])):
                            sup_words[i][j] = tokenp.process(sup_words[i][j], inp_type='support')

                    for i in range(len(t_words)):
                        for j in range(len(t_words[i])):
                            t_words[i][j] = tokenp.process(t_words[i][j], inp_type='target')

                for postp in self.post_processors:
                    inp_words = postp.process(inp_words, inp_type='input')
                    sup_words = postp.process(sup_words, inp_type='support')
                    t_words = postp.process(t_words, inp_type='target')

        return self.state