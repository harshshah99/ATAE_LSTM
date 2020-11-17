# -*- coding: utf-8 -*-
# file: atae-lstm
# author: songyouwei <youwei0314@gmail.com>
# Copyright (C) 2018. All Rights Reserved.
from layers.attention import Attention, NoQueryAttention
from layers.dynamic_rnn import DynamicLSTM
import torch
import torch.nn as nn

from layers.squeeze_embedding import SqueezeEmbedding


class ATAE_LSTM(nn.Module):
    def __init__(self, embedding_matrix, opt):
        super(ATAE_LSTM, self).__init__()
        self.opt = opt
        self.embed = nn.Embedding.from_pretrained(torch.tensor(embedding_matrix, dtype=torch.float))
        self.squeeze_embedding = SqueezeEmbedding()
        self.lstm = DynamicLSTM(opt.embed_dim*2, opt.hidden_dim, num_layers=1, batch_first=True)
        self.attention = NoQueryAttention(opt.hidden_dim+opt.embed_dim, score_function='bi_linear')
        self.dense = nn.Linear(opt.hidden_dim, opt.polarities_dim)

    def forward(self, inputs):
        text_raw_indices, aspect_indices = inputs[0], inputs[1]
        #print("text_raw_indices \n\n\n\n\n\n",text_raw_indices )
        print("text_raw_indices  SHAPE : \n\n\n\n\n\n",text_raw_indices.shape )
        #print("aspect_indices \n\n\n\n\n\n",aspect_indices )
        print("aspect_indices  SHAPE : \n\n\n\n\n\n",aspect_indices.shape )

        x_len = torch.sum(text_raw_indices != 0, dim=-1)
        #print("X length \n\n" , x_len.shape)
        x_len_max = torch.max(x_len)
        print("Max length \n\n\n " , x_len_max)
        aspect_len = torch.tensor(torch.sum(aspect_indices != 0, dim=-1), dtype=torch.float).to(self.opt.device)


        x = self.embed(text_raw_indices)
        x = self.squeeze_embedding(x, x_len)
        aspect = self.embed(aspect_indices)
        aspect_pool = torch.div(torch.sum(aspect, dim=1), aspect_len.view(aspect_len.size(0), 1))
        aspect = torch.unsqueeze(aspect_pool, dim=1).expand(-1, x_len_max, -1)
        print("LOOOK HERE \n\n\n\n" , torch.sum(aspect) )
        print("\n\n\n")

        x = torch.cat((aspect, x), dim=-1)


        h, (_, _) = self.lstm(x, x_len)
        ha = torch.cat((h, aspect), dim=-1)
        #print("Hidden Representation Shape : " , ha.shape)
        _, score = self.attention(ha)
        #print("Attention Score Shape ------- ", score.shape)
        print("Attention weights  : " , score)

        output = torch.squeeze(torch.bmm(score, h), dim=1)

        out = self.dense(output)
        return out
