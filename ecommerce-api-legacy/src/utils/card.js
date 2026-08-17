function isApprovedTestCard(cardNumber) {
    return typeof cardNumber === 'string' && cardNumber.startsWith('4');
}

module.exports = { isApprovedTestCard };
