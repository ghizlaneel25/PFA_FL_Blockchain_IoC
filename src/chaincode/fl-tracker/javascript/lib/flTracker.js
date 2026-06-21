'use strict';

const { Contract } = require('fabric-contract-api');

class FLTrackerContract extends Contract {

    async InitLedger(ctx) {
        console.info('Ledger FL-Tracker initialisé');
        return;
    }

    async RecordExchange(ctx, round, clientEmetteur, clientDestinataire, hashPoids, modeType, timestamp) {
        const txId = ctx.stub.getTxID();

        const transaction = {
            docType: 'flExchange',
            txId: txId,
            round: parseInt(round),
            clientEmetteur: clientEmetteur,
            clientDestinataire: clientDestinataire,
            hashPoids: hashPoids,
            modeType: modeType,
            timestamp: timestamp,
            submittingMSP: ctx.clientIdentity.getMSPID(),
            submittingID: ctx.clientIdentity.getID()
        };

        await ctx.stub.putState(txId, Buffer.from(JSON.stringify(transaction)));

        return JSON.stringify(transaction);
    }

    async GetTransaction(ctx, txId) {
        const data = await ctx.stub.getState(txId);
        if (!data || data.length === 0) {
            throw new Error(`Transaction ${txId} introuvable`);
        }
        return data.toString();
    }

    async GetAllTransactions(ctx) {
        const allResults = [];
        const iterator = await ctx.stub.getStateByRange('', '');
        let result = await iterator.next();
        while (!result.done) {
            const strValue = Buffer.from(result.value.value.toString()).toString('utf8');
            let record;
            try {
                record = JSON.parse(strValue);
            } catch (err) {
                record = strValue;
            }
            if (record.docType === 'flExchange') {
                allResults.push(record);
            }
            result = await iterator.next();
        }
        await iterator.close();
        return JSON.stringify(allResults);
    }

    async GetTransactionsByRound(ctx, round) {
        const allTx = JSON.parse(await this.GetAllTransactions(ctx));
        const filtered = allTx.filter(tx => tx.round === parseInt(round));
        return JSON.stringify(filtered);
    }

    async GetTransactionsByClient(ctx, clientId) {
        const allTx = JSON.parse(await this.GetAllTransactions(ctx));
        const filtered = allTx.filter(tx =>
            tx.clientEmetteur === clientId || tx.clientDestinataire === clientId
        );
        return JSON.stringify(filtered);
    }
}

module.exports = FLTrackerContract;
