import subprocess
import json
import os

class FabricConnector:
    def __init__(self, test_network_path):
        self.path = test_network_path
        self.env = os.environ.copy()
        self.env['PATH'] = f"{self.path}/../bin:" + self.env.get('PATH', '')
        self.env['FABRIC_CFG_PATH'] = f"{self.path}/../config/"
        self.env['CORE_PEER_TLS_ENABLED'] = 'true'
        self.env['CORE_PEER_LOCALMSPID'] = 'Org1MSP'
        self.env['CORE_PEER_TLS_ROOTCERT_FILE'] = f"{self.path}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt"
        self.env['CORE_PEER_MSPCONFIGPATH'] = f"{self.path}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp"
        self.env['CORE_PEER_ADDRESS'] = 'localhost:7051'

    def enregistrer_echange(self, round_num, emetteur, destinataire, hash_poids, mode_type, timestamp):
        cmd = [
            'peer', 'chaincode', 'invoke',
            '-o', 'localhost:7050',
            '--ordererTLSHostnameOverride', 'orderer.example.com',
            '--tls',
            '--cafile', f"{self.path}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem",
            '-C', 'mychannel',
            '-n', 'fltracker',
            '--peerAddresses', 'localhost:7051',
            '--tlsRootCertFiles', f"{self.path}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt",
            '--peerAddresses', 'localhost:9051',
            '--tlsRootCertFiles', f"{self.path}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt",
            '-c', json.dumps({
                'function': 'RecordExchange',
                'Args': [str(round_num), str(emetteur), str(destinataire), str(hash_poids), str(mode_type), str(timestamp)]
            })
        ]
        result = subprocess.run(cmd, env=self.env, capture_output=True, text=True, cwd=self.path)
        if result.returncode != 0:
            raise Exception(f"Erreur invocation: {result.stderr}")
        try:
            payload = result.stdout.split('payload:')[1].strip()
            return json.loads(payload)
        except:
            return result.stdout

    def get_all_transactions(self):
        cmd = [
            'peer', 'chaincode', 'query',
            '-C', 'mychannel',
            '-n', 'fltracker',
            '-c', json.dumps({'function': 'GetAllTransactions', 'Args': []})
        ]
        result = subprocess.run(cmd, env=self.env, capture_output=True, text=True, cwd=self.path)
        if result.returncode != 0:
            raise Exception(f"Erreur requête: {result.stderr}")
        return json.loads(result.stdout.strip())
