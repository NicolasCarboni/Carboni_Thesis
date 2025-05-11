// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract DataFactModel {
    struct Dimensions {
        bool ProductName;
        bool Category;
        bool Supplier;
        bool ExpirationDate;
        bool MonthOfSale;
        bool QuarterOfSale;
        bool BimonthOfSale;
        bool YearOfSale;
        bool City;
        bool Province;
        bool Region;
        bool TypeOfSale;
    }

    Dimensions public allowedDimensions;

    event QueryCheck(address indexed user, string[] queryDimensions);

    constructor() {
        allowedDimensions.ProductName = true;
        allowedDimensions.Category = true;
        allowedDimensions.Supplier = true;
        allowedDimensions.MonthOfSale = true;
        allowedDimensions.QuarterOfSale = true;
        allowedDimensions.BimonthOfSale = true;
        allowedDimensions.YearOfSale = true;
        allowedDimensions.City = true;
        allowedDimensions.Province = true;
        allowedDimensions.Region = true;
        allowedDimensions.TypeOfSale = true;
    }

    function isQueryAllowed(string[] memory queryDimensions) public view returns (bool) {
        for (uint i = 0; i < queryDimensions.length; i++) {
            if (keccak256(abi.encodePacked(queryDimensions[i])) == keccak256(abi.encodePacked("ProductName")) && !allowedDimensions.ProductName) return false;
            if (keccak256(abi.encodePacked(queryDimensions[i])) == keccak256(abi.encodePacked("Category")) && !allowedDimensions.Category) return false;
            if (keccak256(abi.encodePacked(queryDimensions[i])) == keccak256(abi.encodePacked("Supplier")) && !allowedDimensions.Supplier) return false;
            if (keccak256(abi.encodePacked(queryDimensions[i])) == keccak256(abi.encodePacked("MonthOfSale")) && !allowedDimensions.MonthOfSale) return false;
            if (keccak256(abi.encodePacked(queryDimensions[i])) == keccak256(abi.encodePacked("QuarterOfSale")) && !allowedDimensions.QuarterOfSale) return false;
            if (keccak256(abi.encodePacked(queryDimensions[i])) == keccak256(abi.encodePacked("BimonthOfSale")) && !allowedDimensions.BimonthOfSale) return false;
            if (keccak256(abi.encodePacked(queryDimensions[i])) == keccak256(abi.encodePacked("YearOfSale")) && !allowedDimensions.YearOfSale) return false;
            if (keccak256(abi.encodePacked(queryDimensions[i])) == keccak256(abi.encodePacked("City")) && !allowedDimensions.City) return false;
            if (keccak256(abi.encodePacked(queryDimensions[i])) == keccak256(abi.encodePacked("Province")) && !allowedDimensions.Province) return false;
            if (keccak256(abi.encodePacked(queryDimensions[i])) == keccak256(abi.encodePacked("Region")) && !allowedDimensions.Region) return false;
            if (keccak256(abi.encodePacked(queryDimensions[i])) == keccak256(abi.encodePacked("TypeOfSale")) && !allowedDimensions.TypeOfSale) return false;
        }
        return true;
    }

    function executeQuery(string[] memory queryDimensions) public {
        require(isQueryAllowed(queryDimensions), "Query contains disallowed dimensions");
        
        emit QueryCheck(msg.sender, queryDimensions);
    }
}
