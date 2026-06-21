import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import f1_score
from opacus import PrivacyEngine
from model import CNN_LSTM

def separation_iid(X, y, n_clients=4, seed=42):
    np.random.seed(seed)
    indices = np.random.permutation(len(X))
    split = np.array_split(indices, n_clients)
    return [(X[idx], y[idx]) for idx in split]

def separation_non_iid(X, y, n_clients=4, alpha=0.5, seed=42):
    np.random.seed(seed)
    idx_clients = [[] for _ in range(n_clients)]
    for cls in np.unique(y):
        cls_idx = np.where(y == cls)[0]
        np.random.shuffle(cls_idx)
        proportions = np.random.dirichlet([alpha] * n_clients)
        split_points = np.cumsum(proportions * len(cls_idx)).astype(int)
        split_points = np.append(0, split_points)
        for i in range(n_clients):
            start = split_points[i]
            end = split_points[i+1]
            idx_clients[i].extend(cls_idx[start:end].tolist())
    for i in range(n_clients):
        np.random.shuffle(idx_clients[i])
    return [(X[idx], y[idx]) for idx in idx_clients]

def entrainer_client_local(model, X_train, y_train, epochs=3, lr=0.001, batch_size=128, use_dp=False):
    # Si DP activée, on réinitialise le modèle pour éviter les hooks en double
    if use_dp:
        # Créer un nouveau modèle avec les mêmes dimensions
        model = CNN_LSTM(model.conv[0].in_channels, model.fc[-1].out_features)
    model.train()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = torch.nn.CrossEntropyLoss()
    loader = DataLoader(
        TensorDataset(torch.tensor(X_train, dtype=torch.float32),
                      torch.tensor(y_train, dtype=torch.long)),
        batch_size=batch_size, shuffle=True
    )
    if use_dp:
        privacy_engine = PrivacyEngine()
        model, optimizer, loader = privacy_engine.make_private(
            module=model,
            optimizer=optimizer,
            data_loader=loader,
            noise_multiplier=2.5,
            max_grad_norm=1.0,
        )
    for _ in range(epochs):
        for bX, by in loader:
            optimizer.zero_grad()
            loss = criterion(model(bX), by)
            loss.backward()
            optimizer.step()
    if use_dp:
        epsilon = privacy_engine.get_epsilon(delta=1e-5)
        print(f"  🔒 DP ε = {epsilon:.4f}")
    return model

def evaluer_modele(model, X_test, y_test):
    model.eval()
    with torch.no_grad():
        preds = model(torch.tensor(X_test, dtype=torch.float32)).argmax(dim=1).numpy()
        f1 = f1_score(y_test, preds, average='macro', zero_division=0)
        acc = float((preds == y_test).mean())
    return f1, acc
