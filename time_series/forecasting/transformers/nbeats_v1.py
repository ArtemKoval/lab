import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt

# Generate synthetic time series data
def generate_sine_series(seq_len=100):
    x = np.arange(seq_len)
    y = np.sin(0.1 * x) + 0.1 * np.random.randn(seq_len)
    return y

series = generate_sine_series()

# Tokenization: split into windows
def create_sequences(data, input_window=20, output_window=1):
    X, Y = [], []
    for i in range(len(data) - input_window - output_window):
        X.append(data[i:i+input_window])
        Y.append(data[i+input_window:i+input_window+output_window])
    return torch.tensor(X).float(), torch.tensor(Y).float()

input_window = 20
output_window = 1
X, Y = create_sequences(series, input_window, output_window)

# Positional Encoding
class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=500):
        super().__init__()
        pos_encoding = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-np.log(10000.0) / d_model))
        pos_encoding[:, 0::2] = torch.sin(position * div_term)
        pos_encoding[:, 1::2] = torch.cos(position * div_term)
        self.pos_encoding = pos_encoding.unsqueeze(0)

    def forward(self, x):
        return x + self.pos_encoding[:, :x.size(1)]

# Simple Transformer for Time Series
class TimeSeriesTransformer(nn.Module):
    def __init__(self, input_size=1, d_model=64, nhead=4, num_layers=2, dropout=0.1):
        super().__init__()
        self.embedding = nn.Linear(input_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model)
        encoder_layers = nn.TransformerEncoderLayer(d_model, nhead, dim_feedforward=128, dropout=dropout)
        self.transformer = nn.TransformerEncoder(encoder_layers, num_layers)
        self.decoder = nn.Linear(d_model, 1)

    def forward(self, src):
        src = src.unsqueeze(-1)  # (batch, seq_len, 1)
        x = self.embedding(src)
        x = self.pos_encoder(x)
        x = self.transformer(x)
        return self.decoder(x[:, -1, :])  # use last time step output

# Model, loss, optimizer
model = TimeSeriesTransformer()
loss_fn = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

# Training loop
for epoch in range(100):
    model.train()
    optimizer.zero_grad()
    output = model(X)
    loss = loss_fn(output.squeeze(), Y.squeeze())
    loss.backward()
    optimizer.step()
    if epoch % 10 == 0:
        print(f"Epoch {epoch} Loss: {loss.item():.4f}")

# Plot prediction vs actual
model.eval()
with torch.no_grad():
    pred = model(X).squeeze().numpy()

plt.plot(Y.squeeze().numpy(), label='Actual')
plt.plot(pred, label='Predicted')
plt.legend()
plt.title("Mini Transformer Forecast")
plt.show()
