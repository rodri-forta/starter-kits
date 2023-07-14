"""Forta agent scanning for batched transactions"""

from web3 import Web3
from forta_agent import get_json_rpc_url, FindingSeverity
from forta_agent.transaction_event import TransactionEvent

import src.options as options
import src.disperse as disperse
import src.findings as findings
import src.multisend as multisend

# CONSTANTS ###################################################################

ADDRESS_TO_NAME = {
    disperse.ADDRESS.lower(): 'Disperse',
    multisend.ADDRESS.lower(): 'Multisend'}

# SCANNER #####################################################################

def handle_transaction_factory(w3: Web3, token: str=options.TARGET_TOKEN) -> callable:
    _chain_id = w3.eth.chain_id
    _parsers = { # input data parsers for each target contract
        disperse.ADDRESS.lower(): disperse.parse_transaction_input_factory(w3=w3, token=token),
        multisend.ADDRESS.lower(): multisend.parse_transaction_input_factory(w3=w3, token=token)}

    def _handle_transaction(transaction_event: TransactionEvent) -> list:
        _findings = []
        _from = str(getattr(transaction_event.transaction, 'from_', '')).lower()
        _to = str(getattr(transaction_event.transaction, 'to', '')).lower() # could be None in case of a contract creation
        _data = str(getattr(transaction_event.transaction, 'data', '')).lower()
        _wrapped_tx = []
        
        if _to in _parsers and options.TARGET_CONTRACT in _to:
            _token, _wrapped_tx, _is_manual = _parsers[_to](_data)
            if _wrapped_tx:
                _findings.append(findings.FormatBatchTxFinding(
                    origin=_from,
                    contract=ADDRESS_TO_NAME[_to],
                    token=_token,
                    transactions=_wrapped_tx,
                    chain_id=_chain_id,
                    severity=FindingSeverity.Low if _is_manual else FindingSeverity.Info))

        return _findings

    return _handle_transaction

handle_transaction = handle_transaction_factory(w3=Web3(Web3.HTTPProvider(get_json_rpc_url())))
