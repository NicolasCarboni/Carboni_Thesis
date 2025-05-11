// contracts/HashStorage.sol
pragma solidity ^0.8.0;

contract HashStorage {
    bytes32 public storedHash;

    function setHash(bytes32 _hash) public {
        storedHash = _hash;
    }

    function getHash() public view returns (bytes32) {
        return storedHash;
    }
}
