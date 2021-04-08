import json
from typing import List

from scrape.exceptions import MissingDataException, UnneededDataException


def _get_val(element, path, allow_missing=False):
    e = element.find(path)
    if e is None:
        if allow_missing:
            return None
        else:
            raise MissingDataException(path)
    return e.text


def _get_sub_elem(element, path):
    e = element.find(path)
    if e is None:
        raise MissingDataException(path)
    return e


def _list_elem(element, path):
    es = element.findall(path)
    if len(es) == 0:
        raise MissingDataException(path)
    return es


class Transaction:
    def __init__(self, element):
        self.date = _get_val(element, "transactionDate/value")
        self.security_title = _get_val(element, "securityTitle/value")

        amounts = _get_sub_elem(element, "transactionAmounts")
        self.nb_shares = int(float(_get_val(amounts, "transactionShares/value")))
        self.price_per_share = float(_get_val(amounts, "transactionPricePerShare/value"))
        self.total_amount = self.price_per_share * self.nb_shares
        self.is_acquire = _get_val(amounts, "transactionAcquiredDisposedCode/value") == "A"

        self._is_equity_swap = _get_val(element, "transactionCoding/equitySwapInvolved", allow_missing=True) == "1"
        if self._is_equity_swap or self.price_per_share == 0:
            raise UnneededDataException(
                "Transaction is an equity swap, or does not have price per share"
            )


class Insider:
    def __init__(self, element):
        self.name = _get_val(element, "reportingOwnerId/rptOwnerName")

        insider_relationship = _get_sub_elem(element, "reportingOwnerRelationship")
        self._is_director = _get_val(insider_relationship, "isDirector", allow_missing=True) == "1"
        self._is_officer = _get_val(insider_relationship, "isOfficer", allow_missing=True) == "1"
        self._is_ten_pc_owner = _get_val(insider_relationship, "isTenPercentOwner", allow_missing=True) == "1"
        self._officer_title = _get_val(insider_relationship, "officerTitle", allow_missing=True)
        self._other_text = _get_val(insider_relationship, "otherText", allow_missing=True)

        self.title = self.build_title()

    def build_title(self):
        title = ", ".join(filter(None, [self._officer_title, self._other_text]))
        if not title:
            title = ", ".join(filter(None, [
                "Director" if self._is_director else None,
                "Officer" if self._is_officer else None,
                "10% owner" if self._is_ten_pc_owner else None
            ]))
        return title if title else "N/A"

    def __str__(self):
        return f"{self.name} ({self.title})"


class SEC4Data:
    xml_root = "ownershipDocument"

    def __init__(self, element, sec4_file_loc):
        self.sec4_file_loc = sec4_file_loc
        self.company_code = _get_val(element, 'issuer/issuerTradingSymbol')
        self.company_name = _get_val(element, 'issuer/issuerName')
        self.insiders = []
        self.transactions = []

        insider_elements = _list_elem(element, "reportingOwner")
        for insider_element in insider_elements:
            try:
                insider = Insider(insider_element)
                self.insiders.append(insider)
            except (MissingDataException, UnneededDataException):
                pass

        transaction_elements = _list_elem(element, "nonDerivativeTable/nonDerivativeTransaction")
        for transaction_element in transaction_elements:
            try:
                transaction = Transaction(transaction_element)
                self.transactions.append(transaction)
            except (MissingDataException, UnneededDataException):
                pass

        if len(self.transactions) == 0:
            raise UnneededDataException("No needed transaction")

    def flatten(self, file_date: str) -> List[List]:
        return [
            [
                transaction.date,
                self.company_code,
                self.company_name,
                json.dumps([str(insider) for insider in self.insiders]),
                'B' if transaction.is_acquire else 'S',
                transaction.price_per_share,
                transaction.nb_shares,
                transaction.security_title,
                self.sec4_file_loc,
                file_date
            ]
            for transaction in self.transactions
        ]
