import torch
import torch.optim as optim
from torch.utils.data import DataLoader

from tqdm import tqdm

from data import DataReader, ModelDataset
from skipgram import SkipGramModel
from prepare_data import AminerDataset


class Metapath2Vec:
    def __init__(self, path="data", min_count=5, care_type=0, window_size=5, batch_size=50, num_workers=3, dim=128, iterations=15, initial_lr=0.02, output_file="data.embedding"):
        dataset = AminerDataset(path)

        self.data = DataReader(dataset, min_count, care_type)
        dataset = ModelDataset(self.data, window_size)
        self.dataloader = DataLoader(dataset, batch_size=batch_size,
                                     shuffle=True, num_workers=num_workers, collate_fn=dataset.collate)

        self.output_file_name = output_file
        self.emb_size = len(self.data.word2id)
        self.emb_dimension = dim
        self.batch_size = batch_size
        self.iterations = iterations
        self.initial_lr = initial_lr
        self.skip_gram_model = SkipGramModel(self.emb_size, self.emb_dimension)

        self.use_cuda = torch.cuda.is_available()
        self.device = torch.device("cuda" if self.use_cuda else "cpu")
        if self.use_cuda:
            self.skip_gram_model.cuda()

    def train(self):

        optimizer = optim.SparseAdam(
            list(self.skip_gram_model.parameters()), lr=self.initial_lr)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, len(self.dataloader))

        for iteration in range(self.iterations):
            print("\n\n\nIteration: " + str(iteration + 1))
            running_loss = 0.0
            for i, sample_batched in enumerate(tqdm(self.dataloader)):

                if len(sample_batched[0]) > 1:
                    pos_u = sample_batched[0].to(self.device)
                    pos_v = sample_batched[1].to(self.device)
                    neg_v = sample_batched[2].to(self.device)

                    scheduler.step()
                    optimizer.zero_grad()
                    loss = self.skip_gram_model.forward(pos_u, pos_v, neg_v)
                    loss.backward()
                    optimizer.step()

                    running_loss = running_loss * 0.9 + loss.item() * 0.1
                    if i > 0 and i % 500 == 0:
                        print(" Loss: " + str(running_loss))

        self.skip_gram_model.save_embedding(
            self.data.id2word, self.output_file_name)


if __name__ == '__main__':
    m2v = Metapath2Vec()
    m2v.train()
