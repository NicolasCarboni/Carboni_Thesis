const fs = require('fs');
const path = require('path');
const DataFactModel = artifacts.require("DataFactModel");
const HashStorage = artifacts.require("HashStorage");

module.exports = async function (deployer) {
  await deployer.deploy(DataFactModel);
  const dataFactModel = await DataFactModel.deployed();

  await deployer.deploy(HashStorage);
  const hashStorage = await HashStorage.deployed();

  // Save contract addresses to a JSON file
  const addresses = {
    DataFactModel: dataFactModel.address,
    HashStorage: hashStorage.address,
  };

  const filePath = path.join(__dirname, '../config/contract_addresses.json');
  fs.writeFileSync(filePath, JSON.stringify(addresses, null, 2));

  console.log("Contract addresses saved to contract_addresses.json");
};