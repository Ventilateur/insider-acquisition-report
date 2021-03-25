from typing import List

from exceptions import MissingDataException, UnneededDataException


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
        self.nb_shares = float(_get_val(amounts, "transactionShares/value"))
        self.price_per_share = float(_get_val(amounts, "transactionPricePerShare/value"))
        self.total_amount = int(self.price_per_share * self.nb_shares)

        self._is_acquire = _get_val(amounts, "transactionAcquiredDisposedCode/value") == "A"
        self._is_equity_swap = _get_val(element, "transactionCoding/equitySwapInvolved", allow_missing=True) == "1"

        if not self._is_acquire or self._is_equity_swap or self.price_per_share == 0:
            raise UnneededDataException(
                "Transaction is not an acquisition, is an equity swap, or does not have price per share"
            )


class Insider:
    def __init__(self, element):
        self.name = _get_val(element, "reportingOwner/reportingOwnerId/rptOwnerName")

        insider_relationship = _get_sub_elem(element, "reportingOwner/reportingOwnerRelationship")
        self.is_director = _get_val(insider_relationship, "isDirector", allow_missing=True) == "1"
        self.is_officer = _get_val(insider_relationship, "isOfficer", allow_missing=True) == "1"
        self.is_ten_pc_owner = _get_val(insider_relationship, "isTenPercentOwner", allow_missing=True) == "1"

        self._officer_title = _get_val(insider_relationship, "officerTitle", allow_missing=True)
        self._other_text = _get_val(insider_relationship, "otherText", allow_missing=True)
        self.title = self.build_title()

    def build_title(self):
        title = ", ".join(filter(None, [self._officer_title, self._other_text]))
        return title if title else "N/A"


class SEC4Data:
    xml_root = "ownershipDocument"

    def __init__(self, element, form_url):
        self.form_url = form_url
        self.company = _get_val(element, "issuer/issuerName")
        self.company_code = _get_val(element, "issuer/issuerTradingSymbol")
        self.insider = Insider(element)
        self.transactions = []

        sub_elements = _list_elem(element, "nonDerivativeTable/nonDerivativeTransaction")
        for sub_elem in sub_elements:
            try:
                transaction = Transaction(sub_elem)
                self.transactions.append(transaction)
            except (MissingDataException, UnneededDataException):
                pass

        if len(self.transactions) == 0:
            raise UnneededDataException("No needed transaction")

    def to_list(self) -> List[List]:
        result = []
        for transaction in self.transactions:
            result.append(
                [
                    self.company,
                    self.company_code,
                    self.insider.name,
                    self.insider.title,
                    "Yes" if self.insider.is_director else "No",
                    "Yes" if self.insider.is_officer else "No",
                    "Yes" if self.insider.is_ten_pc_owner else "No",
                    f"{transaction.total_amount}$",
                    transaction.nb_shares,
                    f"{transaction.price_per_share}$",
                    transaction.date,
                    transaction.security_title,
                    self.form_url
                ]
            )
        return result
