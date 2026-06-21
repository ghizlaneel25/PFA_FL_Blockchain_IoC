# 🔐 Détection d'IoC par Apprentissage Fédéré Décentralisé sur Blockchain

## 📌 Description

Projet de détection d'attaques réseau par Indicateurs de Compromission (IoC) combinant :
- Modèle CNN-LSTM
- Apprentissage fédéré décentralisé P2P
- Blockchain Hyperledger Fabric
- Sécurité : TenSEAL + Opacus

## 📊 Résultats

| Scénario | F1 IID | F1 Non-IID | ε (Opacus) |
|----------|--------|------------|------------|
| Sans sécurité | 1.0000 | 1.0000 | — |
| TenSEAL uniquement | 1.0000 | 1.0000 | — |
| Opacus (ε=0.9) | 0.4996 | 0.6243 | 0.9063 |
| Opacus (ε=0.49) | 0.4996 | 0.6243 | 0.4902 |

## 🏗️ Architecture

4 clients → Apprentissage local → Agrégation P2P → Blockchain Fabric (traçabilité)

## 👥 Équipe

- Abiza Fadwa
- El Aouni Ghizlane
- El Kadiri Boutchich Radia

Encadré par **Prof. Mohammed Ouadoud** et **M. Oussama Bouzerda**

## 📄 Licence

MIT
