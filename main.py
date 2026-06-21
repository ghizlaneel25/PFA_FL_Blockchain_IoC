import os
import warnings
import tenseal as ts
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import torch  
import matplotlib.pyplot as plt
import hashlib
from datetime import datetime
import json

from model import CNN_LSTM
from utils import separation_iid, separation_non_iid, entrainer_client_local, evaluer_modele
from fabric_connector import FabricConnector

print("=== Chargement du dataset ===")
data_path = "data/02-14-2018.csv"
df = pd.read_csv(data_path, nrows=100000)
print(f"Shape brut : {df.shape}")

df.replace([np.inf, -np.inf], np.nan, inplace=True)
df.dropna(inplace=True)
df.columns = df.columns.str.strip()

if 'Protocol' in df.columns:
    try:
        df['Protocol'] = pd.to_numeric(df['Protocol'])
    except ValueError:
        le = LabelEncoder()
        df['Protocol'] = le.fit_transform(df['Protocol'].astype(str))

cols_a_supprimer = [col for col in ['Label', 'Timestamp', 'Flow ID', 'Src IP', 'Dst IP', 'Src Port', 'Dst Port'] if col in df.columns]
X = df.drop(cols_a_supprimer, axis=1).values
y = LabelEncoder().fit_transform(df['Label'].values)
X = StandardScaler().fit_transform(X)

input_size = X.shape[1]
num_classes = len(np.unique(y))
print(f"Features: {input_size}, Classes: {num_classes}, Samples: {len(X)}")

print("\n=== Partitionnement IID ===")
donnees_iid = separation_iid(X, y, n_clients=4)
for i, (Xc, yc) in enumerate(donnees_iid):
    print(f"Client {i+1}: {len(Xc)} samples, classes: {np.unique(yc, return_counts=True)[1]}")

print("\n=== Partitionnement Non-IID (Dirichlet α=0.5) ===")
donnees_non_iid = separation_non_iid(X, y, n_clients=4, alpha=0.5)
for i, (Xc, yc) in enumerate(donnees_non_iid):
    print(f"Client {i+1}: {len(Xc)} samples, classes: {np.unique(yc, return_counts=True)[1]}")

def run_fl(donnees_clients, mode_type, fabric_connector):
    modeles = [CNN_LSTM(input_size, num_classes) for _ in range(4)]
    clients_data_split = []
    for Xc, yc in donnees_clients:
        n = min(5000, len(Xc))
        X_tr, X_te, y_tr, y_te = train_test_split(
            Xc[:n], yc[:n], test_size=0.2, stratify=yc[:n], random_state=42
        )
        clients_data_split.append((X_tr, y_tr, X_te, y_te))
    f1_history = []
    
    # Contexte TenSEAL
    contexte_tenseal = ts.context(
        ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=[60, 40, 40, 60]
    )
    contexte_tenseal.global_scale = 2**40
    contexte_tenseal.generate_galois_keys()

    for round_num in range(1, 11):
        print(f"\n--- Round {round_num} ({mode_type}) ---")
        use_dp = (round_num > 3)
        if use_dp:
            print("  🔐 Activation de Differential Privacy (Opacus)")
        
        for i in range(4):
            X_tr, y_tr, _, _ = clients_data_split[i]
            n_eff = 2000 if use_dp else 5000
            X_tr_eff = X_tr[:n_eff]
            y_tr_eff = y_tr[:n_eff]
            # Récupérer le modèle (peut être réinitialisé si DP)
            modeles[i] = entrainer_client_local(modeles[i], X_tr_eff, y_tr_eff, epochs=3, use_dp=use_dp)

        tous_les_poids = [modele.state_dict() for modele in modeles]

        for i in range(4):
            poids_moyen = {}
            for key in tous_les_poids[0].keys():
                poids_moyen[key] = torch.stack([p[key] for p in tous_les_poids]).mean(dim=0)
            modeles[i].load_state_dict(poids_moyen)

            poids_flat = torch.cat([p.flatten() for p in poids_moyen.values()]).numpy()
            hash_poids = hashlib.sha256(poids_flat[:1000].tobytes()).hexdigest()

            # TenSEAL : chiffrement des 50 premiers poids (démonstration)
            poids_chiffres = ts.ckks_vector(contexte_tenseal, poids_flat[:50].tolist())

            try:
                tx = fabric_connector.enregistrer_echange(
                    round_num=round_num,
                    emetteur="Reseau",
                    destinataire=f"Client{i+1}",
                    hash_poids=hash_poids,
                    mode_type=mode_type,
                    timestamp=datetime.now().isoformat()
                )
                print(f"  ✅ Transaction enregistrée pour Client {i+1}")
            except Exception as e:
                print(f"  ❌ Erreur Fabric pour Client {i+1}: {e}")

        f1_round = []
        for i in range(4):
            _, _, X_te, y_te = clients_data_split[i]
            f1, acc = evaluer_modele(modeles[i], X_te, y_te)
            f1_round.append(f1)
            print(f"  Client {i+1} - F1: {f1:.4f} | Acc: {acc:.4f}")

        f1_moyen = np.mean(f1_round)
        f1_history.append(f1_moyen)
        print(f"  → F1 moyen du round: {f1_moyen:.4f}")

    return f1_history

fabric = FabricConnector("/home/kali/fabric-project/fabric-samples/test-network")

print("\n\n========== EXÉCUTION IID ==========")
f1_iid = run_fl(donnees_iid, "IID", fabric)

print("\n\n========== EXÉCUTION NON-IID ==========")
f1_non_iid = run_fl(donnees_non_iid, "NonIID", fabric)

print("\n\n=== Historique des transactions depuis Fabric ===")
try:
    historique = fabric.get_all_transactions()
    print(f"{len(historique)} transactions trouvées.")
    print(json.dumps(historique[:3], indent=2))
except Exception as e:
    print(f"Erreur requête: {e}")

plt.figure(figsize=(10,6))
plt.plot(range(1,11), f1_iid, 'b-o', label='IID')
plt.plot(range(1,11), f1_non_iid, 'r-s', label='Non-IID')
plt.xlabel('Round FL')
plt.ylabel('F1-score macro')
plt.title('Comparaison IID vs Non-IID avec Blockchain Fabric')
plt.legend()
plt.grid(True, alpha=0.3)
plt.ylim(0, 1.05)
plt.savefig('comparaison_iid_non_iid.png', dpi=150)
print("\n✅ Graphique sauvegardé sous 'comparaison_iid_non_iid.png'")

print("\n=== FIN DU SCRIPT ===")
