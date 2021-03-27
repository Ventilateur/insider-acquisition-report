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

        self._is_acquire = _get_val(amounts, "transactionAcquiredDisposedCode/value") == "A"
        self._is_equity_swap = _get_val(element, "transactionCoding/equitySwapInvolved", allow_missing=True) == "1"

        if not self._is_acquire or self._is_equity_swap or self.price_per_share == 0:
            raise UnneededDataException(
                "Transaction is not an acquisition, is an equity swap, or does not have price per share"
            )

    def to_dict(self):
        return {
            "nb_shares": self.nb_shares,
            "price": self.price_per_share,
            "date": self.date,
            "security_title": self.security_title
        }


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

    def __init__(self, element, form_url):
        self.form_url = form_url
        self.company = f"{_get_val(element, 'issuer/issuerName')} ({_get_val(element, 'issuer/issuerTradingSymbol')})"
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

    def to_dict(self):
        return {
            "company": self.company,
            "insiders": [str(insider) for insider in self.insiders],
            "transactions": [transaction.to_dict() for transaction in self.transactions],
            "sec4_file": self.form_url
        }
